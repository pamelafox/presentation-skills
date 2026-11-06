#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright"]
# ///
"""Render social-media promo cards listing a speaker's conference sessions.

Usage:
    uv run make_promo_cards.py <config.json> <output_dir> [--owner KEY] [--style tiles list landscape compact]

See ../SKILL.md for the config format. Each style is rendered with headless Chromium
and the image height is trimmed to fit the content.
"""

import argparse
import asyncio
import base64
import html
import json
import mimetypes
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from playwright.async_api import async_playwright

STYLES = {
    # name: (width, description)
    "tiles": (1080, "Portrait card: header with headshot, session tiles in a 2-column grid (LinkedIn)"),
    "list": (1080, "Portrait card: header with headshot, one row per session (LinkedIn)"),
    "landscape": (1200, "Wide card: headshot panel on the left, one column per session"),
    "compact": (960, "Minimal black card, one column per session with paired headshots (X/Bluesky)"),
}

EMOJI = [
    ("workshop", "🛠️"),
    ("lab", "🧪"),
    ("table", "💬"),
    ("lightning", "⚡"),
    ("keynote", "🌟"),
    ("breakout", "🎤"),
    ("theater", "🎭"),
    ("demo", "🖥️"),
    ("panel", "🗣️"),
]

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700;800&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body { width: WIDTHpx; font-family: 'Segoe UI', 'Noto Sans', sans-serif; color: #fff;
       overflow: hidden; position: relative; background: BG; }
.bg { position: absolute; inset: 0; background-size: cover; background-position: center; }
.av { border-radius: 50%; object-fit: cover; object-position: center 20%; background: #444; }
.bottom-bar { position: absolute; left: 0; right: 0; bottom: 0; height: 14px;
              background: linear-gradient(90deg, ACCENT, #7B5CF0 45%, #0078D4 75%, #2EC4B6); }
.pill { display: inline-block; background: #fff; border-radius: 14px; font-weight: 700; }
"""

DEFAULT_BG = (
    "radial-gradient(ellipse at 15% 0%, rgba(120,60,220,.45), transparent 55%), "
    "radial-gradient(ellipse at 100% 100%, rgba(0,120,212,.35), transparent 50%), #0b1250"
)


class Card:
    def __init__(self, config, config_dir, owner):
        self.c = config
        self.dir = config_dir
        self.people = config["people"]
        self.owner = owner
        if owner not in self.people:
            sys.exit(f"Owner '{owner}' not in people: {', '.join(self.people)}")
        self.accent = config.get("accent", "#C03BC4")
        self.event = config.get("event", "the conference")
        self.headline = config.get("headline", f"Join me at {self.event}")
        self.footer = config.get("footer", "")
        self.announce = config.get("announce", "")
        self._uris = {}
        self.sessions = []
        for s in config["sessions"]:
            if owner in s.get("speakers", []) or owner in s.get("proctors", []):
                cos = [k for k in s.get("speakers", []) if k != owner]
                self.sessions.append(dict(s, cos=cos))
        if not self.sessions:
            sys.exit(f"No sessions found for '{owner}'")

    # ---------- helpers
    def esc(self, text):
        return html.escape(text or "")

    def photo(self, key):
        if key in self._uris:
            return self._uris[key]
        src = self.people[key].get("photo") or ""
        uri = None
        try:
            if src.startswith("http"):
                with urlopen(Request(src, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                    data, mime = r.read(), r.headers.get_content_type()
            elif src:
                p = (self.dir / src) if not Path(src).is_absolute() else Path(src)
                data, mime = p.read_bytes(), mimetypes.guess_type(p.name)[0] or "image/jpeg"
            else:
                data = None
            if data:
                uri = f"data:{mime};base64,{base64.b64encode(data).decode()}"
        except OSError as e:
            print(f"  ! photo for {key} unavailable ({e}); using initials", file=sys.stderr)
        if not uri:
            initials = "".join(w[0] for w in self.people[key]["name"].split()[:2]).upper()
            svg = (
                f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='#555'/>"
                f"<text x='50' y='62' font-size='38' font-family='sans-serif' fill='#fff' text-anchor='middle'>{initials}</text></svg>"
            )
            uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
        self._uris[key] = uri
        return uri

    def avatar(self, key, size, border="3px solid #fff"):
        return f'<img class="av" src="{self.photo(key)}" style="width:{size}px;height:{size}px;border:{border}">'

    def first(self, key):
        return self.esc(self.people[key]["name"].split()[0])

    def with_line(self, keys, size=46):
        if not keys:
            return ""
        imgs = "".join(self.avatar(k, size, "2px solid #fff") for k in keys)
        names = " &amp; ".join(self.esc(self.people[k]["name"]) for k in keys)
        return f'<div class="with"><span class="pair">{imgs}</span><span>with <b>{names}</b></span></div>'

    def dates(self, s, short=False):
        d = s.get("short_dates") if short and s.get("short_dates") else s.get("dates", "")
        return self.esc(d)

    def emoji(self, type_):
        t = (type_ or "").lower()
        return next((e for k, e in EMOJI if k in t), "📍")

    def page(self, css, body, width, bg=None):
        base = BASE_CSS.replace("WIDTH", str(width)).replace("ACCENT", self.accent).replace("BG", bg or DEFAULT_BG)
        return f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{base}{css}</style></head><body>{body}</body></html>"

    def bg_layer(self):
        img = self.c.get("background_image")
        if not img:
            return ""
        p = self.dir / img
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        uri = f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
        return f'<div class="bg" style="background-image:url({uri})"></div>'

    def foot(self):
        return f'<div class="foot">{self.esc(self.footer)}</div>' if self.footer else ""

    def announce_html(self):
        return f'<div class="announce">📣 {self.esc(self.announce)}</div>' if self.announce else ""

    # ---------- styles
    def tiles(self):
        me, a = self.people[self.owner], self.accent
        ss = self.sessions
        # Odd count: first session spans full width so the grid stays even
        feat, rest = (ss[0], ss[1:]) if len(ss) % 2 else (None, ss)

        def tile(s, cls):
            title = self.esc(s["title"])
            if cls == "feat":
                title = title.replace(": ", ":<br>", 1)
            return f"""<div class="{cls}"><div class="code">{self.esc(s.get("code"))}<span>{self.esc(s.get("type"))}</span></div>
              <div class="title">{title}</div><div class="date">📅 {self.dates(s)}</div>{self.with_line(s["cos"])}</div>"""

        css = f"""
        .wrap {{ position:relative; padding:0 44px {96 if self.footer else 60}px; }}
        .header {{ position:absolute; top:0; left:0; right:0; height:190px; background:{a}; }}
        .header .pill {{ position:absolute; top:40px; left:60px; color:{a}; font-size:36px; padding:10px 40px; }}
        .me {{ position:absolute; top:40px; right:60px; }}
        .me img {{ width:250px !important; height:250px !important; border:9px solid {a} !important; }}
        .nmblock {{ position:relative; padding:205px 290px 0 16px; min-height:330px; }}
        .nm {{ font-size:50px; font-weight:800; line-height:1.1; }}
        .tt {{ font-size:24px; opacity:.85; }}
        .feat {{ position:relative; background:rgba(8,12,55,.8); border:2px solid {a}99; border-radius:18px; padding:20px 24px; margin-bottom:18px; }}
        .feat .with {{ position:absolute; right:24px; bottom:20px; }}
        .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
        .tile {{ background:rgba(8,12,55,.8); border:2px solid {a}99; border-radius:18px; padding:20px 24px; display:flex; flex-direction:column; }}
        .code {{ font-size:21px; font-weight:800; color:#F2A7F5; }}
        .code span {{ float:right; font-size:15px; font-weight:700; background:{a}; color:#fff; padding:3px 12px; border-radius:16px; text-transform:uppercase; }}
        .title {{ font-size:30px; font-weight:600; line-height:1.18; margin:10px 0 8px; }}
        .date {{ font-size:20px; opacity:.85; }}
        .tile .with {{ margin-top:auto; padding-top:18px; }}
        .with {{ display:flex; align-items:center; gap:12px; font-size:20px; }}
        .pair {{ display:flex; }} .pair img + img {{ margin-left:-12px; }}
        .announce {{ margin-top:18px; border-radius:18px; padding:20px 26px; text-align:center; font-size:32px; font-weight:800;
                     background:linear-gradient(100deg, {a}, #6A4BEA 55%, #0078D4); }}
        .foot {{ position:absolute; bottom:34px; left:0; right:0; text-align:center; font-size:22px; opacity:.85; }}
        """
        body = f"""{self.bg_layer()}
        <div class="header"><div class="pill">{self.esc(self.headline)}</div></div>
        <div class="me">{self.avatar(self.owner, 250)}</div>
        <div class="wrap">
          <div class="nmblock"><div class="nm">{self.esc(me["name"])}</div><div class="tt">{self.esc(me.get("title"))}</div></div>
          {tile(feat, "feat") if feat else ""}
          <div class="grid">{"".join(tile(s, "tile") for s in rest)}</div>
          {self.announce_html()}
        </div>{self.foot()}<div class="bottom-bar"></div>"""
        return self.page(css, body, STYLES["tiles"][0])

    def list(self):
        me, a = self.people[self.owner], self.accent
        sub = self.c.get("subheadline", "")
        head_h = 270 if sub else 190
        rows = ""
        for s in self.sessions:
            co = "".join(self.avatar(k, 70) for k in s["cos"][:2])
            label = f'<div class="n">with {" &amp; ".join(self.first(k) for k in s["cos"])}</div>' if s["cos"] else ""
            rows += f"""<div class="row"><div class="what">
              <div class="code">{self.esc(s.get("code"))} · {self.esc(s.get("type"))}</div>
              <div class="title">{self.esc(s["title"])}</div><div class="date">📅 {self.dates(s)}</div></div>
              <div class="co"><div class="pair">{co}</div>{label}</div></div>"""
        css = f"""
        .header {{ position:absolute; top:0; left:0; right:0; height:{head_h}px; background:{a}; text-align:center; padding-top:44px; }}
        .header .pill {{ color:{a}; font-size:40px; padding:12px 56px; }}
        .header h1 {{ font-weight:400; font-size:42px; margin-top:26px; line-height:1.25; }}
        .me {{ position:absolute; top:{head_h - 75}px; left:60px; display:flex; align-items:center; gap:28px; }}
        .me img {{ width:210px !important; height:210px !important; border:9px solid {a} !important; }}
        .nm {{ font-size:46px; font-weight:700; margin-top:70px; }}
        .tt {{ font-size:26px; opacity:.9; }}
        .wrap {{ position:relative; padding:{head_h + 155}px 46px {84 if self.footer else 50}px; }}
        .row {{ display:flex; align-items:center; gap:20px; padding:14px 26px; margin-bottom:12px;
                background:rgba(10,14,60,.72); border-left:8px solid {a}; border-radius:12px; }}
        .what {{ flex:1; }}
        .code {{ font-size:19px; font-weight:700; letter-spacing:.5px; color:#E9A8FF; text-transform:uppercase; }}
        .title {{ font-size:28px; font-weight:600; line-height:1.17; margin:2px 0 4px; }}
        .date {{ font-size:21px; opacity:.85; }}
        .co {{ text-align:center; width:110px; flex-shrink:0; }}
        .pair {{ display:flex; justify-content:center; }} .pair img + img {{ margin-left:-22px; }}
        .co .n {{ font-size:17px; opacity:.85; margin-top:3px; }}
        .announce {{ margin-top:6px; border-radius:12px; padding:18px; text-align:center; font-size:30px; font-weight:800;
                     background:linear-gradient(100deg, {a}, #6A4BEA 55%, #0078D4); }}
        .foot {{ position:absolute; bottom:32px; left:0; right:0; text-align:center; font-size:22px; opacity:.85; }}
        """
        body = f"""{self.bg_layer()}
        <div class="header"><div class="pill">{self.esc(self.headline)}</div>{f"<h1>{self.esc(sub)}</h1>" if sub else ""}</div>
        <div class="me">{self.avatar(self.owner, 210)}<div><div class="nm">{self.esc(me["name"])}</div><div class="tt">{self.esc(me.get("title"))}</div></div></div>
        <div class="wrap">{rows}{self.announce_html()}</div>{self.foot()}<div class="bottom-bar"></div>"""
        return self.page(css, body, STYLES["list"][0])

    def landscape(self):
        me, a = self.people[self.owner], self.accent
        cols = ""
        for s in self.sessions:
            cols += f"""<div class="col"><div class="tag">{self.esc(s.get("type"))}</div>
              <div class="title">{self.esc(s["title"])}</div><div class="date">{self.dates(s, short=True)}</div>
              {self.with_line(s["cos"], 34)}</div>"""
        css = f"""
        body {{ display:flex; }}
        .left {{ position:relative; width:270px; flex-shrink:0; background:{a}; text-align:center; padding:22px 0 26px; }}
        .left .pill {{ color:{a}; font-size:18px; padding:7px 12px; border-radius:10px; }}
        .left img {{ margin-top:14px; }}
        .nm {{ font-size:30px; font-weight:700; margin-top:8px; }}
        .tt {{ font-size:16px; opacity:.92; padding:0 16px; }}
        .right {{ position:relative; flex:1; padding:22px 22px 30px; display:flex; flex-direction:column; justify-content:center; }}
        .cols {{ display:grid; grid-template-columns:repeat({len(self.sessions)},1fr); gap:10px; width:100%; }}
        .col {{ background:rgba(8,12,55,.75); border-top:5px solid {a}; border-radius:10px; padding:12px 13px; display:flex; flex-direction:column; }}
        .tag {{ font-size:12px; font-weight:800; color:#F2A7F5; text-transform:uppercase; letter-spacing:.5px; }}
        .title {{ font-size:19px; font-weight:600; line-height:1.18; margin-top:6px; }}
        .date {{ font-size:14px; opacity:.8; margin-top:8px; font-weight:600; }}
        .with {{ margin-top:auto; padding-top:12px; display:flex; align-items:center; gap:8px; font-size:13px; line-height:1.15; }}
        .pair {{ display:flex; flex-shrink:0; }} .pair img + img {{ margin-left:-10px; }}
        .announce {{ margin-top:12px; border-radius:10px; padding:10px; text-align:center; font-size:20px; font-weight:800;
                     background:linear-gradient(100deg, {a}, #6A4BEA 55%, #0078D4); }}
        """
        body = f"""{self.bg_layer()}
        <div class="left"><div class="pill">{self.esc(self.headline)}</div><br>{self.avatar(self.owner, 130, "6px solid #fff")}
          <div class="nm">{self.esc(me["name"])}</div><div class="tt">{self.esc(me.get("title"))}</div></div>
        <div class="right"><div class="cols">{cols}</div>{self.announce_html()}</div>
        <div class="bottom-bar" style="height:10px"></div>"""
        return self.page(css, body, STYLES["landscape"][0])

    def compact(self):
        cols = ""
        for s in self.sessions:
            keys = [self.owner] + s["cos"]
            imgs = "".join(self.avatar(k, 28, "2px solid #111") for k in keys)
            cols += f"""<div class="col"><div class="tag">{self.emoji(s.get("type"))} {self.esc((s.get("type") or "").lower())}</div>
              <div class="title">{self.esc(s["title"])}</div><div class="date">{self.dates(s, short=True)}</div>
              <div class="with"><span class="pair">{imgs}</span><span>{" &amp; ".join(self.first(k) for k in keys)}</span></div></div>"""
        css = f"""
        body {{ padding:26px 26px 30px; }}
        .cols {{ display:grid; grid-template-columns:repeat({len(self.sessions)},1fr); gap:10px; }}
        .col {{ background:#111; border:1px solid #2a2a2a; border-radius:16px; padding:12px; display:flex; flex-direction:column; }}
        .tag {{ font-size:13px; font-weight:700; color:#F2A7F5; }}
        .title {{ font-size:17px; font-weight:600; line-height:1.2; margin-top:6px; }}
        .date {{ font-size:13px; opacity:.75; margin-top:8px; }}
        .with {{ margin-top:auto; padding-top:10px; display:flex; align-items:center; gap:7px; font-size:13px; opacity:.9; }}
        .pair {{ display:flex; flex-shrink:0; }} .pair img + img {{ margin-left:-9px; }}
        .announce {{ margin-top:12px; border-radius:14px; padding:10px; text-align:center; font-size:18px; font-weight:800; background:#1d1d1d; }}
        """
        body = f"""<div class="cols">{cols}</div>{self.announce_html()}<div class="bottom-bar" style="height:6px"></div>"""
        return self.page(css, body, STYLES["compact"][0], bg="#000")


async def render(card, styles, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for style in styles:
            width = STYLES[style][0]
            page = await browser.new_page(viewport={"width": width, "height": 800})
            tmp = out_dir / f".{card.owner}_{style}.html"
            tmp.write_text(getattr(card, style)())
            await page.goto(tmp.resolve().as_uri(), wait_until="networkidle")
            height = await page.evaluate("document.body.offsetHeight")
            await page.set_viewport_size({"width": width, "height": height})
            path = out_dir / f"{card.owner}_{style}.png"
            await page.screenshot(path=str(path))
            tmp.unlink()
            print(f"wrote {path} ({width}x{height})")
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("config", help="Path to config.json")
    parser.add_argument("output_dir", help="Directory for PNG output")
    parser.add_argument("--owner", help="Key in 'people' to make the card for (default: config 'owner')")
    parser.add_argument("--style", nargs="+", choices=list(STYLES), default=list(STYLES), help="Styles to render (default: all)")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    owner = args.owner or config.get("owner") or next(iter(config["people"]))
    card = Card(config, config_path.parent, owner)
    asyncio.run(render(card, args.style, Path(args.output_dir)))


if __name__ == "__main__":
    main()
