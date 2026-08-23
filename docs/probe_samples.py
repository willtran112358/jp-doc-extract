# -*- coding: utf-8 -*-
from pathlib import Path
import pymupdf as fitz

root = Path(r"D:\bchin\Downloads\VMO\WOV2-AI") / "Tài liệu AI Data Extraction"
pdfs = sorted(root.rglob("*.pdf"))
print("PDF count", len(pdfs))
for p in pdfs:
    doc = fitz.open(p)
    text = "\n".join(page.get_text("text") for page in doc).strip()
    doc.close()
    preview = text[:100].replace("\n", " ")
    print(f"--- {p.parent.name} | {p.name} | chars={len(text)}")
    print("   ", preview)
