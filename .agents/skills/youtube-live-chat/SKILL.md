---
name: youtube-live-chat
description: >-
  Download live chat transcripts from YouTube videos.
  Use when the user asks for live chat, chat messages, or chat replay from a YouTube video
  and provides a YouTube URL (youtube.com/watch?v=, youtu.be/, or similar).
  Works with live streams and past streams that have chat replay enabled.
---

# YouTube Live Chat Downloader

Download live chat messages from YouTube videos using yt-dlp.

## Usage

Run the script with a YouTube URL or video ID:

```bash
uv run .agents/skills/youtube-live-chat/get_live_chat.py "VIDEO_URL_OR_ID"
```

With timestamps:

```bash
uv run .agents/skills/youtube-live-chat/get_live_chat.py "VIDEO_URL_OR_ID" --timestamps
```

Output to a specific file:

```bash
uv run .agents/skills/youtube-live-chat/get_live_chat.py "VIDEO_URL_OR_ID" --output chat.txt
```

## Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://www.youtube.com/live/VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/embed/VIDEO_ID`
- Raw video ID (11 characters)

## Output Format

- **Without timestamps** (default): `[author]: message` format
- **With timestamps**: `[HH:MM:SS] [author]: message` format

## Output

- If you were asked to save the chat to a specific file, save it to the requested file.
- If no output file was specified, use the YouTube video ID with a `-livechat.txt` suffix.

## Notes

- Works with live streams currently in progress
- Works with past streams that have chat replay enabled
- Some videos may not have live chat available
- Super chats and memberships are included with their message text
