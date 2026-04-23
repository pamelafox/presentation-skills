---
name: fetch-slides
description: >-
  Fetch presentation slides from a URL and convert them to PDF.
  Supports direct PDF URLs, PPTX URLs, OneDrive sharing links, and RevealJS HTML presentations.
  For RevealJS, also extracts slide text content and links to a markdown file.
  USE FOR: download slides, fetch slides from URL, convert PPTX to PDF, get RevealJS slides, OneDrive slides.
argument-hint: <url> <output_dir>
---

# Fetch slides from a URL

Run the [fetch_slides.py](./fetch_slides.py) script to download and convert slides:

```bash
uv run .agents/skills/fetch-slides/fetch_slides.py <url> <output_dir>
```

## Arguments

- `url` (required): URL of the slides. Supported formats:
  - Direct PDF URL (e.g., https://example.com/slides.pdf)
  - PPTX URL (auto-detected via Content-Type header)
  - OneDrive sharing link (e.g., `https://onedrive.live.com/:p:/g/personal/...` or `https://1drv.ms/...`)
  - RevealJS HTML presentation URL (e.g., `https://example.com/slides/`)
- `output_dir` (required): Directory to save output files. Created if it doesn't exist.

## Outputs

- **slides.pdf** — Always produced. The presentation as a PDF file.
- **slides_content.md** — Only for RevealJS presentations. Contains extracted text content and links from each slide, with section headings marked.

## Prerequisites

- **For PPTX conversion**: LibreOffice must be installed
  - macOS: `brew install --cask libreoffice`
  - Ubuntu: `apt-get install libreoffice`
- **For RevealJS presentations**: Playwright browsers must be installed
  - `uv run playwright install chromium`

## How it works

1. The script makes an HTTP HEAD request to detect the content type
2. Based on the content type:
   - **PDF**: Downloads directly
   - **PPTX**: Downloads the file, then converts to PDF using LibreOffice (headless mode)
   - **OneDrive**: Converts the sharing URL to a direct download URL (appends `?download=1`), then handles as PDF or PPTX
   - **RevealJS HTML**: Uses Playwright to open the presentation with `?print-pdf` appended, renders to PDF. Also parses the HTML to extract slide text content and links.
