# -*- coding: utf-8 -*-
"""Pre-download PaddleOCR JP models (use if pip SSL fails on Windows)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

# Multilingual det + japan rec (PaddleOCR 2.x lang=japan)
MODELS = [
    (
        "det",
        "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/Multilingual_PP-OCRv3_det_infer.tar",
        "Multilingual_PP-OCRv3_det_infer",
    ),
    (
        "rec",
        "https://paddleocr.bj.bcebos.com/PP-OCRv4/multilingual/japan_PP-OCRv4_rec_infer.tar",
        "japan_PP-OCRv4_rec_infer",
    ),
    (
        "cls",
        "https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar",
        "ch_ppocr_mobile_v2.0_cls_infer",
    ),
]


def cache_root() -> Path:
    return Path(os.environ.get("PADDLEOCR_HOME", Path.home() / ".paddleocr"))


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print("exists", dest)
        return
    print("download", url)
    # curl often works when Python SSL fails on corp laptops
    r = subprocess.run(
        ["curl.exe", "-L", "-k", "-o", str(dest), url],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"curl failed: {r.stderr or r.stdout}")


def extract(tar_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path) as tf:
        tf.extractall(out_dir.parent)
    print("extracted ->", out_dir)


def main() -> None:
    root = cache_root() / "whl"
    for kind, url, folder in MODELS:
        sub = "det/ml" if kind == "det" else ("rec/japan" if kind == "rec" else "cls")
        target_dir = root / sub / folder
        if (target_dir / "inference.pdmodel").exists():
            print("skip", target_dir)
            continue
        tar_path = target_dir.with_suffix(".tar")
        download(url, tar_path)
        extract(tar_path, target_dir)
        tar_path.unlink(missing_ok=True)
    print("Done. Run: python scripts/benchmark_paddle.py")


if __name__ == "__main__":
    main()
