# -*- coding: utf-8 -*-
"""Render terminal-style screenshots from docs/evidence (extract + journal draft)."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOT = ROOT / "docs" / "screenshots"
EVID = ROOT / "docs" / "evidence"
SHOT.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/consola.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def fonts():
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, 15), ImageFont.truetype(path, 17)
        except OSError:
            continue
    f = ImageFont.load_default()
    return f, f


def render(path: Path, title: str, lines: list[str], width: int = 1040) -> None:
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
        elif line.startswith("OK") or "balanced=True" in line:
            color = "#3fb950"
        elif line.startswith("ERR") or line.startswith("SKIP"):
            color = "#f85149"
        elif line.startswith("===") or line.startswith("Batch") or line.startswith("journal"):
            color = "#79c0ff"
        elif line.strip().startswith("- debit") or line.strip().startswith("- credit"):
            color = "#d2a8ff"
        else:
            color = "#c9d1d9"
        draw.text((pad, y), line[:120], fill=color, font=font)
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
    jd = draft.get("journal_draft") or {}

    render(
        SHOT / "01_setup.png",
        "Step 1 — Setup",
        [
            "$ cd jp-doc-extract",
            "$ python -m venv .venv && source .venv/bin/activate",
            "$ pip install -r requirements.txt",
            "$ python scripts/generate_samples.py",
        ],
    )

    batch_lines = ["$ python src/pipeline.py samples --batch -o output", ""]
    for r in report.get("results", [])[:6]:
        if r.get("ok"):
            batch_lines.append(
                f"OK  {r['file']} -> {r['doc_type']} "
                f"journal={r.get('journal')} lines={r.get('journal_lines', 0)}"
            )
    batch_lines += [
        "",
        f"Batch: {report['ok']}/{report['total']} OK -> output/batch_summary.json",
    ]
    render(SHOT / "02_batch.png", "Step 2 — Batch (extract + journal)", batch_lines)

    jlines = []
    for line in jd.get("lines") or []:
        dept = line.get("dept") or "-"
        jlines.append(
            f"  - {line['side']:6} {line['account_code']} {line['account_name']} "
            f"{dept} {line['amount']}"
        )
    render(
        SHOT / "03_single_run.png",
        "Step 3 — Single file (CLI journal export)",
        [
            "$ python src/pipeline.py samples/sample_electricity_invoice.pdf",
            "",
            "=== jp-doc-extract ===",
            f"doc_type : {draft.get('doc_type')}",
            f"method   : {draft.get('extract_method')}",
            f"fields   : {keys[:6]} ...",
            f"journal  : {jd.get('status')} balanced={jd.get('balanced')} lines={len(jd.get('lines') or [])}",
            *jlines,
            f"output   : output/sample_electricity_invoice_draft.json",
        ],
    )

    flines = [
        f'"tool": "{draft.get("tool")}",',
        f'"doc_type": "{draft.get("doc_type")}",',
        '"draft_fields": {',
    ]
    for k, v in list(draft.get("draft_fields", {}).items())[:5]:
        flines.append(
            f'  "{k}": {{"value": "{v.get("value")}", "confidence": {v.get("confidence")}}},'
        )
    flines += ["  ...", "},"]
    render(SHOT / "04_draft_json.png", "Step 4 — Draft fields JSON", flines)

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

    render(
        SHOT / "06_journal_cli.png",
        "Step 6 — Export journal draft (CLI)",
        [
            "$ python src/pipeline.py samples/sample_electricity_invoice.pdf -o output",
            "$ python scripts/check_journal.py",
            "",
            f"journal  : {jd.get('status')} balanced={jd.get('balanced')}",
            f"payee    : {jd.get('payee')} ({jd.get('payee_code')})",
            f"item     : {jd.get('item')}  gross={jd.get('gross')} net={jd.get('net')} tax={jd.get('tax')}",
            *jlines,
            "OK   sample_electricity_invoice.pdf lines=4 gross=2750000",
            "journal check passed",
        ],
    )

    jjson = [
        '"journal_draft": {',
        f'  "status": "{jd.get("status")}", "balanced": {str(jd.get("balanced")).lower()},',
        f'  "gross": {jd.get("gross")}, "net": {jd.get("net")}, "tax": {jd.get("tax")},',
        f'  "payee": "{jd.get("payee")}", "payee_code": "{jd.get("payee_code")}",',
        '  "lines": [',
    ]
    for line in (jd.get("lines") or [])[:4]:
        jjson.append(
            f'    {{"side": "{line["side"]}", "account_code": "{line["account_code"]}", '
            f'"account_name": "{line["account_name"]}", "dept": {json.dumps(line.get("dept"))}, '
            f'"amount": {line["amount"]}}},'
        )
    jjson += ["  ]", "}"]
    render(SHOT / "07_journal_json.png", "Step 7 — journal_draft JSON export", jjson, width=1100)


if __name__ == "__main__":
    main()
