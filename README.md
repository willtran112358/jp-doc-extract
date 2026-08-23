# CLAP AI OCR POC — AI Data Extraction track

Short PoC: **JP sample PDF → text extract → Draft JSON** (HITL later).  
Related solution tracks (from FS / proposals):

| Track | Scope | This repo |
|-------|--------|-----------|
| **EDINET / MCP** | FSA API, XBRL, Tenant=legal entity | Out of scope |
| **AI Extraction** | User upload → OCR/extract → Draft → Confirm → Core | **In scope (PoC)** |

Q&A anchors (AI Extraction): sample docs required · Draft 未確定 + user confirm (no auto-save Core) · JP residency · Blob JP for files · Draft persisted in DB.

## Quick start

```bash
cd clap-ai-ocr-poc
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src/ocr_pipeline.py samples/jp_electricity_invoice_sakura.pdf
python src/ocr_pipeline.py samples/jp_gas_delivery_sakura.pdf -o output
```

Output: `output/*_draft.json` — fields + evidence snippets + `status: draft`.

## How to run (screenshot)

See [docs/screenshots/run_sample.png](docs/screenshots/run_sample.png).

Expected console:

```text
=== CLAP AI OCR POC ===
file     : samples/jp_electricity_invoice_sakura.pdf
method   : text_layer
status   : draft (Draft / 未確定)
fields   : [...]
evidence : N snippets
output   : output/jp_electricity_invoice_sakura_draft.json
```

## What it does / does not

- **Does:** extract text from JP PDF (text layer), regex-map invoice/GHG-ish fields, emit Draft JSON + evidence snippets.
- **Does not:** Salesforce write, Agentforce, Cloud JP OCR API, EDINET, auto-save Core.

Scan-only PDFs (`method=ocr_needed`): Phase-2 — plug Azure DI / Document AI / EasyOCR (JP region).

## Samples

Client-style dummy docs (WOV2 AI sample pack):

- `samples/jp_electricity_invoice_sakura.pdf` — 電力請求書
- `samples/jp_gas_delivery_sakura.pdf` — 都市ガス納品伝票

## GitLab (git.vmo.dev)

1. Add SSH public key for this laptop: [SSH Keys](https://git.vmo.dev/-/user_settings/ssh_keys) → **Add new key**
2. Create empty project on GitLab (e.g. `WOV2/clap-ai-ocr-poc`)
3. Push:

```bash
git remote add origin git@git.vmo.dev:GROUP/clap-ai-ocr-poc.git
git push -u origin main
```

## Layout

```text
src/ocr_pipeline.py   # extract + map → Draft JSON
samples/              # JP PDF samples
output/               # generated drafts (gitignored)
docs/screenshots/     # run screenshot
```
