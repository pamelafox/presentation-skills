---
name: thumbnail-of-pptx
description: >-
  Capture a thumbnail image of a slide from a OneDrive/Office presentation link.
  Opens the PowerPoint web viewer in a headless browser and screenshots the
  slide canvas, producing a clean 16:9 image with no viewer chrome. Works even
  when the PPTX is not downloadable (e.g. personal OneDrive shares), since it
  screenshots the rendered slide rather than converting the file.
  USE FOR: make a thumbnail from a PPTX, screenshot a slide, title-slide image,
  OneDrive slide thumbnail, talk thumbnail from slides.
argument-hint: <url> <output_path>
---

# Thumbnail of a PPTX slide

Run the [thumbnail_of_pptx.py](./thumbnail_of_pptx.py) script to capture a slide
thumbnail from a OneDrive/Office presentation link:

```bash
uv run .agents/skills/thumbnail-of-pptx/thumbnail_of_pptx.py <url> <output_path>
```

## Arguments

- `url` (required): A OneDrive sharing link, or an `aka.ms` short link that
  redirects to one (e.g. `https://aka.ms/my-talk-slides`). The link must open
  the Office Online / PowerPoint **web viewer**.
- `output_path` (required): Path to write the PNG thumbnail (e.g.
  `thumbnail.png`). Parent directories are created if needed.
- `--slide N` (optional): 1-based slide number to capture. Defaults to `1`, the
  title slide.
- `--scale N` (optional): Device scale factor for a crisper image. Defaults to
  `2`.
- `--wait MS` (optional): Milliseconds to wait for the slide to render before
  screenshotting. Defaults to `9000`. Increase for large decks or slow networks.

## Outputs

A single PNG image of the requested slide, cropped to the slide canvas (roughly
16:9, no PowerPoint viewer UI).

## Prerequisites

Playwright browsers must be installed:

```bash
uv run playwright install chromium
```

## How it works

1. Launches headless Chromium and navigates to the URL (following `aka.ms`
   redirects to the real OneDrive viewer).
2. Waits for the network to go idle, then waits a fixed delay for the Office
   Online viewer to stream in and paint the slide.
3. Locates the viewer iframe (named `wacIframe`, with a fallback that finds any
   frame containing a `<canvas>`).
4. Optionally advances to slide `N` by focusing the canvas and pressing the
   right-arrow key.
5. Element-screenshots the slide `<canvas>` so the output contains only the
   slide, not the surrounding viewer chrome.

## Notes

- This is complementary to **fetch-slides**: use `fetch-slides` when you need the
  full deck as a PDF (requires LibreOffice for PPTX), and this skill when you
  just want a lightweight thumbnail image of one slide and the file may not be
  downloadable.
- Because it relies on the public web viewer, the sharing link must be viewable
  by anyone with the link.
