"""Dump PDF page text to a UTF-8 file for standards/provenance review.

Usage: python scripts/pdf_text.py <input.pdf> [output.txt]
"""

from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: pdf_text.py <input.pdf> [output.txt]")
    source = Path(sys.argv[1])
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else source.with_suffix(".txt")
    reader = PdfReader(source)
    parts = []
    for index, page in enumerate(reader.pages, 1):
        parts.append(f"===== page {index} =====\n" + (page.extract_text() or ""))
    target.write_text("\n".join(parts), encoding="utf-8")
    print(f"{target} | {len(reader.pages)} pages | {target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
