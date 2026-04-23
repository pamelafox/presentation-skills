# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Capture frames from a YouTube video at a regular interval.

Downloads the video with yt-dlp, then extracts frames with ffmpeg.
Produces PNG images and a frames_manifest.md mapping filenames to timestamps.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from a URL."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([^&?/]+)",
        r"(?:embed/)([^&?/]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def format_timestamp(seconds: int) -> str:
    """Format seconds as [MM:SS] or [HH:MM:SS]."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
    return f"[{minutes:02d}:{secs:02d}]"


def download_video(url: str, output_path: str) -> None:
    """Download a YouTube video using yt-dlp."""
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_path,
        url,
    ]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(
            "yt-dlp not found. Install it:\n"
            "  macOS: brew install yt-dlp\n"
            "  pip: pip install yt-dlp",
            file=sys.stderr,
        )
        sys.exit(1)


def extract_frames(video_path: str, output_dir: Path, interval: int) -> list[tuple[str, int]]:
    """Extract frames from video at the given interval.

    Returns a list of (filename, timestamp_seconds) tuples.
    """
    duration = get_video_duration(video_path)
    frames: list[tuple[str, int]] = []

    for t in range(0, int(duration), interval):
        filename = f"frame_{t:04d}.png"
        output_file = output_dir / filename
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(t),
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            str(output_file),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except FileNotFoundError:
            print(
                "ffmpeg not found. Install it:\n"
                "  macOS: brew install ffmpeg\n"
                "  Ubuntu: apt-get install ffmpeg",
                file=sys.stderr,
            )
            sys.exit(1)

        if output_file.exists():
            frames.append((filename, t))

    return frames


def write_manifest(frames: list[tuple[str, int]], output_dir: Path) -> Path:
    """Write frames_manifest.md with filenames, timestamps, and empty descriptions."""
    manifest_path = output_dir / "frames_manifest.md"
    lines = ["| File | Timestamp | Description |", "|------|-----------|-------------|"]
    for filename, seconds in frames:
        timestamp = format_timestamp(seconds)
        lines.append(f"| {filename} | {timestamp} | |")
    manifest_path.write_text("\n".join(lines) + "\n")
    return manifest_path


def main() -> None:
    """Download a YouTube video and capture frames at a regular interval."""
    parser = argparse.ArgumentParser(description="Capture frames from a YouTube video")
    parser.add_argument("youtube_url", help="YouTube video URL")
    parser.add_argument("output_dir", help="Directory to save frames and manifest")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between captured frames (default: 30)",
    )
    args = parser.parse_args()

    # Validate URL
    extract_video_id(args.youtube_url)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download video to a temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = str(Path(tmpdir) / "video.mp4")
        print(f"Downloading video from {args.youtube_url}...")
        download_video(args.youtube_url, video_path)

        print(f"Extracting frames every {args.interval} seconds...")
        frames = extract_frames(video_path, output_dir, args.interval)

    manifest_path = write_manifest(frames, output_dir)
    print(f"Captured {len(frames)} frames in {output_dir}")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
