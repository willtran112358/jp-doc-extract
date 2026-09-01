"""Build Draft JSON schema (generic — no client-specific fields)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from constants import REPO_ID, SCHEMA_VERSION
from mapper import classify_doc


def build_draft(path: Path, text: str, method: str, mapped: dict) -> dict:
    doc_type = classify_doc(text, path.name)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": REPO_ID,
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_file": path.name,
        "doc_type": doc_type,
        "extract_method": method,
        "jp_text_normalized": True,
        "warning": (
            None
            if method not in {"ocr_needed", "xlsx_needs_openpyxl"}
            else (
                "Scan-only PDF — use --mode paddle or --mode vlm"
                if method == "ocr_needed"
                else "Install openpyxl: pip install openpyxl"
            )
        ),
        "soft_warnings": [
            f"{k} confidence < 0.8"
            for k, v in mapped["fields"].items()
            if isinstance(v, dict) and v.get("confidence", 1) < 0.8
        ],
        "draft_fields": mapped["fields"],
        "evidence_history": mapped["evidence"],
        "text_preview": text[:900],
        "next_step": "Human review -> confirm -> downstream system (not included in this PoC)",
    }
