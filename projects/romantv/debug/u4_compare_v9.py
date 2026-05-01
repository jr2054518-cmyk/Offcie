#!/usr/bin/env python3
"""Build a clean v=9 gallery — all 9 tabs side-by-side, after Cursor's
fresh-start strip pass + 2 manual bug fixes. NO before/after splits;
just the current state of each tab so Juan can sweep the row of 9
and confirm consistency."""
from pathlib import Path

OUT = Path("/root/mxstream-app/static/u4_compare/v10.html")
VER = "10"

TABS = [
    ("home",   "Home"),
    ("movies", "Movies"),
    ("series", "Series"),
    ("anime",  "Anime"),
    ("kids",   "Kids"),
    ("livetv", "Live TV"),
    ("sports", "Sports"),
    ("esports","Esports"),
    ("adult",  "Premium TV (18+)"),
]
SLUG_FILE = {
    "home":    "v10_home_APPROVED_v1a.png",
    "movies":  "v10_movies_APPROVED_v1.png",
    "series":  "v10_series_APPROVED_h1.png",
    "anime":   "v10_anime_APPROVED_a1b.png",
    "kids":    "v10_kids_APPROVED_k4.png",
    "livetv":  "v10_livetv_APPROVED_lt1.png",
    "sports":  "v10_sports_APPROVED_sp1.png",
    "esports": "v10_esports_APPROVED_es1.png",
    "adult":   "v10_adult_APPROVED_eg1v2.png",
}

CARDS = "\n".join(f"""
  <section class="row">
    <h3>{title}</h3>
    <img src="{SLUG_FILE[slug]}" alt="{title} topbar">
  </section>
""" for slug, title in TABS)

HTML = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><title>RomanTV · Wave 1 v10 · all 9 topbars</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ --bg:#0b0c10; --panel:#13151a; --panel2:#1c1e26; --line:#2c2e38; --text:#fff; --dim:#a8a8b0; --accent:#e50914; --gold:#ffd66b; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font:400 14px/1.5 -apple-system, sans-serif; padding:32px; }}
  header.intro {{ max-width:1200px; margin:0 auto 32px; }}
  header.intro h1 {{ margin:0 0 8px; font:800 32px/1.1 'Playfair Display', Georgia, serif; }}
  header.intro h1 em {{ color:var(--gold); font-style:italic; }}
  header.intro .lede {{ color:var(--dim); font-size:16px; }}
  header.intro ul {{ color:var(--dim); font-size:14px; padding-left:20px; }}
  header.intro ul li {{ margin:4px 0; }}
  header.intro ul strong {{ color:var(--text); }}
  .qc-banner {{ margin-top:16px; padding:12px 16px; background:rgba(255, 214, 107, 0.10); border:1px solid rgba(255, 214, 107, 0.4); border-radius:12px; color:var(--text); font-size:13px; }}
  .qc-banner strong {{ color:var(--gold); }}
  .row {{ max-width:1200px; margin:0 auto 32px; padding:18px 24px; background:var(--panel); border:1px solid var(--line); border-radius:14px; }}
  .row h3 {{ margin:0 0 12px; font:700 16px/1 -apple-system, sans-serif; color:var(--gold); letter-spacing:.5px; }}
  .row img {{ width:100%; display:block; border:1px solid var(--line); border-radius:8px; }}
  footer {{ max-width:1200px; margin:32px auto 0; color:var(--dim); font-size:13px; padding-top:16px; border-top:1px solid var(--line); }}
</style>
</head>
<body>
  <header class="intro">
    <h1>Wave 1 v10 — <em>active state aliases added</em></h1>
    <p class="lede">v9 had every tab's topbar consistent EXCEPT the active-tab indicator wasn't rendering on Home and Esports. Reason: each tab uses a different active-state class name (Home uses <code>.is-on</code>, Esports uses <code>.es1-active</code>, others use <code>.is-active</code> / <code>.active</code> / <code>aria-current="page"</code>). The unified CSS now accepts <strong>14 active-state aliases</strong> so the gold underline renders no matter which class the tab uses.</p>
    <ul>
      <li><strong>Active-class aliases added:</strong> <code>.is-active</code> · <code>.active</code> · <code>.is-on</code> · <code>.on</code> · <code>.v1a-active</code> · <code>.rv-active</code> · <code>.h1-active</code> · <code>.a1b-active</code> · <code>.k4-active</code> · <code>.lt-active</code> · <code>.sp1-active</code> · <code>.es1-active</code> · <code>.nav-link--active</code> · <code>[aria-current=page]</code></li>
      <li><strong>Wave 1 history:</strong> v1-4 unified topbar deployment · v5 Cursor strip pass · v6-7 search-icon dedup · v8 broken pseudo-element bug · v9 wrap layout · v10 active-state aliases</li>
      <li><strong>Unified CSS:</strong> 26.4 KB · cache-bust v=10</li>
    </ul>
    <p class="qc-banner">★ Verify: scroll the row of 9 below — every tab should show its current page name with a <strong style="color:#ffd66b">gold underline</strong> + gold-tinted background. No red pills. No double magnifiers. No layout breaks.</p>
  </header>

{CARDS}

  <footer>
    Each topbar shown above shares: 72px min-height (wraps when content overflows) · single 44px search pill with magnifier glass · gold underline on the active tab · same brand placement · same font scale · 3-device-class responsive (mobile wraps, TV grows to 88px). Wave 2 next: hero treatment.
  </footer>
</body>
</html>
"""

OUT.write_text(HTML)
print(f"→ wrote {OUT}: {len(HTML):,} chars")
print(f"→ open: https://romantv.net/static/u4_compare/v9.html")
