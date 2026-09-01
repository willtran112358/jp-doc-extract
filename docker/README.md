# Docker — run PaddleOCR benchmark on Linux (avoids Windows OneDNN issues)

```bash
docker build -t jp-doc-extract-paddle -f docker/Dockerfile.paddle .
docker run --rm -v "%cd%/output:/app/output" jp-doc-extract-paddle
```

Or on Linux/macOS:

```bash
docker build -t jp-doc-extract-paddle -f docker/Dockerfile.paddle .
docker run --rm -v "$(pwd)/output:/app/output" jp-doc-extract-paddle
```

Writes `output/paddle_benchmark.json` and scan draft with `ocr_stats`.
