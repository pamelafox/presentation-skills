# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "youtube-transcript-api",
# ]
# ///
"""Extract a timestamped transcript from a YouTube video."""

import re
import sys

from youtube_transcript_api import YouTubeTranscriptApi


def transcribe(url: str) -> str:
    """Get transcript from YouTube URL with timestamps."""
    video_id = None
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([^&?/]+)",
        r"(?:embed/)([^&?/]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break

    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id)

    lines = []
    for snippet in transcript:
        start = int(snippet.start)
        hours, remainder = divmod(start, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
        else:
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
        lines.append(f"{timestamp} {snippet.text}")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run extract_transcript.py <youtube_url> [output_file]")
        sys.exit(1)

    url = sys.argv[1]
    result = transcribe(url)

    if len(sys.argv) >= 3:
        from pathlib import Path

        output_path = Path(sys.argv[2])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result)
        print(f"Transcript saved to: {output_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
