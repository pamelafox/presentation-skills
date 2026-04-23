# 🎤 Presentation Skills

A collection of agent skills for working with presentations.

## Skills

### 📄 pdf-to-markdown

Converts PDF and other document formats (PowerPoint, Word, Excel) to Markdown using [Microsoft's markitdown](https://github.com/microsoft/markitdown) package.

**Use when:** converting a PDF/PPTX/DOCX to Markdown, extracting text from a document, or reading/parsing document content.

### 🔍 review-presentation

Reviews presentation slides for accuracy and consistency with the code samples in the repository.

**Use when:** you want feedback on your slides — checking for errors, inconsistencies, or areas that need clarification relative to the repo's code.

### 🎞️ capture-video-frames

Captures frames from a YouTube video at a regular interval, produces a manifest mapping filenames to timestamps, and describes each frame using the `describe-frame` subagent.

**Use when:** extracting video frames, capturing screenshots from YouTube, or doing frame-by-frame video analysis.

### 🖼️ convert-slides-to-images

Converts a PDF file into individual PNG images (one per slide) using poppler's `pdftoppm` command.

**Use when:** converting PDF slides to images, splitting a PDF into per-slide PNGs.

### 📝 extract-slide-text

Extracts text from each page of a PDF into a structured markdown file using `pdftotext`.

**Use when:** getting the text content of PDF slides, producing a `slide_ascii.md` ground-truth file.

### 🎙️ extract-transcript

Extracts a timestamped transcript from a YouTube video using the YouTube Transcript API.

**Use when:** fetching a video transcript, transcribing a YouTube video, getting YouTube captions.

### 📥 fetch-slides

Fetches presentation slides from a URL and converts them to PDF. Supports direct PDF URLs, PPTX URLs, OneDrive sharing links, and RevealJS HTML presentations.

**Use when:** downloading slides from a URL, converting PPTX to PDF, fetching RevealJS or OneDrive slides.

### 🗂️ outline-slides

Generates a numbered outline of presentation slides with one-sentence summaries per slide.

**Use when:** summarizing slides, creating a slide outline, describing slide images.

### ✍️ generate-writeup

Generates an annotated blog-style write-up from a presentation's slides and video recording. Orchestrates the full pipeline: fetching slides, converting to images, extracting transcript, generating chapters, outlining slides, and producing the final annotated markdown.

**Use when:** creating a blog post or write-up from a recorded presentation.

## Installation

Install all skills using the [`skills`](https://www.npmjs.com/package/skills) CLI:

```sh
npx skills add pamelafox/presentation-skills
```

Or install individual skills:

```sh
npx skills add pamelafox/presentation-skills/pdf-to-markdown
npx skills add pamelafox/presentation-skills/review-presentation
npx skills add pamelafox/presentation-skills/capture-video-frames
npx skills add pamelafox/presentation-skills/convert-slides-to-images
npx skills add pamelafox/presentation-skills/extract-slide-text
npx skills add pamelafox/presentation-skills/extract-transcript
npx skills add pamelafox/presentation-skills/fetch-slides
npx skills add pamelafox/presentation-skills/outline-slides
npx skills add pamelafox/presentation-skills/generate-writeup
```
