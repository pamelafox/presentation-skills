# 📋 Recap My Week Skill

An agent skill that summarizes your last week of work — pulling highlights from your GitHub activity, X/Twitter posts, and Microsoft 365 work data.

Every highlight is grounded in real data: your commits, your meetings, your posts. No fluff. The best recaps come from combining what you shipped, what you discussed, and what you shared publicly.

## How it works

When you ask your coding agent to "recap my week," the skill:

1. **Gathers activity data** from three sources in parallel:
   - **GitHub** — PRs merged, issues closed, repos contributed to
   - **X (Twitter)** — posts, engagement, trends followed
   - **WorkIQ (Microsoft 365)** — meetings attended, emails sent, files edited
2. **Identifies top highlights** — the most meaningful accomplishments and contributions
3. **Delivers a structured recap** — top highlights, code summary, work summary, social summary, and a stats box

## Installation

Install the skill using the [`skills`](https://www.npmjs.com/package/skills) CLI:

```sh
npx skills add pamelafox/recap-my-week
```

## Required MCP Servers

This skill queries three MCP servers for activity data. You'll need to have them connected to your agent:

| Source | MCP Server | What It Provides |
|--------|-----------|-----------------|
| GitHub | [github/github-mcp-server](https://github.com/github/github-mcp-server) | Commits, PRs, issues |
| X (Twitter) | [xdevplatform/xmcp](https://github.com/xdevplatform/xmcp) | Posts, likes, trends |
| Work IQ (Microsoft 365) | [microsoft/work-iq](https://github.com/microsoft/work-iq) | Emails, meetings, files |

> **Note:** The skill gracefully handles missing sources. If a server isn't connected, it notes the gap and summarizes what's available.

## Usage

Once installed, just ask your coding agent:

- "recap my week"
- "what did I do this week"
- "weekly summary"

## Example

> **🏆 Top Highlights**
> - Merged the new auth module PR across 2 repos
> - Led the architecture review meeting with 6 participants
> - Published a thread on API design that got 120 likes
>
> **📊 By the Numbers:** 4 PRs merged · 7 issues closed · 12 meetings · 23 emails sent · 3 posts published
