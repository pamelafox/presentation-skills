---
name: convert-slides-to-images
description: >-
  Convert a PDF file into individual PNG images, one per page/slide.
  Uses poppler's pdftoppm command. Output files are named slide_1.png, slide_2.png, etc.
  USE FOR: convert PDF to images, split slides into PNGs, extract slide images from PDF.
argument-hint: <pdf_path> <output_dir>
---

# Convert PDF slides to images

Run the [convert_slides_to_images.py](./convert_slides_to_images.py) script to split a PDF into individual PNG images:

```bash
uv run .agents/skills/convert-slides-to-images/convert_slides_to_images.py <pdf_path> <output_dir>
```

## Arguments

- `pdf_path` (required): Path to the PDF file to convert.
- `output_dir` (required): Directory to save the PNG images. Created if it doesn't exist.

## Outputs

Individual PNG files named **slide_1.png**, **slide_2.png**, etc. in the output directory.

## Prerequisites

Poppler utilities must be installed (provides the `pdftoppm` command):

- macOS: `brew install poppler`
- Ubuntu: `apt-get install poppler-utils`
