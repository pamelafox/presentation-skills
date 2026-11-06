# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Extract text from each page of a PDF into a markdown file using pdftotext."""

import subprocess
import sys
from pathlib import Path


def extract_slide_text(pdf_path: str, output_path: str, images_dir: str | None = None) -> str:
    """Extract text from each PDF page into a markdown file.

    Args:
        pdf_path: Path to the PDF file.
        output_path: Path to write the output markdown file.
        images_dir: Optional path to slide images directory (for image references).
                    If provided, image references use paths relative to the output file.

    Returns:
        The generated markdown content.
    """
    pdf = Path(pdf_path)
    out = Path(output_path)

    # Determine total page count by extracting all text and counting form feeds
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"],
            check=True, capture_output=True, text=True,
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            "pdftotext not found. Install poppler:\n"
            "  macOS: brew install poppler\n"
            "  Ubuntu: apt-get install poppler-utils"
        )

    # Count pages from form feeds (pdftotext separates pages with \f)
    all_text = result.stdout
    pages = all_text.split("\f")
    # pdftotext appends a trailing form feed, so the last element is empty
    if pages and pages[-1].strip() == "":
        pages = pages[:-1]
    num_pages = len(pages)

    if num_pages == 0:
        print("Warning: No pages found in PDF")
        out.write_text("")
        return ""

    # Compute relative path from output file to images dir
    img_rel = None
    if images_dir:
        try:
            img_rel = Path(images_dir).resolve().relative_to(out.resolve().parent)
        except ValueError:
            img_rel = Path(images_dir)

    lines: list[str] = []
    for i, page_text in enumerate(pages, start=1):
        text = page_text.strip()
        lines.append(f"## Slide {i}")
        lines.append("")
        if img_rel:
            lines.append(f"![Slide {i}]({img_rel}/slide_{i}.png)")
        else:
            lines.append(f"![Slide {i}](slide_images/slide_{i}.png)")
        lines.append("")
        lines.append("```")
        lines.append(text if text else "(no extractable text)")
        lines.append("```")
        lines.append("")

    content = "\n".join(lines)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content)
    return content


def main():
    if len(sys.argv) < 3:
        print("Usage: uv run extract_slide_text.py <pdf_path> <output_path> [images_dir]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2]
    images_dir = sys.argv[3] if len(sys.argv) > 3 else None

    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    extract_slide_text(pdf_path, output_path, images_dir)

    # Count slides in output
    content = Path(output_path).read_text()
    num_slides = content.count("## Slide ")
    print(f"Extracted text from {num_slides} slides to {output_path}")


if __name__ == "__main__":
    main()
