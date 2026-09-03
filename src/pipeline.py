"""
Japanese document extraction PoC — text-layer, CSV/XLSX, optional PaddleOCR / VLM.

Usage:
  python src/pipeline.py samples/sample_electricity_invoice.pdf
  python src/pipeline.py samples --batch -o output
  python src/pipeline.py scan.pdf --mode paddle
  python src/pipeline.py scan.pdf --mode vlm
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Allow running as script from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from constants import REPO_ID, SAMPLE_ELECTRICITY
from extractors import extract_text
from mapper import map_fields
from schema import build_draft


def run(path: Path, out_dir: Path, mode: str = "auto") -> Path:
    extracted = extract_text(path, mode=mode)
    mapped = map_fields(extracted.text, path=path, method=extracted.method)
    draft = build_draft(path, extracted, mapped)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-]+", "_", path.stem, flags=re.UNICODE)[:80]
    out_path = out_dir / f"{safe}_draft.json"
    out_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def iter_samples(root: Path) -> list[Path]:
    exts = {".pdf", ".csv", ".xlsx"}
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in exts and "scan" not in p.parts
    )


def run_batch(root: Path, out_dir: Path, mode: str = "auto") -> Path:
    summary = []
    for path in iter_samples(root):
        try:
            out = run(path, out_dir, mode=mode)
            draft = json.loads(out.read_text(encoding="utf-8"))
            summary.append(
                {
                    "file": path.name,
                    "doc_type": draft["doc_type"],
                    "method": draft["extract_method"],
                    "fields": list(draft["draft_fields"].keys()),
                    "field_count": len(draft["draft_fields"]),
                    "journal": (draft.get("journal_draft") or {}).get("status"),
                    "journal_balanced": (draft.get("journal_draft") or {}).get("balanced"),
                    "journal_lines": len((draft.get("journal_draft") or {}).get("lines") or []),
                    "evidence": len(draft["evidence_history"]),
                    "ocr_avg_confidence": (draft.get("ocr_stats") or {}).get("avg_confidence"),
                    "output": out.name,
                    "ok": True,
                }
            )
            jd = draft.get("journal_draft") or {}
            print(
                f"OK  {path.name} -> {draft['doc_type']} "
                f"fields={len(draft['draft_fields'])} "
                f"journal={jd.get('status')} lines={len(jd.get('lines') or [])} "
                f"evidence={len(draft['evidence_history'])}"
            )
        except Exception as exc:  # noqa: BLE001
            summary.append({"file": path.name, "ok": False, "error": str(exc)})
            print(f"ERR {path.name}: {exc}")

    report = {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "tool": REPO_ID,
        "sample_root": "bundled samples",
        "mode": mode,
        "total": len(summary),
        "ok": sum(1 for s in summary if s.get("ok")),
        "results": summary,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "batch_summary.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nBatch: {report['ok']}/{report['total']} OK -> {report_path}")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="JP document to Draft JSON PoC")
    parser.add_argument("input", nargs="?", default=f"samples/{SAMPLE_ELECTRICITY}")
    parser.add_argument("-o", "--out", default="output")
    parser.add_argument("--batch", action="store_true", help="Process all PDF/CSV/XLSX under input dir")
    parser.add_argument(
        "--mode",
        choices=["auto", "text", "paddle", "vlm"],
        default="auto",
        help="auto=text-layer then flag ocr_needed; paddle=PaddleOCR JP; vlm=Claude vision API",
    )
    args = parser.parse_args()
    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"Not found: {path}")

    extract_mode = "auto" if args.mode == "text" else args.mode

    if args.batch or path.is_dir():
        run_batch(path if path.is_dir() else path.parent, Path(args.out), mode=extract_mode)
        return

    out_path = run(path, Path(args.out), mode=extract_mode)
    draft = json.loads(out_path.read_text(encoding="utf-8"))
    print(f"=== {REPO_ID} ===")
    print(f"file     : {path}")
    print(f"doc_type : {draft['doc_type']}")
    print(f"method   : {draft['extract_method']}")
    print(f"status   : {draft['status']}")
    print(f"fields   : {list(draft['draft_fields'].keys())}")
    for k, v in draft["draft_fields"].items():
        print(f"  - {k}: {v.get('value')} (conf={v.get('confidence')})")
    print(f"evidence : {len(draft['evidence_history'])} snippets")
    jd = draft.get("journal_draft") or {}
    print(f"journal  : {jd.get('status')} balanced={jd.get('balanced')} lines={len(jd.get('lines') or [])}")
    for line in jd.get("lines") or []:
        print(
            f"  - {line['side']:6} {line['account_code']} {line['account_name']} "
            f"{line.get('dept') or '-'} {line['amount']}"
        )
    print(f"output   : {out_path}")
    if draft.get("ocr_stats"):
        ocr = draft["ocr_stats"]
        print(
            f"ocr      : avg_conf={ocr.get('avg_confidence')} "
            f"lines={ocr.get('line_count')} min={ocr.get('min_confidence')}"
        )
    if draft.get("warning"):
        print(f"warning  : {draft['warning']}")


if __name__ == "__main__":
    main()
