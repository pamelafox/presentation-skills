---
name: make-speaker-promo-cards
description: >-
  Create social media promo graphics (LinkedIn, X, Bluesky) for speakers at Microsoft events
  (Microsoft Ignite, Microsoft Build), listing every session a speaker is giving with the day(s)
  and small co-speaker headshots. Pulls sessions, co-speakers, and headshots from the event's
  speaker page (e.g. ignite.microsoft.com/en-US/speakers/<id>).
  USE FOR: Ignite/Build speaker card, session promo graphic, "join me at Microsoft Ignite" image,
  LinkedIn/Twitter graphic for my Microsoft event talks, promo for co-speakers.
argument-hint: <Microsoft event speaker page URL> [extra sessions]
---

# Make speaker promo cards for Microsoft events

Generate PNG promo cards for Microsoft events (Ignite, Build) that show **all** of a speaker's sessions, not just one.
Each session shows its code, type, title, day(s), and the co-speakers' headshots.

## Workflow

### 1. Gather the session data

Run the fetcher on the speaker's Microsoft event page (e.g. `https://ignite.microsoft.com/en-US/speakers/<id>`).
It calls the site's public catalog APIs, groups repeated deliveries of the same session code, works out the day(s) in the event's time zone, and downloads headshots.

```bash
uv run skills/make-speaker-promo-cards/scripts/fetch_microsoft_event_speaker.py "<speaker_url>" <work_dir> [--tz America/Los_Angeles]
```

This writes `<work_dir>/config.json` and `<work_dir>/headshots/`.

If the fetcher fails, for example because the catalog API changed or the session isn't published yet, write `config.json` by hand. Use [assets/example_config.json](./assets/example_config.json) as the template.

### 2. Confirm the session list with the speaker

Public catalogs are often incomplete, so show the speaker the sessions you found and ask whether anything is missing. Common gaps:

- Pre-day workshops and partner-only sessions that aren't in the main catalog.
- Labs where the speaker is a proctor rather than a listed presenter. Add these with `"proctors": ["<key>"]` and keep the presenters in `speakers`.
- Extra deliveries of a repeated lab that are only on the speaker's calendar.
- Session codes that differ from what the speaker remembers (e.g. ILL667 vs LAB667). Search the catalog by title or session ID from a session URL.

Edit `config.json` to add the missing sessions or dates, and ask for missing co-speakers' names.

### 3. Render

```bash
uv run skills/make-speaker-promo-cards/scripts/make_promo_cards.py <work_dir>/config.json <out_dir> [--owner KEY] [--style tiles list landscape compact]
```

Output files are named `<owner>_<style>.png`. Each image's height is trimmed to fit its content.

| Style | Size | Best for |
|-------|------|----------|
| `tiles` | 1080 wide, portrait | LinkedIn. Big headshot and header; sessions in a 2-column grid. With an odd number of sessions, the first spans the full width. |
| `list` | 1080 wide, portrait | LinkedIn. One row per session with co-speaker headshots on the right. Set `subheadline` for a second header line. |
| `landscape` | 1200 wide, short | LinkedIn or blog banners. Headshot panel on the left, one column per session. |
| `compact` | 960 wide, short | X, Bluesky, Mastodon. Plain black background, emoji type labels, and paired headshots with first names on each card. |

To make cards for a co-speaker, re-run with `--owner <their key>`. It shows only that person's sessions, so first fetch their own speaker page or add their other sessions to the config.

### 4. Review and iterate

View every PNG before sharing it. Check for clipped text, awkward line breaks, and empty space. Adjust the config, such as shorter `short_dates`, a different `accent`, or `announce` text, then re-render.

## Config format

```jsonc
{
  "event": "Microsoft Ignite",            // used in the default headline
  "headline": "Join me at Microsoft Ignite", // optional
  "subheadline": "",                       // optional second header line (list style)
  "footer": "Find session times at ignite.microsoft.com", // optional; "" to omit
  "accent": "#C03BC4",                     // header and tag color
  "background_image": "",                  // optional image path, relative to config
  "announce": "",                          // optional banner, e.g. "Announcing the FY27 OpenHack!"
  "owner": "pamela",                       // default --owner
  "people": {
    "pamela": {"name": "Pamela Fox", "title": "Principal Cloud Advocate, Microsoft", "photo": "headshots/pamela.jpg"}
  },
  "sessions": [
    {
      "code": "LAB673",
      "type": "Lab",
      "title": "Turning data into agent-ready knowledge with Foundry IQ",
      "dates": "Tue, Nov 17 · Wed, Nov 18 · Fri, Nov 20",
      "short_dates": "Nov 17, 18 & 20",  // optional; used by narrow styles
      "speakers": ["pamela", "ayca"],      // presenters
      "proctors": []                       // optional; makes the session appear on proctors' cards
    }
  ]
}
```

`photo` can be a path relative to the config file or an `https://` URL. If it's missing, the card shows the person's initials.

## Design guidance (learned from user feedback)

- **Show days, not times or rooms.** Labs and repeated sessions run several times, so times clutter the card and go stale. Put the day(s) under each title and point to the catalog in the footer.
- **Show every session.** Single-session templates under-sell a speaker with several sessions.
- **Keep co-speaker headshots small**, and show co-speakers on every session they share.
- **Style every session the same.** Don't highlight one session with a special color unless the user asks.
- **Trim empty space.** Size cards to their content, not a fixed canvas.
- **For X/Bluesky, keep it casual.** Use the `compact` style: no corporate header or slogan, just the sessions on black. The post text carries the "join me" message.
- Don't reuse an event's brand template art unless the user supplies it. Pass it as `background_image`.

## Writing the post text

After rendering, offer a plain-text session list for the post. LinkedIn doesn't render markdown, so use emoji bullets:

```text
🛠️ PREL42 · Pre-day Workshop (Mon, Nov 16)
Build with Microsoft IQ: A hands-on workshop for context-aware AI, with Ayca Bas
```

Suggest @-mentioning co-speakers and linking the speaker page.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) to run the scripts (Python 3.11+). Dependencies are declared inline.
- Playwright Chromium: `uv run --with playwright playwright install chromium`
- Internet access to load the Noto Sans web font. Rendering falls back to system fonts if offline.
