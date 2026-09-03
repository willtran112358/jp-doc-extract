"""Rule-based 仕訳 (journal) draft after OCR/extract. No LLM. Deterministic + evidence."""

from __future__ import annotations

import json
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parents[1] / "rules" / "journal_rules.json"


def _load_rules() -> dict:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def _val(fields: dict, key: str) -> str:
    item = fields.get(key) or {}
    return str(item.get("value") or "").strip()


def _first_match(blob: str, items: list[dict], key: str = "match") -> dict | None:
    low = blob.lower()
    for row in items:
        token = row.get(key) or ""
        if token and token.lower() in low:
            return row
    return None


def _cat_match(blob: str, cats: list[dict]) -> dict | None:
    low = blob.lower()
    for row in cats:
        if any(str(t).lower() in low for t in row.get("match_any") or []):
            return row
    return None


def _split_yen(total: int, splits: list[dict]) -> list[tuple[dict, int]]:
    out: list[tuple[dict, int]] = []
    used = 0
    for i, part in enumerate(splits):
        amt = total - used if i == len(splits) - 1 else int(total * int(part["pct"]) / 100)
        used += amt
        out.append((part, amt))
    return out


def apply_journal(fields: dict, *, doc_type: str, text: str, source_file: str) -> dict:
    """Map extract fields → balanced AP journal lines. Skip if no amount."""
    rules = _load_rules()
    evidence: list[dict] = []
    gross_s = _val(fields, "amount_yen")
    if not gross_s:
        return {
            "status": "skipped",
            "reason": "no amount_yen",
            "balanced": None,
            "lines": [],
            "evidence": evidence,
        }

    gross = int(float(gross_s.replace(",", "")))
    tax_s = _val(fields, "tax_yen")
    rate = float(rules["tax_included_rate"])
    if tax_s:
        tax = int(float(tax_s.replace(",", "")))
        net = gross - tax
    else:
        net = round(gross / (1 + rate))
        tax = gross - net

    blob = " ".join(
        [
            doc_type,
            source_file,
            _val(fields, "company_name"),
            _val(fields, "customer_name"),
            _val(fields, "item_category"),
            _val(fields, "payee"),
            text[:800],
        ]
    )

    vendor = _first_match(blob, rules["vendors"]) or {}
    payee = _val(fields, "payee") or _val(fields, "company_name") or "UNKNOWN"
    payee_code = vendor.get("payee_code") or "V-UNMAPPED"
    evidence.append(
        {
            "field": "payee",
            "snippet": f"{payee} → {payee_code}",
            "page": 1,
            "source": "journal_rule",
        }
    )

    cat = _cat_match(blob, rules["categories"]) or {
        "expense_code": "5900",
        "expense_name": "雑費",
        "item": _val(fields, "item_category") or "未分類",
    }
    evidence.append(
        {
            "field": "item_category",
            "snippet": f"{cat['item']} → {cat['expense_code']} {cat['expense_name']}",
            "page": 1,
            "source": "journal_rule",
        }
    )

    alloc = _cat_match(blob, rules["allocations"])
    splits = (alloc or {}).get("splits") or rules["default_split"]
    evidence.append(
        {
            "field": "allocation",
            "snippet": " / ".join(f"{s['name']} {s['pct']}%" for s in splits),
            "page": 1,
            "source": "journal_rule",
        }
    )

    ap = rules["ap_account"]
    tx = rules["tax_account"]
    lines: list[dict] = []
    for part, amt in _split_yen(net, splits):
        if amt <= 0:
            continue
        lines.append(
            {
                "side": "debit",
                "account_code": cat["expense_code"],
                "account_name": cat["expense_name"],
                "dept": part["dept"],
                "dept_name": part["name"],
                "amount": amt,
                "tax_code": "JCT10",
                "item": cat["item"],
            }
        )
    if tax:
        lines.append(
            {
                "side": "debit",
                "account_code": tx["code"],
                "account_name": tx["name"],
                "dept": None,
                "dept_name": None,
                "amount": tax,
                "tax_code": "JCT10",
                "item": "消費税",
            }
        )
    lines.append(
        {
            "side": "credit",
            "account_code": ap["code"],
            "account_name": ap["name"],
            "dept": None,
            "dept_name": None,
            "amount": gross,
            "tax_code": "JCT10",
            "item": payee,
            "payee": payee,
            "payee_code": payee_code,
        }
    )

    debit = sum(x["amount"] for x in lines if x["side"] == "debit")
    credit = sum(x["amount"] for x in lines if x["side"] == "credit")
    return {
        "status": "draft",
        "balanced": debit == credit,
        "gross": gross,
        "net": net,
        "tax": tax,
        "payee": payee,
        "payee_code": payee_code,
        "item": cat["item"],
        "lines": lines,
        "evidence": evidence,
        "next_step": "HITL confirm extract + journal; do not auto-post",
    }
