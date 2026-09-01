"""PaddleOCR JP wrapper with per-line confidence (PP-OCR + angle cls)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from PIL import Image

_OCR_ENGINE: Any | None = None

# Disable OneDNN before any paddle import (Windows + Paddle 3.x)
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("PADDLE_DISABLE_MKLDNN", "1")


@dataclass
class OcrLine:
    text: str
    confidence: float
    page: int
    bbox: list[list[float]] = field(default_factory=list)


@dataclass
class PaddleOcrResult:
    text: str
    lines: list[OcrLine]
    engine: str
    lang: str
    page_count: int
    line_count: int
    avg_confidence: float
    min_confidence: float
    max_confidence: float

    def to_dict(self) -> dict:
        return {
            "engine": self.engine,
            "lang": self.lang,
            "page_count": self.page_count,
            "line_count": self.line_count,
            "avg_confidence": round(self.avg_confidence, 4),
            "min_confidence": round(self.min_confidence, 4),
            "max_confidence": round(self.max_confidence, 4),
            "low_confidence_lines": [
                {"text": ln.text[:80], "confidence": round(ln.confidence, 4), "page": ln.page}
                for ln in self.lines
                if ln.confidence < 0.85
            ][:15],
            "sample_lines": [
                {"text": ln.text[:80], "confidence": round(ln.confidence, 4), "page": ln.page}
                for ln in self.lines[:12]
            ],
        }


def _get_ocr_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is not None:
        return _OCR_ENGINE

    try:
        import paddle

        paddle.set_flags({"FLAGS_use_mkldnn": False})
    except Exception:
        pass

    try:
        from paddleocr import PaddleOCR  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "PaddleOCR not installed. Run: pip install -r requirements-optional.txt "
            "then: python scripts/download_paddle_models.py"
        ) from exc

    _OCR_ENGINE = PaddleOCR(
        use_angle_cls=True,
        lang="japan",
        show_log=False,
        enable_mkldnn=False,
        use_gpu=False,
    )
    return _OCR_ENGINE


def _bytes_to_bgr(img_bytes: bytes) -> np.ndarray:
    rgb = np.array(Image.open(__import__("io").BytesIO(img_bytes)).convert("RGB"))
    return rgb[:, :, ::-1].copy()


def _parse_ocr_result(raw: Any, page: int) -> list[OcrLine]:
    lines: list[OcrLine] = []
    if not raw:
        return lines
    page_result = raw[0] if isinstance(raw, list) and raw and isinstance(raw[0], list) else raw
    if not page_result:
        return lines
    for item in page_result:
        if not item or len(item) < 2:
            continue
        bbox, rec = item[0], item[1]
        if isinstance(rec, (list, tuple)) and len(rec) >= 2:
            text, conf = str(rec[0]), float(rec[1])
        else:
            text, conf = str(rec), 0.0
        text = text.strip()
        if text:
            lines.append(OcrLine(text=text, confidence=conf, page=page, bbox=bbox or []))
    return lines


def run_paddle_on_images(image_bytes_list: list[bytes], dpi: int = 200) -> PaddleOcrResult:
    ocr = _get_ocr_engine()
    all_lines: list[OcrLine] = []

    for page_idx, img_bytes in enumerate(image_bytes_list, start=1):
        arr = _bytes_to_bgr(img_bytes)
        try:
            raw = ocr.ocr(arr, cls=True)
        except TypeError:
            raw = ocr.ocr(arr)
        all_lines.extend(_parse_ocr_result(raw, page_idx))

    confs = [ln.confidence for ln in all_lines] or [0.0]
    text = "\n".join(ln.text for ln in all_lines)
    return PaddleOcrResult(
        text=text,
        lines=all_lines,
        engine="PaddleOCR PP-OCR (lang=japan, angle_cls=True)",
        lang="japan",
        page_count=len(image_bytes_list),
        line_count=len(all_lines),
        avg_confidence=sum(confs) / len(confs),
        min_confidence=min(confs),
        max_confidence=max(confs),
    )
