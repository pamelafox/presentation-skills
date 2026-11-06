#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["yt-dlp>=2024.0.0"]
# ///
"""
Download live chat from a YouTube video.

Usage:
    uv run get_live_chat.py <video_id_or_url> [--timestamps] [--output FILE]
"""

import sys
import json
import tempfile
import argparse
from pathlib import Path
from yt_dlp import YoutubeDL


def format_timestamp(ms: int) -> str:
    """Convert milliseconds to HH:MM:SS format."""
    if ms is None or ms < 0:
        return "00:00:00"
    seconds = ms // 1000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_chat_json(json_path: Path, with_timestamps: bool = False) -> str:
    """Parse the live chat JSON file from yt-dlp."""
    lines = []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # Navigate to the chat item
            replay_action = data.get('replayChatItemAction', {})
            actions = replay_action.get('actions', [])
            offset_ms = int(replay_action.get('videoOffsetTimeMsec', 0))
            
            for action in actions:
                add_action = action.get('addChatItemAction', {})
                item = add_action.get('item', {})
                
                # Handle regular text messages
                renderer = item.get('liveChatTextMessageRenderer')
                if renderer:
                    author = renderer.get('authorName', {}).get('simpleText', 'Unknown')
                    message_runs = renderer.get('message', {}).get('runs', [])
                    text = ''.join(run.get('text', '') for run in message_runs)
                    
                    if text:
                        if with_timestamps:
                            timestamp = format_timestamp(offset_ms)
                            lines.append(f"[{timestamp}] [{author}]: {text}")
                        else:
                            lines.append(f"[{author}]: {text}")
    
    return '\n'.join(lines)


def get_live_chat(video_url: str, with_timestamps: bool = False) -> str:
    """Fetch and format live chat for a YouTube video using yt-dlp."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = str(Path(tmpdir) / 'chat')
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'subtitleslangs': ['live_chat'],
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Find the downloaded chat file
        chat_file = Path(tmpdir) / 'chat.live_chat.json'
        if not chat_file.exists():
            raise ValueError("No live chat available for this video")
        
        return parse_chat_json(chat_file, with_timestamps)


def main():
    parser = argparse.ArgumentParser(description='Download YouTube live chat')
    parser.add_argument('video', help='YouTube video URL or video ID')
    parser.add_argument('--timestamps', '-t', action='store_true', 
                        help='Include timestamps in output')
    parser.add_argument('--output', '-o', help='Output file path')
    args = parser.parse_args()
    
    try:
        # yt-dlp handles all URL formats directly
        video_url = args.video
        if not video_url.startswith('http'):
            video_url = f"https://www.youtube.com/watch?v={args.video}"
        
        chat = get_live_chat(video_url, with_timestamps=args.timestamps)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(chat)
            print(f"Chat saved to {args.output}", file=sys.stderr)
        else:
            print(chat)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
