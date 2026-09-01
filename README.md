# jp-doc-extract

Public PoC: **Japanese business documents → structured Draft JSON** with evidence snippets.

Synthetic samples only — safe to share. Use your own files locally for private testing.

## Why this repo helps

| Gap in cloud options | This PoC |
|---|---|
| Amazon Textract — no JP OCR | Text-layer + optional **PaddleOCR (JP)** |
| Bedrock Sonnet blocked on some accounts | Optional **Claude API** vision (`--mode vlm`) |
| Need fast feasibility before hybrid build | **Zero API cost** path on digital PDFs |
| CSV activity tables often missed | **Column-aware CSV mapper** (sum usage by header) |

See [docs/COMPARISON.md](docs/COMPARISON.md) for Textract / Azure DI / VLM trade-offs.

## Quick start

```bash
git clone https://github.com/willtran112358/jp-doc-extract.git
cd jp-doc-extract
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows
pip install -r requirements.txt

# bundled synthetic samples
python scripts/generate_samples.py
python src/pipeline.py samples/sample_electricity_invoice.pdf
python src/pipeline.py samples --batch -o output
```

Output: `output/*_draft.json` + `output/batch_summary.json`.

## Extraction modes

| Mode | Command | When |
|---|---|---|
| **auto** (default) | `python src/pipeline.py file.pdf` | Digital PDF with text layer |
| **text** | `--mode text` | Same as auto, no OCR fallback |
| **paddle** | `--mode paddle` | Scanned PDF (install optional deps) |
| **vlm** | `--mode vlm` | Scan / complex layout (`ANTHROPIC_API_KEY`) |

```bash
pip install -r requirements-optional.txt
copy .env.example .env   # set ANTHROPIC_API_KEY for vlm
python src/pipeline.py scan.pdf --mode paddle
python src/pipeline.py scan.pdf --mode vlm
```

## Screenshots

| Step | Screenshot |
|---|---|
| Setup | ![setup](docs/screenshots/01_setup.png) |
| Batch run | ![batch](docs/screenshots/02_batch.png) |
| Single file | ![single](docs/screenshots/03_single_run.png) |
| Draft JSON | ![draft](docs/screenshots/04_draft_json.png) |
| Summary | ![summary](docs/screenshots/05_batch_summary.png) |

Full runbook: [docs/RUNBOOK.md](docs/RUNBOOK.md)

## Draft JSON shape

```json
{
  "tool": "jp-doc-extract",
  "status": "draft",
  "doc_type": "electricity_invoice",
  "extract_method": "text_layer",
  "draft_fields": {
    "company_name": { "value": "...", "confidence": 0.9 }
  },
  "evidence_history": [
    { "field": "company_name", "snippet": "...", "source": "regex_jp" }
  ]
}
```

## Layout

```text
src/
  pipeline.py      # CLI entry
  extractors.py    # PDF / CSV / XLSX / paddle / vlm
  mapper.py        # regex + CSV column mapping
  schema.py        # Draft JSON builder
scripts/
  generate_samples.py
samples/             # synthetic PDF + CSV (regenerate anytime)
docs/
  RUNBOOK.md
  COMPARISON.md
  evidence/          # committed batch artifacts
  screenshots/
```

## Scope

- **In scope:** extract → classify → map fields → Draft JSON + evidence
- **Out of scope:** CRM integration, auto-commit to production DB, enterprise auth

## License

MIT — see [LICENSE](LICENSE). Bundled samples are synthetic; do not commit real client documents.
