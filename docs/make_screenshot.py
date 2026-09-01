# -*- coding: utf-8 -*-
"""Render terminal-style screenshots from docs/evidence batch output."""
from __future__ import annotations

import json
from collections import Counter
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
    # Light theme — easier to read in README / docs
    bg = "#ffffff"
    border = "#d0d7de"
    title_color = "#0969da"
    prompt_color = "#116329"
    ok_color = "#116329"
    err_color = "#cf222e"
    accent_color = "#0550ae"
    text_color = "#24292f"

    img = Image.new("RGB", (width, h), bg)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width - 1, h - 1], outline=border, width=1)
    y = pad
    draw.text((pad, y), title, fill=title_color, font=font_b)
    y += lh + 6
    for line in lines:
        if line.startswith("PS>") or line.startswith("$"):
            color = prompt_color
        elif line.startswith("OK"):
            color = ok_color
        elif line.startswith("ERR"):
            color = err_color
        elif line.startswith("===") or line.startswith("Batch"):
            color = accent_color
        else:
            color = text_color
        draw.text((pad, y), line[:105], fill=color, font=font)
        y += lh
    img.save(path)
    print("saved", path)


def main() -> None:
    report = json.loads((EVID / "batch_summary.json").read_text(encoding="utf-8"))
    draft_path = EVID / "sample_electricity_invoice_draft.json"
    if not draft_path.exists():
        draft_path = ROOT / "output" / "sample_electricity_invoice_draft.json"
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    keys = list(draft.get("draft_fields", {}).keys())

    render(
        SHOT / "01_setup.png",
        "Step 1 — Setup",
        [
            "PS> cd jp-doc-extract",
            "PS> python -m venv .venv",
            "PS> .\\.venv\\Scripts\\Activate.ps1",
            "PS> pip install -r requirements.txt",
            "PS> python scripts/generate_samples.py",
        ],
    )

    batch_lines = [
        "PS> python src/pipeline.py samples --batch -o output",
        "",
    ]
    for r in report.get("results", [])[:5]:
        if r.get("ok"):
            batch_lines.append(
                f"OK  {r['file']} -> {r['doc_type']} fields={r['field_count']}"
            )
    batch_lines += [
        "...",
        f"Batch: {report['ok']}/{report['total']} OK -> output/batch_summary.json",
    ]
    render(SHOT / "02_batch.png", "Step 2 — Batch run (bundled samples)", batch_lines)

    render(
        SHOT / "03_single_run.png",
        "Step 3 — Single file",
        [
            "PS> python src/pipeline.py samples/sample_electricity_invoice.pdf",
            "",
            "=== jp-doc-extract ===",
            f"doc_type : {draft.get('doc_type')}",
            f"method   : {draft.get('extract_method')}",
            f"status   : {draft.get('status')}",
            f"fields   : {keys}",
            f"evidence : {len(draft.get('evidence_history', []))} snippets",
        ],
    )

    lines = [
        f'"tool": "{draft.get("tool")}",',
        f'"doc_type": "{draft.get("doc_type")}",',
        f'"extract_method": "{draft.get("extract_method")}",',
        '"draft_fields": {',
    ]
    for k, v in list(draft.get("draft_fields", {}).items())[:6]:
        lines.append(f'  "{k}": {{"value": "{v.get("value")}", "confidence": {v.get("confidence")}}},')
    lines += [
        "  ...",
        "},",
        f'"evidence_history": [ ... {len(draft.get("evidence_history", []))} items ]',
    ]
    render(SHOT / "04_draft_json.png", "Step 4 — Draft JSON excerpt", lines, width=1040)

    types = Counter(r.get("doc_type", "?") for r in report["results"] if r.get("ok"))
    mix = [f"  {k}: {v}" for k, v in types.most_common()]
    render(
        SHOT / "05_batch_summary.png",
        "Step 5 — Batch summary",
        [
            "sample_root: bundled samples/",
            f"total: {report['total']}  |  OK: {report['ok']}",
            "",
            "doc_type counts:",
            *mix,
        ],
    )


if __name__ == "__main__":
    main()
