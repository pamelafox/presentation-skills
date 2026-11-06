#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build a promo-card config from a Microsoft event speaker page (Ignite, Build, etc.).

Microsoft event sites expose public catalog APIs at /api/session/all/<locale> and
/api/speaker/all/<locale>. This script finds every session the speaker presents,
collapses repeated deliveries into one entry with a list of days, and downloads
headshots for the speaker and co-speakers.

Usage:
    uv run fetch_microsoft_event_speaker.py <speaker_url> <output_dir> [--tz America/Los_Angeles]
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

UA = {"User-Agent": "Mozilla/5.0 (speaker-promo-cards)"}


def get_json(url):
    with urlopen(Request(url, headers=UA), timeout=60) as resp:
        return json.load(resp)


def parse_listish(value):
    """Catalog fields are sometimes Python-repr strings like "['a', 'b']"."""
    if isinstance(value, list):
        return value
    if not value:
        return []
    return re.findall(r"'([^']+)'", str(value))


def display_value(value):
    if isinstance(value, dict):
        return value.get("displayValue", "")
    m = re.search(r"'displayValue': '([^']*)'", str(value))
    return m.group(1) if m else ""


def format_dates(days):
    """Sorted unique dates -> ("Tue, Nov 17 · Wed, Nov 18", "Nov 17 & 18")."""
    long = " · ".join(f"{d:%a}, {d:%b} {d.day}" for d in days)
    if len(days) == 1:
        return long, None
    if len({d.month for d in days}) == 1:
        nums = [str(d.day) for d in days]
        short = f"{days[0]:%b} " + ", ".join(nums[:-1]) + " & " + nums[-1]
    else:
        short = " & ".join(f"{d:%b} {d.day}" for d in days)
    return long, short


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("speaker_url", help="Speaker page URL, e.g. https://ignite.microsoft.com/en-US/speakers/<id>")
    parser.add_argument("output_dir", help="Directory for config.json and headshots/")
    parser.add_argument("--tz", default="America/Los_Angeles", help="Event time zone for computing session days")
    args = parser.parse_args()

    url = urlparse(args.speaker_url)
    m = re.search(r"/([a-z]{2}-[A-Z]{2})/speakers/([^/?#]+)", url.path)
    if not m:
        sys.exit("Could not find /<locale>/speakers/<id> in the URL")
    locale, speaker_id = m.groups()
    base = f"{url.scheme}://{url.netloc}"
    tz = ZoneInfo(args.tz)

    print(f"Fetching catalog from {base} ...", file=sys.stderr)
    sessions = get_json(f"{base}/api/session/all/{locale}")
    speakers = {s["speakerId"]: s for s in get_json(f"{base}/api/speaker/all/{locale}")}
    if speaker_id not in speakers:
        sys.exit(f"Speaker {speaker_id} not found in catalog")

    out = Path(args.output_dir)
    (out / "headshots").mkdir(parents=True, exist_ok=True)

    keys = {}
    people = {}

    def person_key(sid):
        if sid in keys:
            return keys[sid]
        sp = speakers.get(sid, {})
        key = re.sub(r"[^a-z]", "", (sp.get("firstName") or "speaker").lower()) or "speaker"
        while key in people:
            key += "x"
        keys[sid] = key
        photo = sp.get("photo") or ""
        local = ""
        if photo.startswith("http"):
            ext = ".png" if ".png" in photo.lower() else ".jpg"
            local = f"headshots/{key}{ext}"
            try:
                with urlopen(Request(photo, headers=UA), timeout=60) as resp:
                    (out / local).write_bytes(resp.read())
            except OSError as e:  # keep going; the card falls back to initials
                print(f"  ! could not download photo for {key}: {e}", file=sys.stderr)
                local = ""
        title = sp.get("jobTitle") or ""
        if sp.get("company") and sp["company"] not in title:
            title = f"{title}, {sp['company']}" if title else sp["company"]
        name = sp.get("displayName") or f"{sp.get('firstName', '')} {sp.get('lastName', '')}".strip()
        people[key] = {"name": name, "title": title, "photo": local}
        return key

    owner = person_key(speaker_id)

    grouped = {}
    for s in sessions:
        ids = parse_listish(s.get("speakerIds"))
        if speaker_id not in ids:
            continue
        code = s.get("sessionCode") or s.get("sessionId")
        g = grouped.setdefault(code, {"session": s, "ids": ids, "starts": []})
        if s.get("startDateTime"):
            g["starts"].append(datetime.fromisoformat(s["startDateTime"]).astimezone(tz))

    def first_start(item):
        starts = item[1]["starts"]
        return min(starts).timestamp() if starts else float("inf")

    out_sessions = []
    for code, g in sorted(grouped.items(), key=first_start):
        s = g["session"]
        days = sorted({d.date() for d in g["starts"]})
        entry = {
            "code": code,
            "type": display_value(s.get("sessionType")),
            "title": s.get("title", ""),
            "speakers": [owner] + [person_key(i) for i in g["ids"] if i != speaker_id],
        }
        if days:
            entry["dates"], short = format_dates(days)
            if short:
                entry["short_dates"] = short
        # Reference only (cards don't show times); useful for double-checking with the speaker
        entry["deliveries"] = [f"{d:%a %b %d %I:%M %p}" for d in sorted(g["starts"])]
        out_sessions.append(entry)

    event_name = {"ignite": "Microsoft Ignite", "build": "Microsoft Build"}.get(url.netloc.split(".")[0], url.netloc)
    config = {
        "event": event_name,
        "owner": owner,
        "footer": f"Find session times at {url.netloc}",
        "people": people,
        "sessions": out_sessions,
    }
    (out / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out / 'config.json'} with {len(out_sessions)} session(s) for {people[owner]['name']}", file=sys.stderr)
    for e in out_sessions:
        print(f"  {e['code']}: {e['title']} [{e.get('dates', 'no date')}]", file=sys.stderr)


if __name__ == "__main__":
    main()
