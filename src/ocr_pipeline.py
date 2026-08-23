"""
CLAP AI Extraction POC — JP document OCR / text extract → Draft JSON
Track: AI Data Extraction (not EDINET/MCP)
Flow: Upload PDF → extract text → map fields → Draft (HITL later)
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pymupdf as fitz


# GHG / invoice-oriented fields (canonical draft sketch for CLAP)
FIELD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("company_name", re.compile(r"(株式会社[\w一-龥ぁ-んァ-ヶー]+|[\w一-龥ぁ-んァ-ヶー]+株式会社)")),
    ("invoice_date", re.compile(r"(20\d{2})[年/\-.](\d{1,2})[月/\-.](\d{1,2})")),
    ("billing_period", re.compile(r"(20\d{2}年\d{1,2}月(?:分|度)?)")),
    ("activity_amount", re.compile(r"(?:使用量|電力量|ガス使用量|数量)[^\d]{0,12}([\d,]+(?:\.\d+)?)\s*(kWh|m3|m³|kg|t)?", re.I)),
    ("amount_yen", re.compile(r"(?:ご請求金額|請求金額|税込|合計|金額)[^\d]{0,12}[¥￥]?\s*([\d,]+)\s*円?")),
    ("emission_hint", re.compile(r"(?:排出量|t-?CO2e?)[^\d]{0,12}([\d,]+(?:\.\d+)?)", re.I)),
]


def extract_text(pdf_path: Path) -> tuple[str, str]:
    """Return (full_text, method). method=text_layer|ocr_needed."""
    doc = fitz.open(pdf_path)
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text("text"))
    doc.close()
    text = "\n".join(parts).strip()
    if len(text) >= 20:
        return text, "text_layer"
    return text, "ocr_needed"


def map_fields(text: str) -> dict:
    fields: dict = {}
    evidence: list[dict] = []
    for name, pat in FIELD_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        if name == "invoice_date" and m.lastindex and m.lastindex >= 3:
            value = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            snippet = m.group(0)
        elif name == "activity_amount":
            value = m.group(1).replace(",", "")
            unit = m.group(2) or ""
            fields["activity_unit"] = {
                "value": unit,
                "confidence": 0.7 if unit else 0.4,
            }
            snippet = m.group(0)
        else:
            value = m.group(1).replace(",", "") if m.lastindex else m.group(0)
            snippet = m.group(0)
        conf = 0.85 if name in ("company_name", "invoice_date") else 0.75
        fields[name] = {"value": value, "confidence": conf}
        evidence.append(
            {
                "field": name,
                "snippet": snippet[:120],
                "page": 1,
                "source": "regex_on_extracted_text",
            }
        )
    return {"fields": fields, "evidence": evidence}


def build_draft(pdf_path: Path, text: str, method: str, mapped: dict) -> dict:
    return {
        "poc": "clap-ai-ocr-poc",
        "track": "AI_Data_Extraction",
        "status": "draft",  # 未確定 — HITL required before Core
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_file": pdf_path.name,
        "extract_method": method,
        "warning": (
            None
            if method == "text_layer"
            else "Scanned/low-text PDF: install OCR engine (see README) for Phase-2 scan support"
        ),
        "soft_warnings": [
            f"{k} confidence < 0.8"
            for k, v in mapped["fields"].items()
            if isinstance(v, dict) and v.get("confidence", 1) < 0.8
        ],
        "draft_ghg": mapped["fields"],
        "evidence_history": mapped["evidence"],
        "text_preview": text[:800],
        "next_step": "User review/edit → Confirm → SF Validation Rule → GHG Core (not in this POC)",
    }


def run(pdf_path: Path, out_dir: Path) -> Path:
    text, method = extract_text(pdf_path)
    mapped = map_fields(text)
    draft = build_draft(pdf_path, text, method, mapped)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pdf_path.stem}_draft.json"
    out_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="CLAP JP document → Draft JSON POC")
    parser.add_argument(
        "pdf",
        nargs="?",
        default="samples/jp_electricity_invoice_sakura.pdf",
        help="Path to JP sample PDF",
    )
    parser.add_argument("-o", "--out", default="output", help="Output directory")
    args = parser.parse_args()
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"File not found: {pdf_path}")
    out_path = run(pdf_path, Path(args.out))
    draft = json.loads(out_path.read_text(encoding="utf-8"))
    print("=== CLAP AI OCR POC ===")
    print(f"file     : {pdf_path}")
    print(f"method   : {draft['extract_method']}")
    print(f"status   : {draft['status']} (Draft / 未確定)")
    print(f"fields   : {list(draft['draft_ghg'].keys())}")
    print(f"evidence : {len(draft['evidence_history'])} snippets")
    print(f"output   : {out_path}")
    if draft.get("warning"):
        print(f"warning  : {draft['warning']}")


if __name__ == "__main__":
    main()
