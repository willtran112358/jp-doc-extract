"""Fail if journal lines do not balance on bundled PDFs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pipeline import run  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def main() -> None:
    fails = []
    for pdf in sorted((ROOT / "samples").glob("*.pdf")):
        path = run(pdf, OUT)
        draft = json.loads(path.read_text(encoding="utf-8"))
        jd = draft["journal_draft"]
        if jd.get("status") == "skipped":
            print(f"SKIP {pdf.name}")
            continue
        if not jd.get("balanced"):
            fails.append(pdf.name)
            print(f"FAIL {pdf.name} unbalanced {jd}")
        else:
            print(f"OK   {pdf.name} lines={len(jd['lines'])} gross={jd['gross']}")
    if fails:
        raise SystemExit(f"unbalanced: {fails}")
    print("journal check passed")


if __name__ == "__main__":
    main()
