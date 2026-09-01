# -*- coding: utf-8 -*-
"""Generate synthetic public-domain sample files (no real company data)."""
from __future__ import annotations

import csv
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"

JP_FONTS = [
    Path("C:/Windows/Fonts/msgothic.ttc"),
    Path("C:/Windows/Fonts/meiryo.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
]


def _jp_font() -> tuple[str, str | None]:
    for path in JP_FONTS:
        if path.exists():
            return "jpfont", str(path)
    return "helv", None


def _write_pdf(name: str, lines: list[str]) -> None:
    fontname, fontfile = _jp_font()
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    if fontfile:
        page.insert_font(fontname=fontname, fontfile=fontfile)
    y = 50
    for line in lines:
        kw = {"fontsize": 11, "fontname": fontname}
        page.insert_text((50, y), line, **kw)
        y += 16
        if y > 800:
            page = doc.new_page(width=595, height=842)
            if fontfile:
                page.insert_font(fontname=fontname, fontfile=fontfile)
            y = 50
    path = SAMPLES / name
    doc.save(path)
    doc.close()
    print("wrote", path)


def main() -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)

    _write_pdf(
        "sample_electricity_invoice.pdf",
        [
            "電気ご使用量のお知らせ(御請求書)",
            "デモ電力株式会社 産業用電力部",
            "発行日:2024年5月10日",
            "請求書番号:INV-2024-04-00001",
            "お客様名:サンプル製造株式会社 本社工場",
            "ご使用期間:2024年4月1日~2024年4月30日",
            "使用電力量",
            "125,000 kWh",
            "ご請求額合計(税込)",
            "2,750,000円",
            "※本書類は技術検証用の合成サンプルです。",
        ],
    )

    _write_pdf(
        "sample_gas_delivery.pdf",
        [
            "都市ガス供給計量票(伝票)",
            "デモガス株式会社",
            "発行日:2024年6月5日",
            "伝票番号:GAS-2024-05-00002",
            "供給先名:サンプル製造株式会社 本社工場",
            "計量期間:2024年5月1日~2024年5月31日",
            "都市ガス使用量",
            "4,850 m3",
            "※本書類は技術検証用の合成サンプルです。",
        ],
    )

    csv_path = SAMPLES / "sample_activity_energy.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["会社名", "拠点", "対象年度", "エネルギー種別", "使用量", "単位"])
        w.writerow(["サンプル製造株式会社", "本社工場", "2024年度", "電力", "125000", "kWh"])
        w.writerow(["サンプル製造株式会社", "本社工場", "2024年度", "都市ガス", "4850", "m3"])
    print("wrote", csv_path)


if __name__ == "__main__":
    main()
