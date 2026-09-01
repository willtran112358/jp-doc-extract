# -*- coding: utf-8 -*-
"""Create scan-like PDF (image-only, no text layer) for OCR benchmark."""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from extractors import pdf_to_images  # noqa: E402


def rasterize_pdf(src: Path, dst: Path, dpi: int = 200) -> Path:
    images = pdf_to_images(src, max_pages=20, dpi=dpi)
    doc = fitz.open()
    for img_bytes in images:
        page = doc.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=img_bytes)
    dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dst, garbage=4, deflate=True)
    doc.close()
    print(f"scan PDF: {dst} ({dst.stat().st_size // 1024} KB, {len(images)} page(s))")
    return dst


def main() -> None:
    src = ROOT / "samples" / "sample_electricity_invoice.pdf"
    gas = ROOT / "samples" / "sample_gas_delivery.pdf"
    out_dir = ROOT / "samples" / "scan"
    if not src.exists():
        raise SystemExit(f"Run scripts/generate_samples.py first — missing {src}")
    rasterize_pdf(src, out_dir / "sample_electricity_invoice_scan.pdf")
    if gas.exists():
        rasterize_pdf(gas, out_dir / "sample_gas_delivery_scan.pdf")


if __name__ == "__main__":
    main()
