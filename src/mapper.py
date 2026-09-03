"""JP field mapping: regex on text + structured CSV/XLSX column detection."""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

NUM = r"([\d,]+(?:\.\d+)?)"
SEP = r"[\s　:：]*"
GAP = r"[\s　\n]{0,40}"

FIELD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "payee",
        re.compile(r"(?:支払先|請求元|発行元)" + SEP + r"([^\n]{3,80})"),
    ),
    (
        "company_name",
        re.compile(
            r"("
            r"(?:株式会社|有限会社|合同会社)[一-龥ぁ-んァ-ヶーA-Za-z0-9・･]{1,40}"
            r"|"
            r"[一-龥ぁ-んァ-ヶーA-Za-z0-9・･]{1,40}(?:株式会社|有限会社|合同会社)"
            r"|"
            r"[A-Za-z][A-Za-z0-9 .,&\-]{2,50}(?:Co\.,?\s*Ltd\.|Corporation|Inc\.)"
            r")"
        ),
    ),
    (
        "item_category",
        re.compile(r"(?:品目|費目|摘要)" + SEP + r"([^\n]{2,40})"),
    ),
    (
        "tax_yen",
        re.compile(
            r"(?:消費税(?:額)?|内消費税)(?:[(（][^)）\n]{0,12}[)）])?"
            + SEP
            + r"[¥￥]?\s*"
            + NUM
            + r"\s*円?"
        ),
    ),
    (
        "customer_name",
        re.compile(r"(?:お客様名|供給先名|納品先|検証対象|お客様)" + SEP + r"([^\n]{3,80})"),
    ),
    (
        "invoice_no",
        re.compile(
            r"(?:請求書番号|伝票番号|納品書番号|計量票番号|文書番号|Invoice\s*No\.?)"
            + SEP
            + r"([A-Za-z0-9\-_/]+)",
            re.I,
        ),
    ),
    (
        "invoice_date",
        re.compile(r"(?:発行日|作成日|お支払期限)" + SEP + r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?"),
    ),
    (
        "invoice_date_iso",
        re.compile(r"(?:発行日|Date)" + SEP + r"(20\d{2})-(\d{1,2})-(\d{1,2})", re.I),
    ),
    (
        "billing_period",
        re.compile(
            r"(?:ご使用期間|対象期間|対象|請求|計量期間)"
            + SEP
            + r"("
            r"20\d{2}年\d{1,2}月(?:分|度)?"
            r"|"
            r"20\d{2}年\d{1,2}月\d{1,2}日\s*[〜～\-~]\s*20\d{2}年\d{1,2}月\d{1,2}日"
            r"|"
            r"20\d{2}年\d{1,2}月\s*[〜～\-~]\s*20\d{2}年\d{1,2}月"
            r")"
        ),
    ),
    ("billing_period_loose", re.compile(r"(20\d{2}年\d{1,2}月(?:分|度)?)")),
    (
        "activity_amount",
        re.compile(
            r"(?:使用電力量|使用量|電力量|ガス使用量|数量|納入量|重量|Volume|Quantity)"
            + GAP
            + NUM
            + r"\s*(kWh|m3|m³|kg|t|トン|L|㎥)?",
            re.I,
        ),
    ),
    ("activity_kwh", re.compile(NUM + r"\s*kWh", re.I)),
    ("activity_m3", re.compile(NUM + r"\s*(?:m3|m³|㎥)", re.I)),
    (
        "amount_yen",
        re.compile(
            r"(?:ご請求額合計|ご請求金額|請求金額|税込合計|合計金額|請求金額サマリー|当月お買上額)"
            r"(?:[(（][^)）\n]{0,20}[)）])?"
            + GAP
            + r"[¥￥]?\s*"
            + NUM
            + r"\s*円?",
            re.I,
        ),
    ),
    (
        "emission_tco2e",
        re.compile(
            r"(?:Scope\s*[123]|総排出量|排出量|温室効果ガス)"
            + GAP
            + NUM
            + r"\s*(?:t-?CO2e?|トン)?",
            re.I,
        ),
    ),
    ("fiscal_year", re.compile(r"(FY\s*20\d{2}|FYE?\s*3/20\d{2}|20\d{2}年度|令和\d{1,2}年度)", re.I)),
]

DOC_TYPE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("vendor_invoice", re.compile(r"支払先|事務用品|消耗品")),
    ("electricity_invoice", re.compile(r"電気|電力|kWh|ご使用量のお知らせ|御請求書")),
    ("gas_invoice", re.compile(r"ガス|都市ガス|m³|m3|供給計量票")),
    ("shipping_invoice", re.compile(r"SHIPPING|海上輸送|Invoice", re.I)),
    ("coal_ticket", re.compile(r"石炭|煤炭|COAL", re.I)),
    ("milk_delivery", re.compile(r"生乳|納品書")),
    ("company_profile", re.compile(r"企業概要")),
    ("sustainability_report", re.compile(r"サステナビリティレポート")),
    ("verification_evidence", re.compile(r"検証|エビデンス|監査|指摘")),
]

CSV_COLUMN_MAP: dict[str, list[str]] = {
    "company_name": ["会社名", "企業名", "company", "名称", "法人名"],
    "site_name": ["拠点", "工場", "事業所", "site", "拠点名"],
    "fiscal_year": ["年度", "会計年度", "fiscal", "fy", "対象年度"],
    "activity_amount": ["使用量", "電力量", "活動量", "数量", "kwh", "kWh", "エネルギー"],
    "activity_unit": ["単位", "unit"],
    "emission_tco2e": ["排出量", "co2", "tco2", "温室効果ガス", "ghg"],
    "fuel_type": ["燃料", "エネルギー種別", "種別"],
}


def normalize_jp_text(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = t.replace("\u00a0", " ").replace("〜", "～")
    t = t.replace("\u2010", "-").replace("\u2011", "-").replace("\u2212", "-")
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = re.sub(r"[^\S\n]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def normalize_number(value: str) -> str:
    v = unicodedata.normalize("NFKC", str(value))
    return v.replace(",", "").replace("，", "").strip()


def classify_doc(text: str, name: str) -> str:
    n = name.lower()
    if any(k in name or k in n for k in ["文具", "vendor", "支払"]):
        return "vendor_invoice"
    if any(k in name or k in n for k in ["電力", "electricity"]):
        return "electricity_invoice"
    if any(k in name or k in n for k in ["ガス", "gas"]):
        return "gas_invoice"
    if "coal" in n or "石炭" in name:
        return "coal_ticket"
    if "shipping" in n or "海上" in name:
        return "shipping_invoice"
    if any(k in name or k in n for k in ["生乳", "milk"]):
        return "milk_delivery"
    if any(k in name or k in n for k in ["profile", "企業概要"]):
        return "company_profile"
    if any(k in name or k in n for k in ["sustainability", "サステナ"]):
        return "sustainability_report"
    if any(k in name or k in n for k in ["evidence", "検証", "監査", "survey", "エビデンス"]):
        return "verification_evidence"
    if any(k in name or k in n for k in ["activity", "活動量", "ghg", "排出", "emission", "fuel", "energy"]):
        return "activity_table"
    blob = f"{name}\n{text[:1500]}"
    for label, pat in DOC_TYPE_RULES:
        if pat.search(blob):
            return label
    return "other"


def _set_field(fields: dict, evidence: list, name: str, value: str, snippet: str, conf: float, source: str) -> None:
    if name in fields:
        return
    fields[name] = {"value": value, "confidence": conf}
    evidence.append({"field": name, "snippet": snippet[:140], "page": 1, "source": source})


def map_fields_regex(text: str) -> dict:
    text = normalize_jp_text(text)
    fields: dict = {}
    evidence: list = []

    for name, pat in FIELD_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        if name in {"invoice_date", "invoice_date_iso"} and m.lastindex and m.lastindex >= 3:
            value = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            _set_field(fields, evidence, "invoice_date", value, m.group(0), 0.9, "regex_jp")
        elif name == "activity_amount":
            value = normalize_number(m.group(1))
            unit = (m.group(2) or "").replace("トン", "t").replace("㎥", "m3")
            _set_field(fields, evidence, "activity_amount", value, m.group(0), 0.84, "regex_jp")
            if unit:
                _set_field(fields, evidence, "activity_unit", unit, m.group(0), 0.82, "regex_jp")
        elif name == "activity_kwh":
            _set_field(fields, evidence, "activity_amount", normalize_number(m.group(1)), m.group(0), 0.86, "regex_jp")
            _set_field(fields, evidence, "activity_unit", "kWh", m.group(0), 0.88, "regex_jp")
        elif name == "activity_m3":
            _set_field(fields, evidence, "activity_amount", normalize_number(m.group(1)), m.group(0), 0.86, "regex_jp")
            _set_field(fields, evidence, "activity_unit", "m3", m.group(0), 0.88, "regex_jp")
        elif name == "emission_tco2e":
            _set_field(fields, evidence, "emission_tco2e", normalize_number(m.group(1)), m.group(0), 0.72, "regex_jp")
        elif name in {"billing_period", "billing_period_loose"}:
            value = next((g for g in m.groups() if g), m.group(0))
            _set_field(fields, evidence, "billing_period", value.strip(), m.group(0), 0.84, "regex_jp")
        elif name == "amount_yen":
            _set_field(fields, evidence, "amount_yen", normalize_number(m.group(1)), m.group(0), 0.86, "regex_jp")
        elif name == "tax_yen":
            _set_field(fields, evidence, "tax_yen", normalize_number(m.group(1)), m.group(0), 0.84, "regex_jp")
        elif name == "payee":
            value = re.split(r"\s{2,}|　", m.group(1).strip())[0].strip()
            _set_field(fields, evidence, "payee", value, m.group(0), 0.9, "regex_jp")
        elif name == "item_category":
            _set_field(fields, evidence, "item_category", m.group(1).strip(), m.group(0), 0.86, "regex_jp")
        elif name == "customer_name":
            value = re.split(r"\s{2,}|　", m.group(1).strip())[0].strip()
            _set_field(fields, evidence, "customer_name", value, m.group(0), 0.88, "regex_jp")
        else:
            value = m.group(1) if m.lastindex else m.group(0)
            if name in {"activity_amount", "amount_yen", "emission_tco2e"}:
                value = normalize_number(value)
            conf = 0.9 if name in {"company_name", "invoice_no"} else 0.8
            _set_field(fields, evidence, name, value.strip(), m.group(0), conf, "regex_jp")

    return {"fields": fields, "evidence": evidence}


def _decode_csv_bytes(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp932", "shift_jis", "utf-8"):
        try:
            return normalize_jp_text(raw.decode(enc))
        except UnicodeDecodeError:
            continue
    return normalize_jp_text(raw.decode("utf-8", errors="replace"))


def _match_column(header: str, field: str) -> bool:
    h = header.lower().strip()
    return any(hint.lower() in h or h in hint.lower() for hint in CSV_COLUMN_MAP[field])


def _read_csv_dicts(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    text = _decode_csv_bytes(path.read_bytes())
    reader = csv.DictReader(text.splitlines())
    if not reader.fieldnames:
        return [], []
    headers = [normalize_jp_text(h) for h in reader.fieldnames if h]
    rows: list[dict[str, str]] = []
    for i, row in enumerate(reader):
        if i >= 200:
            break
        clean = {normalize_jp_text(k): normalize_jp_text(str(v)) for k, v in row.items() if k and v}
        if any(clean.values()):
            rows.append(clean)
    return headers, rows


def map_fields_csv(path: Path) -> dict:
    headers, rows = _read_csv_dicts(path)
    fields: dict = {}
    evidence: list = []
    if not headers:
        return {"fields": fields, "evidence": evidence}

    col_for: dict[str, str] = {}
    for field in CSV_COLUMN_MAP:
        for h in headers:
            if _match_column(h, field):
                col_for[field] = h
                break

    def first_val(field: str) -> str | None:
        col = col_for.get(field)
        if not col:
            return None
        for row in rows:
            v = row.get(col, "").strip()
            if v:
                return v
        return None

    company = first_val("company_name")
    if company:
        _set_field(fields, evidence, "company_name", company, f"{col_for.get('company_name')}={company}", 0.88, "csv_column")

    fy = first_val("fiscal_year")
    if not fy:
        m = re.search(r"(20\d{2})", path.name)
        fy = m.group(1) + "年度" if m else None
    if fy:
        _set_field(fields, evidence, "fiscal_year", fy, f"fiscal_year={fy}", 0.85, "csv_column")

    amount_col = col_for.get("activity_amount")
    if amount_col:
        total = 0.0
        count = 0
        unit = first_val("activity_unit") or ""
        for row in rows:
            raw = row.get(amount_col, "").replace(",", "")
            if re.match(r"^-?\d+(\.\d+)?$", raw):
                total += float(raw)
                count += 1
        if count:
            val = str(int(total)) if total == int(total) else str(total)
            _set_field(fields, evidence, "activity_amount", val, f"sum({amount_col}) over {count} rows", 0.82, "csv_aggregate")
            if not unit and "kwh" in amount_col.lower():
                unit = "kWh"
            if unit:
                _set_field(fields, evidence, "activity_unit", unit, amount_col, 0.8, "csv_column")

    emission_col = col_for.get("emission_tco2e")
    if emission_col:
        total = 0.0
        count = 0
        for row in rows:
            raw = row.get(emission_col, "").replace(",", "")
            if re.match(r"^-?\d+(\.\d+)?$", raw):
                total += float(raw)
                count += 1
        if count:
            val = str(total)
            _set_field(fields, evidence, "emission_tco2e", val, f"sum({emission_col})", 0.78, "csv_aggregate")

    site = first_val("site_name")
    if site:
        _set_field(fields, evidence, "site_name", site, site, 0.8, "csv_column")

    return {"fields": fields, "evidence": evidence}


def map_fields(text: str, path: Path | None = None, method: str = "text_layer") -> dict:
    if method == "csv_parse" and path is not None:
        structured = map_fields_csv(path)
        if structured["fields"]:
            return structured
    return map_fields_regex(text)
