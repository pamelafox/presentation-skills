---
name: capture-video-frames
description: >-
  Capture frames from a YouTube video at a regular interval, produce a manifest
  mapping filenames to timestamps, and describe each frame with an LLM.
  USE FOR: extract video frames, capture screenshots from YouTube, describe video frames,
  video frame analysis, frame-by-frame summary.
argument-hint: <youtube_url> <output_dir> [--interval SECONDS]
---

# Capture and describe video frames

## Step 1: Capture frames

Run the [capture_video_frames.py](./capture_video_frames.py) script:

```bash
uv run .agents/skills/capture-video-frames/capture_video_frames.py <youtube_url> <output_dir> [--interval SECONDS]
```

### Arguments

- `youtube_url` (required): YouTube video URL (same formats accepted by the extract-transcript skill).
- `output_dir` (required): Directory to save frames and the manifest file. Created if it doesn't exist.
- `--interval` (optional): Seconds between captured frames. Defaults to **30**.

### Outputs

- **frame_0000.png**, **frame_0030.png**, … — PNG images named by their timestamp in seconds (zero-padded to 4 digits).
- **frames_manifest.md** — A markdown file listing each frame with its timestamp and a placeholder for descriptions.

Example **frames_manifest.md**:

```
| File | Timestamp | Description |
|------|-----------|-------------|
| frame_0000.png | [00:00] | |
| frame_0030.png | [00:30] | |
| frame_0060.png | [01:00] | |
```

### Prerequisites

- **yt-dlp**: `brew install yt-dlp` or `pip install yt-dlp`
- **ffmpeg**: `brew install ffmpeg` or `apt-get install ffmpeg`

## Step 2: Describe frames using the `describe-frame` subagent

After capturing frames, describe each frame by running the **describe-frame** custom agent as a subagent. Each subagent invocation gets an isolated context, so frame images won't accumulate and exhaust the context window.

The `describe-frame` agent is defined in `.github/agents/describe-frame.md`.

### Procedure

1. Read **frames_manifest.md** from the output directory to get the full list of frames.
2. For each frame, run the `describe-frame` agent as a subagent with a prompt that includes:
   - The **absolute path** to the current frame image to view.
   - The **absolute path** to the previous frame image to view (if one exists).
   - The **previous frame's description** as text (if one exists).
3. The subagent will return a plain-text description (or `(same as previous)` if the frame is essentially identical to the previous one).
4. After each subagent returns, update the Description column for that row in **frames_manifest.md** immediately.
5. Continue until all frames are described.

### Subagent prompt template

Use this as the prompt when invoking the `describe-frame` subagent (fill in the bracketed values):

```
Describe the current frame image at: [CURRENT_FRAME_ABSOLUTE_PATH]

[If previous frame exists, include these two lines:]
The previous frame image is at: [PREVIOUS_FRAME_ABSOLUTE_PATH]
The previous frame was described as: "[PREVIOUS_DESCRIPTION]"
```

### Example output

After describing all frames, **frames_manifest.md** should look like:

```
| File | Timestamp | Description |
|------|-----------|-------------|
| frame_0000.png | [00:00] | Title slide introducing "Building RAG apps with Python" |
| frame_0030.png | [00:30] | Speaker showing the agenda with four main topics |
| frame_0060.png | [01:00] | (same as previous) |
| frame_0090.png | [01:30] | Architecture diagram of a retrieval-augmented generation pipeline |
```

## Step 3: Deduplicate frames and select best speaker faces

After all frames are described, groups of consecutive `(same as previous)` rows represent the same visual content captured at different moments. Within each group, speaker faces may differ — eyes open vs closed, mouth open vs closed, facing camera vs turned away.

### Goal

For each group of duplicate frames, keep only **one** frame — the one with the best speaker face quality — and remove the rest.

### Criteria for best face (in priority order)

1. **The current speaker's mouth should be open** (mid-speech). If you know who is speaking at that timestamp (from a transcript), prioritize that speaker.
2. **Eyes open** — no mid-blink frames.
3. **Facing camera** — not turned sideways or looking down.
4. If no speakers are visible (e.g., full-screen demo or slide without webcam feeds), all frames in the group are equivalent — keep the first one.

### Procedure

1. Identify all groups of consecutive rows where the description is `(same as previous)`. Each group starts with the "anchor" frame (the one with an actual description) followed by one or more `(same as previous)` rows.
2. For each group, run the `describe-frame` subagent to compare faces across the anchor frame and each duplicate. Use this prompt template:

```
Compare these two frames focusing ONLY on the speaker faces visible in webcam feeds. Which frame has better speaker faces — eyes open, facing camera, mouth open (mid-speech), not mid-blink or turned away?

Frame A: [ANCHOR_FRAME_ABSOLUTE_PATH]
Frame B: [DUPLICATE_FRAME_ABSOLUTE_PATH]

Reply with ONLY one of:
- "A BETTER" if the anchor frame has better speaker faces
- "B BETTER" if the duplicate frame has better speaker faces
- "EQUAL" if both are equivalent
- "NO SPEAKERS" if no speaker faces are visible in either frame

Then add a brief reason.
```

3. After comparing all duplicates in a group against the anchor (and the current best), determine the single best frame.
4. If the best frame is NOT the anchor:
   - Move the anchor's description to the best frame's row.
   - Add a face-quality note to the description, e.g., `(better speaker faces than frame_XXXX: eyes open, facing camera)`
5. Remove all other `(same as previous)` rows from the manifest.
6. If the anchor was already the best, just remove the duplicate rows.

### Recapturing frames for closed mouths

After deduplication, if the best frame in a group still has the speaking person's mouth closed (both speakers have mouths closed), try recapturing at nearby timestamps:

1. Download the video if not already available:
   ```bash
   yt-dlp -f "bestvideo[height<=720]" --no-playlist -o "<output_dir>/video.%(ext)s" "<youtube_url>"
   ```
2. Capture alternative frames at +2s, +5s, +8s, and +10s offsets from the frame's timestamp:
   ```bash
   ffmpeg -ss <SECONDS> -i <output_dir>/video.mp4 -frames:v 1 -q:v 2 <output_dir>/alt_<FRAME>_<SECONDS>.png -y
   ```
3. Use the `describe-frame` subagent to check if the speaker's mouth is open in any alternative, AND that the slide/demo content is still the same.
4. If a better alternative is found, replace the frame file (`cp alt_XXXX.png frame_XXXX.png`).
5. Clean up: `rm -f <output_dir>/alt_*.png <output_dir>/video.mp4`
