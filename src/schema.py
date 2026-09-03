"""Build Draft JSON schema (generic — no client-specific fields)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from constants import REPO_ID, SCHEMA_VERSION
from extract_result import ExtractResult
from journal import apply_journal
from mapper import classify_doc


def build_draft(path: Path, extracted: ExtractResult, mapped: dict) -> dict:
    text = extracted.text
    method = extracted.method
    doc_type = classify_doc(text, path.name)
    journal = apply_journal(
        mapped["fields"], doc_type=doc_type, text=text, source_file=path.name
    )
    evidence = list(mapped["evidence"]) + list(journal.get("evidence") or [])
    draft = {
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
        "journal_draft": {k: v for k, v in journal.items() if k != "evidence"},
        "hitl": {
            "original": path.name,
            "extract_fields": list(mapped["fields"].keys()),
            "journal": journal.get("status"),
            "approval": None,
            "registered": None,
        },
        "evidence_history": evidence,
        "text_preview": text[:900],
        "next_step": "HITL: original + extract + journal_draft → confirm (no auto-post)",
    }
    if extracted.ocr_stats:
        draft["ocr_stats"] = extracted.ocr_stats
    return draft
