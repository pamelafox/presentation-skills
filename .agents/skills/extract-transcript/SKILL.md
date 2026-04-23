---
name: extract-transcript
description: >-
  Extract a timestamped transcript from a YouTube video.
  Returns text with [MM:SS] or [HH:MM:SS] timestamps for each segment.
  USE FOR: get transcript, transcribe YouTube video, fetch video transcript, YouTube captions.
argument-hint: <youtube_url> [output_file]
---

# Extract transcript from YouTube video

Run the [extract_transcript.py](./extract_transcript.py) script to fetch a timestamped transcript:

```bash
uv run .agents/skills/extract-transcript/extract_transcript.py <youtube_url> [output_file]
```

## Arguments

- `youtube_url` (required): YouTube video URL. Supported formats:
  - `https://www.youtube.com/watch?v=VIDEO_ID`
  - `https://youtu.be/VIDEO_ID`
  - `https://www.youtube.com/embed/VIDEO_ID`
- `output_file` (optional): Path to save the transcript. If omitted, prints to stdout.

## Output format

Each line has a timestamp followed by the transcript text:

```
[00:00] Welcome to this talk about...
[00:15] Today we'll be covering...
[01:30] Let's start with the first topic...
```

Timestamps use `[MM:SS]` format for videos under an hour, `[HH:MM:SS]` for longer videos.
