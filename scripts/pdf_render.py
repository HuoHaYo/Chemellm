"""Render PDF pages to PNG for manual reading (no OCR).

Usage: python scripts/pdf_render.py <input.pdf> <outdir> [dpi]
"""

from __future__ import annotations

import sys
from pathlib import Path

import pypdfium2 as pdfium


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: pdf_render.py <input.pdf> <outdir> [dpi]")
    source = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 160
    outdir.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(source)
    for index in range(len(document)):
        page = document[index]
        image = page.render(scale=dpi / 72).to_pil()
        target = outdir / f"page-{index + 1:02d}.png"
        image.save(target)
        print(target, image.size)


if __name__ == "__main__":
    main()
