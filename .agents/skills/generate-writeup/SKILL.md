---
name: generate-writeup
description: >-
  Generate an annotated blog-style write-up from a presentation's slides and video recording.
  Orchestrates the full pipeline: fetching slides, converting to images, extracting transcript,
  generating chapters, outlining slides, and producing the final annotated markdown.
  USE FOR: write-up, blog post, presentation summary, annotated write-up, generate writeup.
argument-hint: <presentation_folder>
---

# Generate annotated write-up from a presentation

You are generating a blog-style write-up from a presentation. The user will provide a **presentation folder** path (e.g., `presentations/my-talk`). That folder must contain a `presentation.md` file.

## presentation.md format

```markdown
# Talk title

- **Date:** 2026-01-15
- **Video:** https://www.youtube.com/watch?v=VIDEO_ID
- **Slides:** slides.pdf
- **Transcript:** transcript.txt

## Notes

Extra notes here
```

Required fields: **Video** and **Slides**. All others are optional.
**Slides** can be a local PDF path, PDF URL, PPTX URL, OneDrive link, or RevealJS URL.
**Video** can be a YouTube URL or local MP4 path.

## Pipeline

Follow these steps in order. Cache all intermediate outputs in `<presentation_folder>/outputs/` so subsequent runs skip completed steps.

### Step 1: Resolve slides

- If **Slides** in presentation.md is a URL, fetch and convert to PDF:
  ```bash
  uv run .agents/skills/fetch-slides/fetch_slides.py <url> <presentation_folder>/outputs
  ```
  This produces `slides.pdf` (and `slides_content.md` for RevealJS URLs).
- If **slides** is a local file path (relative to the presentation folder), use it directly.
- Skip if `<presentation_folder>/outputs/slides.pdf` already exists.

### Step 2: Convert slides to images

Split the PDF into individual PNGs:

```bash
uv run .agents/skills/convert-slides-to-images/convert_slides_to_images.py <pdf_path> <presentation_folder>/outputs/slide_images
```

Skip if `<presentation_folder>/outputs/slide_images/` already contains `slide_*.png` files.

### Step 3: Extract transcript

- If **Transcript** is specified in presentation.md, read from that path (relative to presentation folder).
- If `<presentation_folder>/outputs/transcript.txt` exists, use the cached version.
- Otherwise, extract from YouTube:
  ```bash
  uv run .agents/skills/extract-transcript/extract_transcript.py <youtube_url> <presentation_folder>/outputs/transcript.txt
  ```

### Step 4: Generate video chapters

If `<presentation_folder>/outputs/chapters.txt` exists, use the cached version. Otherwise:

1. Read the transcript from Step 3.
2. Write a brief summary paragraph (2-3 sentences) describing what the video is about.
3. Create a list of timestamped chapters in "MM:SS - Chapter Title" format covering the main topics.
4. Save to `<presentation_folder>/outputs/chapters.txt`.

### Step 5: Extract slide text

Extract the text content of each PDF page to provide ground truth for what each slide actually says. This prevents misidentifying embedded screenshots or demo captures as actual slide content.

```bash
uv run .agents/skills/extract-slide-text/extract_slide_text.py <pdf_path> <presentation_folder>/outputs/slide_ascii.md <presentation_folder>/outputs/slide_images
```

Skip if `<presentation_folder>/outputs/slide_ascii.md` already exists.

### Step 6: Outline slides

If `<presentation_folder>/outputs/outline.txt` exists, use the cached version. Otherwise:

1. Find all `slide_*.png` files in `<presentation_folder>/outputs/slide_images/`, sorted numerically.
2. Read `<presentation_folder>/outputs/slide_ascii.md` (from Step 5) as ground truth for each slide's text content.
3. Look at each slide image and write a one-sentence summary. Base the summary primarily on the extracted text from slide_ascii.md, using the image only for visual context (diagrams, layout, screenshots).
4. For large presentations (50+ slides), work in batches of 50.
5. Save to `<presentation_folder>/outputs/outline.txt`.

### Step 7: Generate the annotated write-up

Gather all context, then generate the write-up following the rules below.

**Context to gather:**
- `TRANSCRIPT` — Full transcript text (Step 3)
- `VIDEO_CHAPTERS` — Chapter summary (Step 4)
- `SLIDE_TEXT` — Extracted text per slide from `slide_ascii.md` (Step 5). Use as ground truth for what each slide contains.
- `SLIDE_OUTLINE` — Numbered slide outline (Step 6)
- `VIDEO_SOURCE` — YouTube URL or MP4 path from presentation.md
- `IS_LOCAL_VIDEO` — true if VIDEO_SOURCE is a local MP4 file
- `SLIDES_HTML_CONTENT` — Contents of `slides_content.md` if it exists (RevealJS only)
- Check if SLIDES_HTML_CONTENT contains "SECTION HEADING" markers → `HAS_SECTION_HEADINGS`

**Write-up generation prompt:**

Create an annotated blog post that explains the content of each slide.

STRUCTURE REQUIREMENTS:
1. Start with a level-1 heading (#) containing the talk title.
2. Follow with an overview paragraph introducing the talk.
3. Do NOT include a table of contents — it will be generated automatically.

If HAS_SECTION_HEADINGS is true (RevealJS slides with section markers):
- Use level-2 headings (##) for SECTION HEADING slides — these are section dividers.
- Use level-3 headings (###) for regular slides within each section.

If HAS_SECTION_HEADINGS is false:
- Use level-2 headings (##) with a descriptive title for each slide's content.

For each slide section, include:
- The heading
- The slide image reference immediately after the heading: `![Alt text](slide_images/slide_N.png)`
- A timestamp link to the video (or `[MM:SS]` for local MP4s)
- The explanatory text

End with a `## Q&A` section containing questions and answers, each question as a level-3 heading (###).

HEADING CAPITALIZATION: Capitalize the first letter like a normal sentence. Only capitalize proper nouns and acronyms elsewhere.
- CORRECT: "Hybrid search combines keyword and vector retrieval"
- WRONG: "Hybrid Search Combines Keyword And Vector Retrieval" (title case)

Example structure:

```markdown
# Building intelligent agents with RAG

This talk introduces techniques for building AI agents...

## Hybrid search combines multiple retrieval methods

![Diagram showing hybrid search architecture](slide_images/slide_8.png)
[Watch from 04:12](https://www.youtube.com/watch?v=VIDEO_ID&t=252s)

Hybrid search combines keyword search and vector search...

## Q&A

### How do I configure specific indexes as knowledge sources?

Answer text here...
```

WRITING GUIDELINES:
1. Write like speaker notes: state the actual information and explain how things work. Do NOT describe or analyze the talk from the outside.
2. Never narrate what speakers, slides, or the talk itself did. Forbidden patterns include "The speaker explains...", "This slide shows...", "The talk demonstrates...", "This section marks the shift to...", "The diagram illustrates...". Instead, just state the content directly.
3. Make every sentence information-dense without repetition.
4. Provide enough detail per slide that a reader does not need to watch the video.
5. Capture supplementary information from the talk that is NOT visible on the slides.
6. Use short words, fewer words. Get to the point.
7. Avoid multiple examples if one suffices. Cut transitional fluff.
8. Prefer flowing prose over bullet points.
9. Use simple language. No emojis. No hedge words unless exceptions matter.
10. Include relevant links from the slides where appropriate.
11. For YouTube videos, create timestamped links: `[Watch from MM:SS](VIDEO_SOURCE&t=SECONDSs)`
12. For local MP4 files, just provide timestamps in `[MM:SS]` format.
13. Reference slides as `slide_images/slide_1.png`, `slide_images/slide_2.png`, etc.

If SLIDES_HTML_CONTENT exists, use it to find URLs that should be included in the writeup.

### Step 8: Insert table of contents

After generating the write-up:

1. Find all `## ` headings in the generated markdown.
2. For each heading, create an anchor link:
   - Convert to lowercase
   - Remove special characters (keep alphanumeric, spaces, hyphens)
   - Replace spaces with hyphens
   - Collapse multiple hyphens
3. Build a TOC:
   ```markdown
   ## Table of contents

   - [Heading text](#anchor-link)
   - [Another heading](#another-heading)
   ```
4. Insert the TOC before the first `## ` heading (after the `# ` title and intro paragraph).

### Step 9: Save output

Save the final write-up to `<presentation_folder>/outputs/writeup.md`.

## Output structure

```
<presentation_folder>/
├── presentation.md
└── outputs/
    ├── writeup.md           ← Final output
    ├── transcript.txt       ← Cached transcript
    ├── chapters.txt         ← Cached video chapters
    ├── slide_ascii.md       ← Extracted text per slide
    ├── outline.txt          ← Cached slide outline
    ├── slides_content.md    ← RevealJS extracted content (if applicable)
    └── slide_images/
        ├── slide_1.png
        ├── slide_2.png
        └── ...
```
