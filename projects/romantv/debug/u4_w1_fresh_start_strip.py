#!/usr/bin/env python3
"""u4 Wave 1 FRESH-START STRIP — dispatch Cursor to remove ALL lingering
per-tab topbar/search/nav CSS + sibling magnifier icon spans from each
of the 9 catalog HTML files. After this runs, /static/u4_unified.css owns
the topbar with no overrides needed.

Per Juan: 'the whole point of redoing everything was a fresh start so we
don't have lingering code'. We remove the OLD inline rules + leftover icon
elements; the unified CSS is the SINGLE source of truth.
"""
import subprocess
from pathlib import Path

CURSOR = "/root/.local/bin/cursor-agent"
MODEL = "auto"

CTX = """RomanTV catalog cleanup — remove lingering bespoke top-bar code so
/static/u4_unified.css can OWN the topbar/search/nav unambiguously.

CONTEXT:
We have 9 catalog HTML pages at /root/mxstream-app/static/mockups/CATALOG/:
  home_APPROVED_v1a.html       (uses classes: .v1a-topbar .v1a-nav .v1a-search ...)
  movies_APPROVED_v1.html      (.rv-topbar .rv-nav .rv-search .rv-search-icon)
  series_APPROVED_h1.html      (.h1-topbar .h1-mainnav .h1-search)
  anime_APPROVED_a1b.html      (.a1b-topbar .a1b-nav .a1b-search)
  kids_APPROVED_k4.html        (.k4-topbar .k4-nav .k4-search)
  livetv_APPROVED_lt1.html     (.lt-top .lt-nav .lt-search-wrap .lt-search-icon .lt-search)
  sports_APPROVED_sp1.html     (.sp1-topbar .sp1-nav .sp1-search)
  esports_APPROVED_es1.html    (.es1-top .es1-nav .es1-search)
  adult_APPROVED_eg1v2.html    (.topbar .nav-pills .top-search)

Each page has TWO copies of its design (one inside <div class="lang-wrap" id="lang-en">
and one inside <div class="lang-wrap" id="lang-es">). Apply changes to BOTH copies.

The unified styling lives at /root/mxstream-app/static/u4_unified.css and is loaded
via <link rel="stylesheet" href="/static/u4_unified.css?v=4"> in each page's <head>.

WHAT TO STRIP IN EACH PAGE:
1. Remove inline <style> CSS rules whose selectors target topbar/search/nav layout:
   - .v1a-topbar, .rv-topbar, .h1-topbar, .a1b-topbar, .k4-topbar, .lt-top,
     .sp1-topbar, .es1-top, .lang-wrap > .topbar, .lang-wrap .design > .topbar
     -> rules setting height, display, padding, background, border, position, gap,
        align-items, sticky, position. KEEP rules for child elements like .v1a-brand
        (logo) or .lt-region-pill (regional pills) — those are page-specific tools.
   - .v1a-nav, .rv-nav, .h1-mainnav, .a1b-nav, .k4-nav, .lt-nav, .sp1-nav, .es1-nav,
     .lang-wrap .nav-pills
     -> rules setting display, gap, align-items, flex-wrap. KEEP nav-active visual
        bonuses (e.g. background red = the active 'tab' indicator) only if removing
        them would break which-tab-is-active.
   - .X-nav a, .X-nav button, .X-mainnav a, etc.
     -> rules setting padding, color, font, border-radius, height. KEEP page-unique
        treatments only if visually load-bearing.
   - .X-search, .X-search input, .X-search-wrap input, .X-search-wrap input[type=search]
     -> rules setting height, padding, background, border-radius, border, color, font,
        outline. STRIP entirely — unified CSS handles this.
   - .X-search-icon AND .X-search-icon::after (the legacy magnifier glass — there's a
     SVG/CSS-art icon here that duplicates the magnifier the unified CSS adds).
     -> STRIP ALL rules for these selectors.

2. Remove sibling icon HTML elements that produce a duplicate magnifier:
   - <span class="rv-search-icon" ...></span>
   - <span class="lt-search-icon" ...></span>
   - any <svg> or <span> immediately before/inside the <input type=search> wrapper that
     renders a magnifier glass. The unified CSS already adds a magnifier as a
     background-image on the input itself.

3. Remove <link rel="stylesheet" href="/static/u4_unified.css?..."> if present, then
   re-add as <link rel="stylesheet" href="/static/u4_unified.css?v=5"> right after
   <title> (so the cache busts and we trigger a reload). DO NOT remove other <link>
   tags or <script> tags.

4. After stripping, REMOVE my temporary suppression rule from /static/u4_unified.css:
   the block starting with the comment
   "/* ─── Suppress legacy sibling magnifier icons (movies + livetv shipped with their own) ─── */"
   and the rule that follows it (4 selectors with display: none !important).
   The unified CSS should look clean — no defensive overrides.

WHAT TO KEEP:
- The HTML structure (don't change the <header class="...">; keep existing class names)
- Brand wordmarks (.v1a-brand, .lt-brand, etc.)
- Regional tools (.lt-region-pill, .sp1-mexico-pill, language toggles)
- Nav active state CLASS NAME (e.g. .v1a-nav a.is-active) — JUST DON'T duplicate the
  visual styling; let the unified CSS render it.
- All <script> tags and JS handlers untouched.

VERIFY:
- After stripping, run: `python3 /root/mxstream_debug/u4_search_icon_audit.py`
  Expected: 0 of 9 tabs have a likely duplicate icon.
- Then `python3 /root/mxstream_debug/u4_qc_audit.py` and confirm all 9 ✓ OK with
  exactly 1 visible search input per page.
- Use chrome --headless to render screenshots: e.g.
    google-chrome --headless --no-sandbox --disable-gpu --window-size=1440,200 \\
      --screenshot=/tmp/clean_lt.png \\
      'https://romantv.net/static/mockups/CATALOG/livetv_APPROVED_lt1.html'
  Verify visually that there's exactly ONE magnifier in each page's search bar.

DELIVERABLE:
- All 9 HTML files cleaned up (idempotent — running twice should be a no-op)
- u4_unified.css with the suppression rule removed
- A short report listing per-page: bytes-stripped, icons-removed, css-rules-removed
- Run the audits at the end and report PASS/FAIL.

Be CAREFUL: don't break layout. If you're unsure whether a CSS rule is page-specific
or topbar-redundant, KEEP it. Better to leave 1 line of mostly-harmless old code than
break a layout. Backup each file before editing as `<filename>.bak_freshstart`.
"""

prompt_file = "/tmp/cursor_freshstart.txt"
out_file = "/tmp/cursor_freshstart.out"
Path(prompt_file).write_text(CTX)

print(f"Dispatching Cursor with {MODEL} (this will take ~5-10 min)...")
cmd = f'{CURSOR} --model {MODEL} --print --force --yolo "$(cat {prompt_file})" > {out_file} 2>&1'
try:
    subprocess.run(["bash", "-c", cmd], timeout=900)
    print("→ Cursor finished")
except subprocess.TimeoutExpired:
    print("⚠ Cursor timed out — check /tmp/cursor_freshstart.out for partial output")

# Print the last 80 lines of cursor output
out = Path(out_file).read_text() if Path(out_file).exists() else "(no output)"
print("\n=== CURSOR OUTPUT (last 80 lines) ===")
print("\n".join(out.split("\n")[-80:]))
