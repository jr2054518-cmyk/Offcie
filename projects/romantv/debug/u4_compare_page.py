#!/usr/bin/env python3
"""Build a single comparison HTML showing Wave 1 BEFORE/AFTER side-by-side
across 4 representative tabs (Home, Series, Live TV, 18+)."""
from pathlib import Path

OUT = Path("/root/mxstream-app/static/u4_compare/index.html")

PAIRS = [
    ("home",          "Home / v1A",                      "Header was thin (62px), search input small, nav had its own .active pill"),
    ("series",        "Series / h1",                     "Search 40px, RomanTV brand sized differently, nav links cramped"),
    ("livetv",        "Live TV / lt1",                   "Top-bar was sticky and 70px-ish, REGION pill weirdly outside nav"),
    ("esports",       "Esports / es1 · QC fix",     "BEFORE shipped with no real search input — Cursor used a placeholder &lt;div&gt;. QC pass converted it to a proper &lt;input type=search&gt;."),
    ("adult_FIXED",   "18+ / Premium TV / eg1v2 · QC fix", "BEFORE Wave 1 had TWO search bars stacked: topbar search + a body-level &lt;form class=search-wide&gt; below the title. QC pass removed the body duplicate."),
]

def slug_files(slug):
    """Map slug -> (before_file, after_file). The QC-fix variant uses a different AFTER."""
    if slug == "adult_FIXED":
        return "w1_BEFORE_adult.png", "w1_AFTER_adult_FIXED.png"
    return f"w1_BEFORE_{slug}.png", f"w1_AFTER_{slug}.png"

CARDS = "\n".join(f"""
  <section class="pair">
    <h2>{title}</h2>
    <p class="note">{note}</p>
    <div class="grid">
      <figure><figcaption>BEFORE</figcaption><img src="{slug_files(slug)[0]}" alt="before"></figure>
      <figure><figcaption>AFTER — u4 unified</figcaption><img src="{slug_files(slug)[1]}" alt="after"></figure>
    </div>
  </section>
""" for slug, title, note in PAIRS)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RomanTV · u4 Wave 1 · Before / After</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ --bg:#0b0c10; --panel:#13151a; --panel2:#1c1e26; --line:#2c2e38; --text:#fff; --dim:#a8a8b0; --accent:#e50914; --gold:#ffd66b; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font:400 14px/1.5 -apple-system, Segoe UI, Roboto, sans-serif; padding:32px; }}
  header.intro {{ max-width: 1100px; margin: 0 auto 32px; }}
  header.intro h1 {{ margin:0 0 8px; font:800 32px/1.1 'Playfair Display', Georgia, serif; }}
  header.intro h1 em {{ color: var(--gold); font-style: italic; }}
  header.intro .lede {{ color: var(--dim); font-size: 16px; }}
  header.intro ul {{ color: var(--dim); font-size: 14px; padding-left: 20px; }}
  header.intro ul li {{ margin: 4px 0; }}
  header.intro ul strong {{ color: var(--text); }}
  header.intro .qc-banner {{ margin-top: 16px; padding: 12px 16px; background: rgba(255, 214, 107, 0.10); border:1px solid rgba(255, 214, 107, 0.4); border-radius: 12px; color: var(--text); font-size: 13px; line-height: 1.6; }}
  header.intro .qc-banner strong {{ color: var(--gold); }}
  .pair {{ max-width: 1100px; margin: 0 auto 48px; padding: 24px; background: var(--panel); border:1px solid var(--line); border-radius: 16px; }}
  .pair h2 {{ margin: 0 0 4px; font: 700 22px/1 -apple-system, sans-serif; }}
  .pair .note {{ color: var(--dim); margin: 0 0 16px; font-size: 13px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  figure {{ margin: 0; }}
  figcaption {{ font: 700 11px/1 -apple-system, sans-serif; color: var(--gold); letter-spacing: 1px; text-transform: uppercase; padding: 8px 12px; background: var(--panel2); border: 1px solid var(--line); border-radius: 8px 8px 0 0; }}
  figure img {{ width: 100%; display:block; border:1px solid var(--line); border-top:none; border-radius: 0 0 8px 8px; }}
  @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  footer {{ max-width: 1100px; margin: 32px auto 0; color: var(--dim); font-size: 13px; padding-top: 16px; border-top: 1px solid var(--line); }}
</style>
</head>
<body>
  <header class="intro">
    <h1>u4 Wave 1 — <em>before / after</em></h1>
    <p class="lede">Wave 1 = unified top-bar (header + search + nav). One CSS file targets every tab's bespoke selectors so all 9 catalog tabs share the exact same header.</p>
    <ul>
      <li><strong>Top-bar height:</strong> 72px laptop · 56px mobile (wraps to rows) · 88px TV box</li>
      <li><strong>Search:</strong> 44px pill with magnifier icon, gold focus glow (was: 40px varied per tab)</li>
      <li><strong>Nav links:</strong> 40px / 14px font / 10px radius, gold underline on .is-active (was: each tab had its own active style — pill, square, red, etc.)</li>
      <li><strong>D-pad focus:</strong> 4px gold ring laptop · 6px gold ring TV (consistent everywhere)</li>
      <li><strong>Implementation:</strong> single <code>/static/u4_unified.css</code> (14.2 KB) injected via <code>&lt;link&gt;</code> tag — zero HTML rewrites</li>
    </ul>
    <p class="qc-banner">★ <strong>QC PASS</strong> · 9 tabs audited · 2 issues found and fixed: Esports had a fake &lt;div&gt; placeholder instead of a real input · 18+ had a duplicate body-level search alongside the topbar one. Both fixed below.</p>
  </header>

{CARDS}

  <footer>
    Wave 2 next: unified hero treatment (60vh/50vh/85vh · italic serif kicker + sans bold title · 2 CTA pattern). · Cache-bust v=3
  </footer>
</body>
</html>
"""

OUT.write_text(HTML)
print(f"→ wrote {OUT}: {len(HTML):,} chars")
print(f"→ open: https://romantv.net/static/u4_compare/")
