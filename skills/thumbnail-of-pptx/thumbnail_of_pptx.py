# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""Capture a slide thumbnail image from a OneDrive/Office web-viewer presentation.

Given a OneDrive sharing link (or an aka.ms short link that redirects to one),
this opens the PowerPoint web viewer with a headless browser, waits for the
slide to render, and element-screenshots the slide canvas. The result is a
clean 16:9 image of the slide with no viewer chrome -- ideal for a talk
thumbnail.

Unlike fetch-slides, this needs no LibreOffice: it screenshots the slide as
rendered by the Office Online viewer, so it works even when the PPTX itself is
not downloadable (e.g. personal OneDrive shares).
"""

import argparse
import logging
import sys
from pathlib import Path

from playwright.sync_api import Frame, sync_playwright

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# The Office Online viewer renders the deck inside an iframe named "wacIframe".
VIEWER_FRAME_NAME = "wacIframe"


def find_viewer_frame(page) -> Frame:
    """Return the Office web-viewer iframe that contains the slide canvas."""
    # Preferred: the well-known frame name used by the Office Online viewer.
    for frame in page.frames:
        if frame.name == VIEWER_FRAME_NAME:
            return frame
    # Fallback: any frame that actually holds a <canvas> element.
    for frame in page.frames:
        try:
            if frame.query_selector("canvas"):
                return frame
        except Exception:
            continue
    raise RuntimeError(
        "Could not find the slide viewer iframe. Is this a OneDrive/Office "
        "presentation sharing link?"
    )


def capture_thumbnail(
    url: str,
    output_path: Path,
    slide: int = 1,
    scale: int = 2,
    wait_ms: int = 9000,
) -> None:
    """Open the viewer, advance to the requested slide, screenshot the canvas."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                viewport={"width": 1600, "height": 1000},
                device_scale_factor=scale,
            )
            logger.info("Opening %s", url)
            # aka.ms short links redirect to the real OneDrive viewer URL;
            # Playwright follows the redirects for us.
            page.goto(url, wait_until="networkidle", timeout=90000)
            # The viewer streams the slide in after load; give it time to paint.
            page.wait_for_timeout(wait_ms)

            frame = find_viewer_frame(page)

            if slide > 1:
                logger.info("Advancing to slide %d", slide)
                canvas = frame.query_selector("canvas")
                if canvas:
                    canvas.click()
                for _ in range(slide - 1):
                    frame.press("body", "ArrowRight")
                    page.wait_for_timeout(1200)

            canvas = frame.query_selector("canvas")
            if canvas is None:
                raise RuntimeError("No slide canvas found in the viewer frame.")

            canvas.screenshot(path=str(output_path))
        finally:
            # Always close Chromium, even if navigation or rendering failed.
            browser.close()

    logger.info("Saved thumbnail to %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture a slide thumbnail from a OneDrive/Office presentation link."
    )
    parser.add_argument(
        "url",
        help="OneDrive sharing link or aka.ms short link to the presentation.",
    )
    parser.add_argument(
        "output_path",
        help="Path to write the PNG thumbnail (e.g. thumbnail.png).",
    )
    parser.add_argument(
        "--slide",
        type=int,
        default=1,
        help="1-based slide number to capture (default: 1, the title slide).",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=2,
        help="Device scale factor for a crisper image (default: 2).",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=9000,
        help="Milliseconds to wait for the slide to render (default: 9000).",
    )
    args = parser.parse_args()

    try:
        capture_thumbnail(
            url=args.url,
            output_path=Path(args.output_path),
            slide=args.slide,
            scale=args.scale,
            wait_ms=args.wait,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
