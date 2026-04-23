---
name: outline-slides
description: >-
  Generate a numbered outline of presentation slides with one-sentence summaries.
  Looks at each slide image and produces a brief description.
  USE FOR: summarize slides, outline presentation, describe slide images, create slide summary.
---

# Outline slides

Generate a numbered outline of all slides with one-sentence summaries per slide.

## Input

- A directory containing slide images named **slide_1.png**, **slide_2.png**, etc. (produced by the convert-slides-to-images skill).
- Optionally, a **slide_ascii.md** file containing extracted text per slide (produced by the extract-slide-text skill).

## Procedure

1. Find all **slide_*.png** files in the specified directory, sorted numerically by slide number.
2. If **slide_ascii.md** is available, read it and use the extracted text as ground truth for each slide's content. This prevents misidentifying embedded screenshots or demo captures as actual slide content.
3. Look at each slide image and write a one-sentence summary describing the content of that slide. When slide_ascii.md is available, base the summary primarily on the extracted text, using the image only for visual context (diagrams, screenshots, etc.).
4. Output a numbered list matching the slide numbers.

For large presentations (more than 50 slides), work through the slides in batches of 50.

## Output format

```
1. Title slide introducing the presentation on [topic]
2. Agenda slide listing the main sections to be covered
3. Diagram showing the architecture of [system]
4. Code example demonstrating [technique]
...
```

## Example usage

To outline slides that have already been converted to images:

```
Please outline the slides in presentations/my-talk/outputs/slide_images/
```

Save the output to **outputs/outline.txt** in the presentation folder for caching.
