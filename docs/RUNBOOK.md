# Runbook — jp-doc-extract

## 1. Prerequisites

- Python 3.10+
- Windows / macOS / Linux

## 2. Install

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
python scripts/generate_samples.py
```

## 3. Run bundled samples

```bash
# single PDF
python src/pipeline.py samples/sample_electricity_invoice.pdf

# all samples
python src/pipeline.py samples --batch -o output
```

Expected:

```text
OK  sample_electricity_invoice.pdf → electricity_invoice fields=7 ...
OK  sample_gas_delivery.pdf → gas_invoice fields=5 ...
OK  sample_activity_energy.csv → activity_table fields=4 ...

Batch: 3/3 OK → output/batch_summary.json
```

## 4. Use your own files (local only — do not commit)

```bash
python src/pipeline.py "C:\path\to\your\docs" --batch -o output
```

Keep private PDFs/CSVs out of git (`.gitignore` already excludes `output/`).

## 5. Scanned PDF — PaddleOCR

```bash
pip install -r requirements-optional.txt
python src/pipeline.py path/to/scan.pdf --mode paddle -o output
```

Notes:

- First run downloads JP OCR models (~100MB+).
- On AWS Lambda, use a **container image** (same pattern as colleague PoC).

## 6. Scanned PDF — VLM (Claude vision)

```bash
pip install anthropic
set ANTHROPIC_API_KEY=sk-ant-...     # Windows
export ANTHROPIC_API_KEY=sk-ant-...  # Linux/macOS
python src/pipeline.py path/to/scan.pdf --mode vlm -o output
```

Use only synthetic or approved test data until production trust layer is in place.

## 7. Regenerate docs screenshots

```bash
python src/pipeline.py samples --batch -o docs/evidence
copy docs\evidence\*_draft.json docs\evidence\  # ensure evidence folder populated
python docs/make_screenshot.py
```

## 8. Troubleshooting

| Issue | Fix |
|---|---|
| `ocr_needed` warning on PDF | File is scan-only → `--mode paddle` or `--mode vlm` |
| CSV `field_count=0` | Check headers match JP hints in `mapper.CSV_COLUMN_MAP` |
| `openpyxl` missing | `pip install openpyxl` |
| Paddle import error | `pip install -r requirements-optional.txt` |
| VLM auth error | Set `ANTHROPIC_API_KEY` in `.env` |

## 9. Suggested hybrid architecture mapping

```text
This PoC                    Production hybrid
─────────────────────────────────────────────
text_layer / paddle         JP OCR worker (Lambda)
regex + csv_column          LLM field mapping (Bedrock/Azure when available)
draft_fields JSON           Draft DB → CRM Draft object
evidence_history            Lineage metadata (snippet + external bbox ref)
```
