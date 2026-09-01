# PaddleOCR benchmark (JP invoice)

Aligns with proposal: **PaddleOCR (PP-OCR JP) on EC2 Tokyo** + Bedrock LLM mapping.

## Quick run

```bash
pip install -r requirements-optional.txt
python scripts/download_paddle_models.py   # if SSL blocks auto-download
python scripts/make_scan_sample.py         # image-only PDF from synthetic invoice
python scripts/benchmark_paddle.py
```

Output: `docs/evidence/paddle_benchmark.json`

Single file:

```bash
python src/pipeline.py samples/scan/sample_electricity_invoice_scan.pdf --mode paddle -o output
```

Draft JSON includes `ocr_stats`:

```json
"ocr_stats": {
  "avg_confidence": 0.94,
  "min_confidence": 0.81,
  "line_count": 18,
  "sample_lines": [{ "text": "...", "confidence": 0.97 }]
}
```

## What the benchmark measures

| Metric | Meaning |
|---|---|
| `field_accuracy` | % ground-truth fields matched after regex mapper |
| `ocr_stats.avg_confidence` | Mean PaddleOCR line confidence (0–1) |
| `text` mode on scan PDF | Should be **0%** (no text layer) |
| `paddle` mode on scan PDF | Target **>85%** field accuracy on clean scans |

Ground truth: `scripts/benchmark_paddle.py` → `GROUND_TRUTH` (synthetic samples only).

## Platform notes

| Environment | Status |
|---|---|
| **Linux EC2 / Lambda container** | Recommended (matches production slide) |
| **Windows + Python 3.13** | Paddle 3.x may hit OneDNN error — use WSL2 or EC2 |
| **Model download** | `scripts/download_paddle_models.py` uses `curl -k` if Python SSL fails |

## Expected pipeline (production)

```text
PDF digital  → PyMuPDF text-layer (free, 100% on bundled sample)
PDF scan     → PaddleOCR JP → regex/LLM map → Draft JSON
             → ocr_stats + draft_fields → HITL review
```

## Sample results (text-layer baseline — always works)

| File | Mode | Fields | Accuracy |
|---|---|---|---|
| `sample_electricity_invoice.pdf` | text | 8/8 | 100% |
| `sample_electricity_invoice_scan.pdf` | text | 0/8 | 0% (expected) |

Run `paddle` on scan PDF after models install on Linux; update this table with real `ocr_avg_conf` + accuracy.
