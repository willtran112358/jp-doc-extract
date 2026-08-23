# -*- coding: utf-8 -*-
"""Render terminal-style screenshots for README."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOT = ROOT / "docs" / "screenshots"
SHOT.mkdir(parents=True, exist_ok=True)


def fonts():
    for path, size in (
        ("C:/Windows/Fonts/msgothic.ttc", 15),
        ("C:/Windows/Fonts/meiryo.ttc", 15),
        ("C:/Windows/Fonts/yu_gothic.ttc", 15),
        ("C:/Windows/Fonts/consola.ttf", 15),
    ):
        try:
            return (
                ImageFont.truetype(path, size),
                ImageFont.truetype(path, size + 2),
            )
        except OSError:
            continue
    f = ImageFont.load_default()
    return f, f


def render(path: Path, title: str, lines: list[str], width: int = 980) -> None:
    font, font_b = fonts()
    pad, lh = 22, 22
    # measure with JP-capable font
    h = pad * 2 + lh * (len(lines) + 2)
    img = Image.new("RGB", (width, h), "#0d1117")
    draw = ImageDraw.Draw(img)
    y = pad
    draw.text((pad, y), title, fill="#58a6ff", font=font_b)
    y += lh + 6
    for line in lines:
        if line.startswith("PS>") or line.startswith("$"):
            color = "#3fb950"
        elif line.startswith("===") or line.startswith("---"):
            color = "#79c0ff"
        elif "error" in line.lower() or "warning" in line.lower():
            color = "#d29922"
        else:
            color = "#c9d1d9"
        draw.text((pad, y), line[:100], fill=color, font=font)
        y += lh
    img.save(path)
    print("saved", path)


def main() -> None:
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
            "Successfully installed pymupdf Pillow ...",
            "(venv ready)",
        ],
    )

    keys = list(draft["draft_ghg"].keys())
    render(
        SHOT / "02_run_electricity.png",
        "Step 2 — Run (電力請求書)",
        [
            "PS> python src/ocr_pipeline.py samples/jp_electricity_invoice_sakura.pdf",
            "",
            "=== CLAP AI OCR POC ===",
            "file     : samples/jp_electricity_invoice_sakura.pdf",
            f"method   : {draft['extract_method']}",
            f"status   : {draft['status']} (Draft / 未確定)",
            f"fields   : {keys}",
            f"evidence : {len(draft['evidence_history'])} snippets",
            "output   : output/jp_electricity_invoice_sakura_draft.json",
        ],
    )

    render(
        SHOT / "03_run_gas.png",
        "Step 3 — Run (都市ガス納品伝票)",
        [
            "PS> python src/ocr_pipeline.py samples/jp_gas_delivery_sakura.pdf -o output",
            "",
            "=== CLAP AI OCR POC ===",
            "file     : samples/jp_gas_delivery_sakura.pdf",
            "method   : text_layer",
            "status   : draft (Draft / 未確定)",
            "fields   : [company_name, invoice_date, billing_period, ...]",
            "evidence : 4 snippets",
            "output   : output/jp_gas_delivery_sakura_draft.json",
        ],
    )

    out_lines = ["Step 4 — Output Draft JSON (excerpt)", ""]
    out_lines.append("{")
    out_lines.append(f'  "status": "{draft["status"]}",')
    out_lines.append(f'  "source_file": "{draft["source_file"]}",')
    out_lines.append(f'  "extract_method": "{draft["extract_method"]}",')
    out_lines.append('  "draft_ghg": {')
    for k, v in list(draft["draft_ghg"].items())[:5]:
        out_lines.append(f'    "{k}": {{"value": "{v.get("value")}", "confidence": {v.get("confidence")}}},')
    out_lines.append("    ...")
    out_lines.append("  },")
    out_lines.append(f'  "evidence_history": [ ... {len(draft["evidence_history"])} items ],')
    out_lines.append('  "next_step": "User review/edit → Confirm → GHG Core"')
    out_lines.append("}")
    # title is first line conceptually - render() uses title arg
    render(
        SHOT / "04_draft_json_output.png",
        "Step 4 — Output Draft JSON (excerpt)",
        out_lines[2:],
        width=1000,
    )

    # keep legacy alias
    render(
        SHOT / "run_sample.png",
        "CLAP AI OCR POC — run sample",
        [
            "PS> python src/ocr_pipeline.py samples/jp_electricity_invoice_sakura.pdf",
            "",
            "=== CLAP AI OCR POC ===",
            f"method   : {draft['extract_method']}",
            f"status   : {draft['status']}",
            f"fields   : {keys}",
            f"evidence : {len(draft['evidence_history'])} snippets",
            "output   : output/jp_electricity_invoice_sakura_draft.json",
        ],
    )


if __name__ == "__main__":
    main()
