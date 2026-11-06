---
name: youtube-description
description: Generate a YouTube description with a brief intro, relevant links, and clickable timestamps for each question.
---

# Generating the YouTube description

When asked to generate a YouTube description, create a `youtube_description.md` with:

1. A brief intro line
2. A link to any relevant materials for the video
3. Timestamps for each question (YouTube auto-links timestamps that appear at the start of a line in `MM:SS` or `H:MM:SS` format)

For example:

```text
Weekly Python + AI office hours - January 6, 2026

This is just a recording from the Discord office hours, for those who couldn't attend live.
Join the live weekly OH here: http://aka.ms/pythonai/oh

See a write-up of each weekly office hours here:
https://aka.ms/pythonai/oh/links

Timestamps:
0:00 Intro
5:48 How do you set up Entra OBO flow for Python MCP servers?
20:24 Which MCP inspector should I use for testing servers with Entra authentication?
28:04 How do you track LLM usage tokens and costs?
30:32 How do you keep yourself updated with all the new changes related to AI?
36:30 How do you build a Microsoft Copilot agent in Python?
46:39 How do I learn about AI from scratch as a backend developer?
49:50 What's new with the RAG demo after SharePoint was added?
53:53 Will companies create internal MCP servers?
```

Note: YouTube automatically makes timestamps clickable when they appear at the start of a line. Do not include the `📹` emoji or markdown links in the YouTube description.
