---
name: extract-slide-text
description: >-
  Extract text from each page of a PDF into a markdown file using pdftotext.
  Produces slide_ascii.md with a heading, image reference, and extracted text per slide.
  USE FOR: extract text from PDF slides, get slide text content, PDF to markdown text, slide_ascii.md.
argument-hint: <pdf_path> <output_path> [images_dir]
---

# Extract slide text from PDF

Run the [extract_slide_text.py](./extract_slide_text.py) script to extract the text content of each PDF page into a structured markdown file:

```bash
uv run .agents/skills/extract-slide-text/extract_slide_text.py <pdf_path> <output_path> [images_dir]
```

## Arguments

- `pdf_path` (required): Path to the PDF file.
- `output_path` (required): Path to write the output markdown file
- `images_dir` (optional): Path to the slide images directory. Used to generate correct relative image references. Defaults to `slide_images/`.

## Output format

A markdown file with one section per slide:

```markdown
## Slide 1

![Slide 1](slide_images/slide_1.png)

\```
Extracted text content from slide 1
\```

## Slide 2

![Slide 2](slide_images/slide_2.png)

\```
Extracted text content from slide 2
\```
```

Pages with no extractable text (e.g., full-bleed images) show `(no extractable text)`.

## Why this matters

PDF text extraction is deterministic — it produces ground-truth slide content without relying on vision models. This prevents misidentification of embedded screenshots or demo captures as actual slide content, a common failure mode when using only image-based slide analysis.

## Prerequisites

Poppler utilities must be installed (provides the `pdftotext` command):

- macOS: `brew install poppler`
- Ubuntu: `apt-get install poppler-utils`
