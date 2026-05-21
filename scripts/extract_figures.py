"""Extract large embedded figures from an academic PDF.

The script keeps whole embedded raster figures in page order. Small images
such as journal logos are skipped by default.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract figures from input PDF.")
    parser.add_argument("pdf", nargs="?", default="input.pdf", help="Input PDF path.")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="output/extracted_figures",
        help="Directory for extracted figure images.",
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=600,
        help="Minimum image width in pixels.",
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=300,
        help="Minimum image height in pixels.",
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=250_000,
        help="Minimum image area in pixels.",
    )
    return parser.parse_args()


def pixmap_for_save(doc: fitz.Document, xref: int) -> fitz.Pixmap:
    pix = fitz.Pixmap(doc, xref)
    if pix.alpha or pix.n > 3:
        converted = fitz.Pixmap(fitz.csRGB, pix)
        pix = None
        return converted
    return pix


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    seen_xrefs: set[int] = set()
    manifest: list[dict[str, object]] = []

    for page_index, page in enumerate(doc, start=1):
        for image in page.get_images(full=True):
            xref = image[0]
            if xref in seen_xrefs:
                continue

            pix = fitz.Pixmap(doc, xref)
            width, height = pix.width, pix.height
            area = width * height
            pix = None

            if width < args.min_width or height < args.min_height or area < args.min_area:
                continue

            seen_xrefs.add(xref)
            figure_index = len(manifest) + 1
            filename = f"figure_{figure_index}.png"
            output_path = out_dir / filename

            save_pix = pixmap_for_save(doc, xref)
            save_pix.save(output_path)
            save_pix = None

            manifest.append(
                {
                    "figure_index": figure_index,
                    "figure_label": f"图 {figure_index}",
                    "source_page": page_index,
                    "xref": xref,
                    "filename": filename,
                    "path": str(output_path.as_posix()),
                    "width": width,
                    "height": height,
                }
            )

    manifest_path = out_dir / "figure_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Extracted {len(manifest)} figure image(s) to {out_dir}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
