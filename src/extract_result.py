"""Extraction result with optional Paddle OCR statistics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExtractResult:
    text: str
    method: str
    ocr_stats: dict | None = None
    extra: dict = field(default_factory=dict)
