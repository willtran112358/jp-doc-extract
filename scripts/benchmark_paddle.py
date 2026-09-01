# -*- coding: utf-8 -*-
"""
Benchmark text_layer vs PaddleOCR on JP invoice samples.

Usage:
  python scripts/benchmark_paddle.py
  python scripts/benchmark_paddle.py --file samples/scan/sample_electricity_invoice_scan.pdf
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from extractors import extract_text  # noqa: E402
from mapper import map_fields, normalize_number  # noqa: E402

# Ground truth for bundled synthetic samples (scripts/generate_samples.py)
GROUND_TRUTH: dict[str, dict[str, str]] = {
    "sample_electricity_invoice.pdf": {
        "company_name": "デモ電力株式会社",
        "customer_name": "サンプル製造株式会社 本社工場",
        "invoice_no": "INV-2024-04-00001",
        "invoice_date": "2024-05-10",
        "billing_period": "2024年4月",
        "activity_amount": "125000",
        "activity_unit": "kWh",
        "amount_yen": "2750000",
    },
    "sample_electricity_invoice_scan.pdf": {
        "company_name": "デモ電力株式会社",
        "customer_name": "サンプル製造株式会社 本社工場",
        "invoice_no": "INV-2024-04-00001",
        "invoice_date": "2024-05-10",
        "billing_period": "2024年4月",
        "activity_amount": "125000",
        "activity_unit": "kWh",
        "amount_yen": "2750000",
    },
    "sample_gas_delivery.pdf": {
        "company_name": "デモガス株式会社",
        "customer_name": "サンプル製造株式会社 本社工場",
        "invoice_no": "GAS-2024-05-00002",
        "invoice_date": "2024-06-05",
        "billing_period": "2024年5月",
        "activity_amount": "4850",
        "activity_unit": "m3",
    },
    "sample_gas_delivery_scan.pdf": {
        "company_name": "デモガス株式会社",
        "customer_name": "サンプル製造株式会社 本社工場",
        "invoice_no": "GAS-2024-05-00002",
        "invoice_date": "2024-06-05",
        "billing_period": "2024年5月",
        "activity_amount": "4850",
        "activity_unit": "m3",
    },
}


def _norm_val(v: str) -> str:
    return normalize_number(v).replace(" ", "").lower()


def score_fields(expected: dict[str, str], actual: dict) -> dict:
    hits = []
    misses = []
    for key, exp in expected.items():
        got = actual.get(key, {})
        val = got.get("value", "") if isinstance(got, dict) else str(got)
        val = val.strip()
        if not val:
            misses.append({"field": key, "expected": exp, "got": val})
            continue
        if _norm_val(exp) == _norm_val(val) or exp in val or _norm_val(exp) in _norm_val(val):
            hits.append(key)
        else:
            misses.append({"field": key, "expected": exp, "got": val})
    total = len(expected)
    return {
        "expected_fields": total,
        "matched_fields": len(hits),
        "accuracy_pct": round(100 * len(hits) / total, 1) if total else 0,
        "matched": hits,
        "missed": misses,
    }


def run_one(path: Path, mode: str) -> dict:
    extracted = extract_text(path, mode=mode)
    mapped = map_fields(extracted.text, path=path, method=extracted.method)
    row = {
        "file": path.name,
        "mode": mode,
        "extract_method": extracted.method,
        "text_len": len(extracted.text),
        "field_count": len(mapped["fields"]),
        "fields": {k: v.get("value") for k, v in mapped["fields"].items()},
    }
    if extracted.ocr_stats:
        row["ocr_stats"] = extracted.ocr_stats
    gt = GROUND_TRUTH.get(path.name)
    if gt:
        row["field_accuracy"] = score_fields(gt, mapped["fields"])
    return row


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark PaddleOCR vs text-layer on JP invoices")
    parser.add_argument("--file", type=Path, help="Single PDF to test")
    parser.add_argument("-o", default="docs/evidence/paddle_benchmark.json")
    args = parser.parse_args()

    scan_dir = ROOT / "samples" / "scan"
    if args.file:
        targets = [args.file]
    else:
        targets = []
        digital = ROOT / "samples" / "sample_electricity_invoice.pdf"
        if digital.exists():
            targets.append(digital)
        scan_pdf = scan_dir / "sample_electricity_invoice_scan.pdf"
        if not scan_pdf.exists():
            import subprocess

            subprocess.run([sys.executable, str(ROOT / "scripts" / "make_scan_sample.py")], check=False)
        if scan_pdf.exists():
            targets.append(scan_pdf)

    results = []
    for path in targets:
        print(f"\n=== {path.name} ===")
        for mode in ("text", "paddle"):
            try:
                row = run_one(path, mode)
                results.append(row)
                acc = row.get("field_accuracy", {})
                ocr = row.get("ocr_stats", {})
                print(
                    f"  [{mode}] fields={row['field_count']} "
                    f"accuracy={acc.get('accuracy_pct', 'n/a')}% "
                    f"ocr_avg_conf={ocr.get('avg_confidence', 'n/a')}"
                )
                if acc.get("missed"):
                    for m in acc["missed"][:3]:
                        print(f"       miss {m['field']}: expected={m['expected']!r} got={m['got']!r}")
            except Exception as exc:  # noqa: BLE001
                err = str(exc)
                if len(err) > 400:
                    err = err[:400] + "..."
                results.append({"file": path.name, "mode": mode, "error": err})
                print(f"  [{mode}] ERR: {err[:120]}")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "jp-doc-extract",
        "benchmark": "text_layer vs paddle_ocr_jp",
        "results": results,
    }
    out = Path(args.o)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
