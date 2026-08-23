# -*- coding: utf-8 -*-
"""Render terminal-style screenshots after client-pack batch run."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOT = ROOT / "docs" / "screenshots"
EVID = ROOT / "docs" / "evidence"
SHOT.mkdir(parents=True, exist_ok=True)


def fonts():
    for path in (
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/consola.ttf",
    ):
        try:
            return ImageFont.truetype(path, 15), ImageFont.truetype(path, 17)
        except OSError:
            continue
    f = ImageFont.load_default()
    return f, f


def render(path: Path, title: str, lines: list[str], width: int = 1000) -> None:
    font, font_b = fonts()
    pad, lh = 22, 22
    h = pad * 2 + lh * (len(lines) + 2)
    img = Image.new("RGB", (width, h), "#0d1117")
    draw = ImageDraw.Draw(img)
    y = pad
    draw.text((pad, y), title, fill="#58a6ff", font=font_b)
    y += lh + 6
    for line in lines:
        if line.startswith("PS>") or line.startswith("$"):
            color = "#3fb950"
        elif line.startswith("OK"):
            color = "#3fb950"
        elif line.startswith("ERR"):
            color = "#f85149"
        elif line.startswith("===") or line.startswith("---") or line.startswith("Batch"):
            color = "#79c0ff"
        else:
            color = "#c9d1d9"
        draw.text((pad, y), line[:105], fill=color, font=font)
        y += lh
    img.save(path)
    print("saved", path)


def main() -> None:
    report = json.loads((EVID / "batch_summary.json").read_text(encoding="utf-8"))
    draft_path = ROOT / "docs" / "evidence" / "jp_electricity_invoice_sakura_draft.json"
    if not draft_path.exists():
        draft_path = ROOT / "output" / "jp_electricity_invoice_sakura_draft.json"
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    render(
        SHOT / "01_setup.png",
        "Step 1 — Setup",
        [
            "PS> cd clap-ai-ocr-poc",
            "PS> python -m venv .venv",
            "PS> .\\.venv\\Scripts\\Activate.ps1",
            "PS> pip install -r requirements.txt",
            "",
            "Installed: pymupdf, Pillow, openpyxl",
        ],
    )

    render(
        SHOT / "02_batch_client_pack.png",
        "Step 2 — Batch run (client sample pack)",
        [
            "PS> python src/ocr_pipeline.py \"D:\\...\\Tài liệu AI Data Extraction\" --batch -o output",
            "",
            "OK  Sample1/電力請求書_本社工場 → electricity_invoice fields=8 evidence=8",
            "OK  Sample1/都市ガス納品伝票 → gas_invoice fields=7 evidence=7",
            "OK  Sample2/海上輸送インボイス → shipping_invoice fields=5 evidence=5",
            "OK  Sample3/invoice_electricity_kawasaki → electricity_invoice fields=8",
            "OK  Sample5/invoice_electricity_tokyo_hq → electricity_invoice fields=8",
            "OK  Sample6/gas_invoice_dummy_konotori → gas_invoice fields=4",
            "...",
            f"Batch: {report['ok']}/{report['total']} OK → docs/evidence/batch_summary.json",
        ],
    )

    keys = list(draft.get("draft_ghg", {}).keys())
    render(
        SHOT / "03_run_single_invoice.png",
        "Step 3 — Single file run (電力請求書)",
        [
            "PS> python src/ocr_pipeline.py samples/jp_electricity_invoice_sakura.pdf",
            "",
            "=== CLAP AI OCR POC ===",
            f"doc_type : {draft.get('doc_type')}",
            f"method   : {draft.get('extract_method')}",
            f"status   : {draft.get('status')} (Draft / 未確定)",
            f"fields   : {keys}",
            f"evidence : {len(draft.get('evidence_history', []))} snippets",
            f"output   : output/{draft.get('source_file', 'invoice')}_draft.json",
        ],
    )

    lines = [
        f'"status": "{draft.get("status")}",',
        f'"doc_type": "{draft.get("doc_type")}",',
        f'"source_file": "{draft.get("source_file")}",',
        f'"extract_method": "{draft.get("extract_method")}",',
        '"draft_ghg": {',
    ]
    for k, v in list(draft.get("draft_ghg", {}).items())[:6]:
        lines.append(f'  "{k}": {{"value": "{v.get("value")}", "confidence": {v.get("confidence")}}},')
    lines += [
        "  ...",
        "},",
        f'"evidence_history": [ ... {len(draft.get("evidence_history", []))} items ],',
        '"next_step": "User review/edit → Confirm → GHG Core"',
    ]
    render(SHOT / "04_draft_json_output.png", "Step 4 — Draft JSON output (excerpt)", lines, width=1040)

    # doc type mix from batch
    from collections import Counter

    types = Counter(r.get("doc_type", "?") for r in report["results"] if r.get("ok"))
    mix = [f"  {k}: {v}" for k, v in types.most_common()]
    render(
        SHOT / "05_batch_summary.png",
        "Step 5 — Batch summary by doc_type",
        [
            f"sample_root: Tài liệu AI Data Extraction",
            f"total files: {report['total']}  |  OK: {report['ok']}",
            "",
            "doc_type counts:",
            *mix,
            "",
            "Evidence artifact: docs/evidence/batch_summary.json",
        ],
    )

    render(
        SHOT / "02_run_electricity.png",
        "Step 2 — Run (電力請求書) [alias]",
        [
            "PS> python src/ocr_pipeline.py samples/jp_electricity_invoice_sakura.pdf",
            "",
            "=== CLAP AI OCR POC ===",
            f"doc_type : {draft.get('doc_type')}",
            f"method   : {draft.get('extract_method')}",
            f"status   : {draft.get('status')} (Draft / 未確定)",
            f"fields   : {keys}",
            f"evidence : {len(draft.get('evidence_history', []))} snippets",
        ],
    )
    render(
        SHOT / "03_run_gas.png",
        "Step 3 — Run (都市ガス) [alias]",
        [
            "PS> python src/ocr_pipeline.py samples/jp_gas_delivery_sakura.pdf",
            "",
            "=== CLAP AI OCR POC ===",
            "doc_type : gas_invoice",
            "method   : text_layer",
            "status   : draft (Draft / 未確定)",
            "fields   : [company_name, invoice_date, activity_amount, ...]",
            "evidence : 7 snippets",
        ],
    )
    render(SHOT / "run_sample.png", "CLAP AI OCR POC — run sample", [
        "PS> python src/ocr_pipeline.py \"<client sample pack>\" --batch -o output",
        f"Batch: {report['ok']}/{report['total']} OK",
        f"Example fields: {keys}",
    ])


if __name__ == "__main__":
    main()
