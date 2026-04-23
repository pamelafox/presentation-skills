# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "playwright",
# ]
# ///
"""Fetch presentation slides from a URL and convert to PDF."""

import logging
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def is_onedrive_url(url: str) -> bool:
    """Check if URL is a OneDrive sharing link."""
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc in ("onedrive.live.com", "1drv.ms")
    except Exception:
        return False


def get_onedrive_download_url(url: str) -> str:
    """Convert a OneDrive sharing URL to a direct download URL."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params["download"] = ["1"]
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def convert_pptx_to_pdf(pptx_path: str, output_path: str) -> str:
    """Convert a PPTX file to PDF using LibreOffice."""
    pptx_path = Path(pptx_path)
    output_path = Path(output_path)
    output_dir = output_path.parent

    soffice_paths = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        shutil.which("soffice"),
        shutil.which("libreoffice"),
    ]

    soffice = None
    for path in soffice_paths:
        if path and Path(path).exists():
            soffice = path
            break

    if not soffice:
        raise FileNotFoundError(
            "LibreOffice not found. Install it:\n"
            "  macOS: brew install --cask libreoffice\n"
            "  Ubuntu: apt-get install libreoffice"
        )

    logger.info(f"Converting PPTX to PDF using LibreOffice: {soffice}")

    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(pptx_path),
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"LibreOffice output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to convert PPTX to PDF: {e.stderr}")

    generated_pdf = output_dir / f"{pptx_path.stem}.pdf"
    if not generated_pdf.exists():
        raise FileNotFoundError(f"Expected PDF not found: {generated_pdf}")

    if generated_pdf != output_path:
        generated_pdf.rename(output_path)

    logger.info(f"Saved PDF to: {output_path}")
    return str(output_path)


def extract_revealjs_content(url: str, output_path: str) -> str:
    """Extract text content and links from RevealJS slides."""
    logger.info(f"Extracting RevealJS slide content from: {url}")

    response = httpx.get(url, follow_redirects=True)
    html = response.text

    class SlideExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.slides = []
            self.current_slide = []
            self.in_slides = False
            self.in_section = False
            self.is_heading_slide = False
            self.section_depth = 0
            self.current_tag = None
            self.links = []

        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            self.current_tag = tag

            if tag == "div" and "slides" in attrs_dict.get("class", ""):
                self.in_slides = True
            elif tag == "section" and self.in_slides:
                if self.section_depth == 0:
                    self.in_section = True
                    self.current_slide = []
                    self.links = []
                    classes = attrs_dict.get("class", "")
                    self.is_heading_slide = "heading" in classes
                self.section_depth += 1
            elif tag == "a" and self.in_section:
                href = attrs_dict.get("href", "")
                if href and not href.startswith("#"):
                    self.links.append(href)
            elif tag == "img" and self.in_section:
                alt = attrs_dict.get("alt", "")
                if alt:
                    self.current_slide.append(f"[Image: {alt}]")

        def handle_endtag(self, tag):
            if tag == "section" and self.in_slides:
                self.section_depth -= 1
                if self.section_depth == 0 and self.in_section:
                    self.in_section = False
                    slide_content = " ".join(self.current_slide).strip()
                    if slide_content or self.links:
                        self.slides.append(
                            {
                                "content": slide_content,
                                "links": self.links.copy(),
                                "is_heading": self.is_heading_slide,
                            }
                        )
                    self.is_heading_slide = False

        def handle_data(self, data):
            if self.in_section:
                text = data.strip()
                if text:
                    self.current_slide.append(text)

    parser = SlideExtractor()
    parser.feed(html)

    lines = ["# RevealJS Slide Content\n"]
    for i, slide in enumerate(parser.slides, 1):
        slide_type = "SECTION HEADING" if slide["is_heading"] else "Slide"
        lines.append(f"## {slide_type} {i}\n")
        if slide["content"]:
            lines.append(slide["content"])
            lines.append("")
        if slide["links"]:
            lines.append("**Links:**")
            for link in slide["links"]:
                lines.append(f"- {link}")
            lines.append("")

    content = "\n".join(lines)
    Path(output_path).write_text(content)
    logger.info(f"Saved slide content to: {output_path}")
    return output_path


def fetch_revealjs_pdf(url: str, output_path: str) -> str:
    """Fetch a RevealJS presentation as PDF using Playwright."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params["print-pdf"] = [""]
    new_query = urlencode(query_params, doseq=True).replace("print-pdf=", "print-pdf")
    print_url = urlunparse(parsed._replace(query=new_query))

    logger.info(f"Fetching RevealJS PDF from: {print_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(print_url, wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.pdf(
            path=output_path,
            format="Letter",
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()

    logger.info(f"Saved PDF to: {output_path}")
    return output_path


def fetch_slides_from_url(url: str, output_dir: str) -> tuple[str, str | None]:
    """Fetch slides from a URL, detecting whether it's a PDF, PPTX, or HTML (RevealJS)."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    pdf_path = output_path / "slides.pdf"
    pptx_path = output_path / "slides.pptx"
    html_content_path = output_path / "slides_content.md"

    if is_onedrive_url(url):
        download_url = get_onedrive_download_url(url)
        logger.info(f"Detected OneDrive URL, using download URL: {download_url}")

        response = httpx.get(download_url, follow_redirects=True, timeout=60.0)
        content_type = response.headers.get("content-type", "").lower()

        if "presentationml" in content_type or "pptx" in content_type:
            logger.info("Detected PPTX, downloading and converting to PDF...")
            pptx_path.write_bytes(response.content)
            convert_pptx_to_pdf(str(pptx_path), str(pdf_path))
            return str(pdf_path), None
        elif "application/pdf" in content_type:
            logger.info("Detected PDF from OneDrive, downloading...")
            pdf_path.write_bytes(response.content)
            return str(pdf_path), None
        else:
            raise ValueError(f"Unexpected content type from OneDrive: {content_type}")

    logger.info(f"Checking content type for: {url}")
    response = httpx.head(url, follow_redirects=True)
    content_type = response.headers.get("content-type", "").lower()

    if "application/pdf" in content_type:
        logger.info("Detected PDF, downloading directly...")
        response = httpx.get(url, follow_redirects=True)
        pdf_path.write_bytes(response.content)
        logger.info(f"Saved PDF to: {pdf_path}")
        return str(pdf_path), None
    elif "presentationml" in content_type or "pptx" in content_type:
        logger.info("Detected PPTX, downloading and converting to PDF...")
        response = httpx.get(url, follow_redirects=True)
        pptx_path.write_bytes(response.content)
        convert_pptx_to_pdf(str(pptx_path), str(pdf_path))
        return str(pdf_path), None
    elif "text/html" in content_type:
        logger.info("Detected HTML, treating as RevealJS presentation...")
        fetch_revealjs_pdf(url, str(pdf_path))
        extract_revealjs_content(url, str(html_content_path))
        return str(pdf_path), str(html_content_path)
    else:
        logger.warning(
            f"Unknown content type '{content_type}', attempting RevealJS fetch..."
        )
        fetch_revealjs_pdf(url, str(pdf_path))
        return str(pdf_path), None


def main():
    if len(sys.argv) < 3:
        print("Usage: uv run fetch_slides.py <url> <output_dir>")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2]

    pdf_path, html_content_path = fetch_slides_from_url(url, output_dir)
    print(f"PDF saved to: {pdf_path}")
    if html_content_path:
        print(f"Slide content saved to: {html_content_path}")


if __name__ == "__main__":
    main()
