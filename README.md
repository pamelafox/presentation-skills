# 🎤 Presentation Skills

A collection of [agent skills](https://agentskills.io/home) for working with presentations.

## Table of Contents

- [Skills](#skills)
- [Installing with npx skills CLI](#installing-with-npx-skills-cli)
- [Installing with gh CLI](#installing-with-gh-cli)

## Skills

### 📄 pdf-to-markdown

Converts PDF and other document formats (PowerPoint, Word, Excel) to Markdown using [Microsoft's markitdown](https://github.com/microsoft/markitdown) package.

**Use when:** converting a PDF/PPTX/DOCX to Markdown, extracting text from a document, or reading/parsing document content.

### 🎞️ make-revealjs-presentation

Creates or updates a RevealJS HTML presentation using the repository's bundled slide template.

**Use when:** starting a new RevealJS talk deck, creating HTML slides from an outline, or reusing the repository's presentation template for a new conference talk.

### 🔍 review-presentation

Reviews presentation slides for accuracy and consistency with the code samples in the repository.

**Use when:** you want feedback on your slides — checking for errors, inconsistencies, or areas that need clarification relative to the repo's code.

### 🎞️ capture-video-frames

Captures frames from a YouTube video at a regular interval, produces a manifest mapping filenames to timestamps, and describes each frame using the `describe-frame` subagent.

**Use when:** extracting video frames, capturing screenshots from YouTube, or doing frame-by-frame video analysis.

### 🖼️ convert-slides-to-images

Converts a PDF file into individual PNG images (one per slide) using poppler's `pdftoppm` command.

**Use when:** converting PDF slides to images, splitting a PDF into per-slide PNGs.

### 🖼️ thumbnail-of-pptx

Captures a thumbnail image of a slide from a OneDrive/Office presentation link by opening the PowerPoint web viewer in a headless browser and screenshotting the slide canvas. Works even when the PPTX itself is not downloadable.

**Use when:** making a thumbnail from a PPTX, screenshotting a title slide, or generating a talk thumbnail from OneDrive-hosted slides.

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

### 📝 youtube-description

Generates a `youtube_description.md` with a brief intro, relevant links, and clickable `MM:SS`/`H:MM:SS` timestamps for each question.

**Use when:** creating a plain-text YouTube description from a recording, with timestamp lines that YouTube auto-links.

### 💬 youtube-live-chat

Downloads live chat messages from YouTube videos using yt-dlp. Supports output with or without timestamps.

**Use when:** fetching live chat or chat replay from a YouTube live stream or past stream.

### 🗣️ discussion-commenter

Posts Q&A entries from markdown writeups as individual comments to a GitHub Discussion. Each `## ` section in the writeup becomes a separate comment, prefixed with a date.

**Use when:** posting Q&A content from a markdown writeup file to a GitHub Discussion thread.

## Installation

### Installing with npx skills CLI

Install all skills using the [`skills`](https://www.npmjs.com/package/skills) CLI:

```sh
npx skills add pamelafox/presentation-skills
```

Or install individual skills:

```sh
npx skills add pamelafox/presentation-skills/pdf-to-markdown
npx skills add pamelafox/presentation-skills/make-revealjs-presentation
npx skills add pamelafox/presentation-skills/review-presentation
npx skills add pamelafox/presentation-skills/capture-video-frames
npx skills add pamelafox/presentation-skills/convert-slides-to-images
npx skills add pamelafox/presentation-skills/thumbnail-of-pptx
npx skills add pamelafox/presentation-skills/extract-slide-text
npx skills add pamelafox/presentation-skills/extract-transcript
npx skills add pamelafox/presentation-skills/fetch-slides
npx skills add pamelafox/presentation-skills/outline-slides
npx skills add pamelafox/presentation-skills/generate-writeup
npx skills add pamelafox/presentation-skills/youtube-description
npx skills add pamelafox/presentation-skills/youtube-live-chat
npx skills add pamelafox/presentation-skills/discussion-commenter
```

### Installing with gh CLI

Install skills using the [GitHub CLI](https://github.blog/changelog/2026-04-16-manage-agent-skills-with-github-cli/):

```sh
gh skill install pamelafox/presentation-skills
```

Or install individual skills:

```sh
gh skill install pamelafox/presentation-skills pdf-to-markdown
gh skill install pamelafox/presentation-skills make-revealjs-presentation
gh skill install pamelafox/presentation-skills review-presentation
gh skill install pamelafox/presentation-skills capture-video-frames
gh skill install pamelafox/presentation-skills convert-slides-to-images
gh skill install pamelafox/presentation-skills thumbnail-of-pptx
gh skill install pamelafox/presentation-skills extract-slide-text
gh skill install pamelafox/presentation-skills extract-transcript
gh skill install pamelafox/presentation-skills fetch-slides
gh skill install pamelafox/presentation-skills outline-slides
gh skill install pamelafox/presentation-skills generate-writeup
gh skill install pamelafox/presentation-skills youtube-description
gh skill install pamelafox/presentation-skills youtube-live-chat
gh skill install pamelafox/presentation-skills discussion-commenter
```

You can also target a specific agent when installing with `gh`:

```sh
gh skill install pamelafox/presentation-skills make-revealjs-presentation --agent claude-code
```
