#!/usr/bin/env python3
"""Build Wave 2 hero gallery — all 9 tabs side-by-side."""
from pathlib import Path

OUT = Path("/root/mxstream-app/static/u4_compare/w2.html")

TABS = [
    ("home",    "Home",                "FEATURED · Project Hail Mary · 3 CTAs"),
    ("movies",  "Movies",              "MOVIE OF THE DAY · Project Hail Mary · 3 CTAs"),
    ("series",  "Series",              "PICK UP WHERE YOU LEFT OFF · Breaking Bad · Resume CTA"),
    ("anime",   "Anime",               "FULL LATIN-AM DUB showcase · 1080+ episodes"),
    ("kids",    "Kids",                "TONIGHT'S FAMILY MOVIE · Coco · Watch Together"),
    ("livetv",  "Live TV",             "What's on now · American TV · multiplex picker"),
    ("sports",  "Sports",              "LIVE NOW · América vs Pumas · scoreboard hero"),
    ("esports", "Esports",             "Worlds 2026 · Watch on Twitch / YouTube / Bracket"),
    ("adult",   "Premium TV (18+)",    "PREMIUM PRIVATE LIBRARY · 3-bucket Creators+Hentai+Tube"),
]

CARDS = "\n".join(f"""
  <section class="row">
    <h3>{title}</h3>
    <p class="note">{note}</p>
    <img src="w2_{slug}.png" alt="{title} hero">
  </section>
""" for slug, title, note in TABS)

HTML = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><title>RomanTV · Wave 2 · all 9 heroes</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ --bg:#0b0c10; --panel:#13151a; --panel2:#1c1e26; --line:#2c2e38; --text:#fff; --dim:#a8a8b0; --accent:#e50914; --gold:#ffd66b; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font:400 14px/1.5 -apple-system, sans-serif; padding:32px; }}
  header.intro {{ max-width:1100px; margin:0 auto 32px; }}
  header.intro h1 {{ margin:0 0 8px; font:800 32px/1.1 'Playfair Display', Georgia, serif; }}
  header.intro h1 em {{ color:var(--gold); font-style:italic; }}
  header.intro .lede {{ color:var(--dim); font-size:16px; }}
  header.intro ul {{ color:var(--dim); font-size:14px; padding-left:20px; }}
  header.intro ul li {{ margin:4px 0; }}
  header.intro ul strong {{ color:var(--text); }}
  .qc-banner {{ margin-top:16px; padding:12px 16px; background:rgba(255, 214, 107, 0.10); border:1px solid rgba(255, 214, 107, 0.4); border-radius:12px; color:var(--text); font-size:13px; }}
  .qc-banner strong {{ color:var(--gold); }}
  .row {{ max-width:1100px; margin:0 auto 32px; padding:18px 24px; background:var(--panel); border:1px solid var(--line); border-radius:14px; }}
  .row h3 {{ margin:0 0 4px; font:700 18px/1 -apple-system, sans-serif; color:var(--gold); }}
  .row .note {{ margin:0 0 12px; color:var(--dim); font-size:13px; }}
  .row img {{ width:100%; display:block; border:1px solid var(--line); border-radius:8px; }}
  footer {{ max-width:1100px; margin:32px auto 0; color:var(--dim); font-size:13px; padding-top:16px; border-top:1px solid var(--line); }}
</style>
</head>
<body>
  <header class="intro">
    <h1>Wave 2 — <em>unified hero treatment</em></h1>
    <p class="lede">Cursor dispatched. Wave 2 CSS appended to <code>u4_unified.css</code> (cache-bust v=11). Each hero now follows the same pattern: italic gold kicker → big white title → dim description → 2-3 CTAs (red primary + secondary + sometimes tertiary).</p>
    <ul>
      <li><strong>Hero anatomy:</strong> kicker (italic gold uppercase) → title (sans bold 64-84px) → desc (1 line dim) → CTAs (.btn-primary red w/ gold edge + .btn-secondary outline gold)</li>
      <li><strong>Per-tab content kept intact:</strong> live scoreboard (Sports), continue-watching strip (Series), bucket strip (18+), channel multiplex (Live TV), age-chip filter (Kids)</li>
      <li><strong>Canonical class names:</strong> <code>.hero-kicker</code>, <code>.hero-title</code>, <code>.hero-desc</code>, <code>.hero-ctas</code> applied across pages — unified CSS targets these without per-tab overrides</li>
      <li><strong>Cache-bust:</strong> v=11</li>
    </ul>
    <p class="qc-banner">★ Skim the gallery. Heroes share the same visual language now: gold kicker · big bold title · 1-line desc · CTA pair. Anime and 18+ titles look slightly small relative to others — quick tune available if you flag them. Otherwise greenlight Wave 3 (tiles + chips).</p>
  </header>

{CARDS}

  <footer>
    Wave 1 v10 (topbar) · Wave 2 v11 (hero) shipped. Wave 3 next: tiles + chips. Wave 4: cards.
  </footer>
</body>
</html>
"""

OUT.write_text(HTML)
print(f"→ wrote {OUT}: {len(HTML):,} chars")
print(f"→ open: https://romantv.net/static/u4_compare/w2.html")
