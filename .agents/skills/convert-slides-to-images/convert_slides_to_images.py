# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Convert a PDF file into individual PNG slide images using pdftoppm."""

import subprocess
import sys
from pathlib import Path


def pdf2imgs(pdf_path: str, output_dir: str, prefix: str = "slide") -> list[str]:
    """Split a PDF into individual PNG images."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cmd = ["pdftoppm", "-png", str(pdf_path), str(output_path / prefix)]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError:
        raise FileNotFoundError(
            "pdftoppm not found. Install poppler:\n"
            "  macOS: brew install poppler\n"
            "  Ubuntu: apt-get install poppler-utils"
        )

    # pdftoppm creates files like slide-01.png, slide-02.png, etc.
    # Rename to slide_1.png, slide_2.png format (strip leading zeros)
    image_files = []
    for f in sorted(output_path.glob(f"{prefix}-*.png")):
        page_num = int(f.stem.split("-")[-1])
        new_name = output_path / f"{prefix}_{page_num}.png"
        f.rename(new_name)
        image_files.append(str(new_name))

    return image_files


def main():
    if len(sys.argv) < 3:
        print("Usage: uv run convert_slides_to_images.py <pdf_path> <output_dir>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]

    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    image_files = pdf2imgs(pdf_path, output_dir)
    print(f"Created {len(image_files)} slide images in {output_dir}")
    for f in image_files:
        print(f"  {f}")


if __name__ == "__main__":
    main()
