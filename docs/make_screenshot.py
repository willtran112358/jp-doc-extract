# -*- coding: utf-8 -*-
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

draft = json.loads(
    Path("output/jp_electricity_invoice_sakura_draft.json").read_text(encoding="utf-8")
)
keys = list(draft["draft_ghg"].keys())
lines = [
    "CLAP AI OCR POC — run sample",
    "",
    "PS> python src/ocr_pipeline.py samples/jp_electricity_invoice_sakura.pdf",
    "",
    "=== CLAP AI OCR POC ===",
    "file     : samples/jp_electricity_invoice_sakura.pdf",
    f"method   : {draft['extract_method']}",
    f"status   : {draft['status']} (Draft / HITL)",
    f"fields   : {keys}",
    f"evidence : {len(draft['evidence_history'])} snippets",
    "output   : output/jp_electricity_invoice_sakura_draft.json",
    "",
    "draft_ghg (excerpt):",
]
for k, v in draft["draft_ghg"].items():
    lines.append(f"  {k}: {v.get('value')}  (conf={v.get('confidence')})")
lines += ["", "Next: User review -> Confirm -> GHG Core (not in POC)"]

try:
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
    font_b = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 18)
except OSError:
    font = ImageFont.load_default()
    font_b = font

pad, lh = 24, 22
w = 960
h = pad * 2 + lh * (len(lines) + 1)
img = Image.new("RGB", (w, h), "#0d1117")
draw = ImageDraw.Draw(img)
y = pad
for i, line in enumerate(lines):
    if i == 0:
        color = "#58a6ff"
        f = font_b
    elif line.startswith("PS>"):
        color = "#3fb950"
        f = font
    else:
        color = "#c9d1d9"
        f = font
    draw.text((pad, y), line, fill=color, font=f)
    y += lh

out = Path("docs/screenshots/run_sample.png")
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out)
print("saved", out, out.stat().st_size)
