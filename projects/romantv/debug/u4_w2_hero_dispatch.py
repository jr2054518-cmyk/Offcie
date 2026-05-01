#!/usr/bin/env python3
"""u4 Wave 2 dispatch — give Cursor the full hero unification job.

Cursor handles audit + design + apply + strip-bespoke + verify across all
9 catalog pages. Same fresh-start pattern that worked for Wave 1.
"""
import subprocess
from pathlib import Path

CURSOR = "/root/.local/bin/cursor-agent"
MODEL = "auto"  # premium tier exhausted earlier — auto handles it

CTX = """RomanTV catalog Wave 2 — UNIFIED HERO TREATMENT across 9 tabs.

CONTEXT:
Wave 1 finished: /root/mxstream-app/static/u4_unified.css (cache-bust v=10) owns
the topbar/search/nav across all 9 catalog pages with NO per-tab overrides. We
stripped 188 bespoke CSS rules and 4 leftover magnifier spans. Same approach
needed for Wave 2 hero.

9 catalog pages at /root/mxstream-app/static/mockups/CATALOG/:
  home_APPROVED_v1a.html       (Cinematic Hero, 5-pick rotating spotlight, full-bleed background)
  movies_APPROVED_v1.html      (Featured movie hero w/ poster + 2 CTAs)
  series_APPROVED_h1.html      (Resume-First continue-watching hero, "Pick up where you left off")
  anime_APPROVED_a1b.html      (Cinematic Hero · Dub-First showcase, 70vh rotating spotlight)
  kids_APPROVED_k4.html        ("Tonight's Family Movie" hero, single curated pick e.g. Coco)
  livetv_APPROVED_lt1.html     (Channel grid + EPG strip, "What's on now · American TV" hero)
  sports_APPROVED_sp1.html     (LIVE-NOW WALL, multiplex picks, scoreboard hero)
  esports_APPROVED_es1.html    (Tournament-Centric, GRID adapter feed)
  adult_APPROVED_eg1v2.html    ("Premium private library", 3-bucket Creators+Hentai+Tube hero)

Each page has TWO copies of its design (lang-en + lang-es wrappers). Apply
changes to BOTH copies. Read /root/mxstream-app/static/u4_unified.css to see
the established pattern.

DESIGN SPEC (from the u4 system Juan picked):
  • HERO HEIGHT: min-height 60vh laptop · 50vh mobile · 85vh TV-box
  • OVERLAY: linear-gradient(135deg, rgba(11,12,16,0.95) 0%, rgba(11,12,16,0.5) 50%, transparent 100%)
    -> dark-on-left, fades to clear-on-right (so right-side imagery shows through)
  • KICKER (eyebrow): italic serif, gold (#ffd66b), 14-16px, uppercase 1px letter-spacing
    -> e.g. "FEATURED" / "TONIGHT'S FAMILY MOVIE" / "PICK UP WHERE YOU LEFT OFF"
  • TITLE: sans bold, white, 64-84px laptop, 48-60px mobile, 96-120px TV
    -> e.g. "Project Hail Mary" / "Breaking Bad" / "Coco · Watch Together Tonight"
  • DESCRIPTION: 1 line, var(--dim) #a8a8b0, 16-18px, max 70 chars before ellipsis
  • CTAs: 2 primary buttons, 64px height
    -> Primary: red bg (var(--u4-red) #ff0a14) + 4px gold left-edge accent + white text
    -> Secondary: transparent bg + 2px gold border + gold text
  • CONTENT POSITION: kicker + title + desc + CTAs in left 60% of hero, right 40% reserved for visual

CSS VARS (use these — already defined in u4_unified.css):
  --bg:#0b0c10  --panel:#13151a  --panel2:#1c1e26  --line:#2c2e38
  --text:#fff   --dim:#a8a8b0  --accent:#e50914  --gold:#ffd66b
  --u4-red:#ff0a14  --u4-tb-h:72px

YOUR JOB:
1. AUDIT each of the 9 pages — find the hero container class (.X-hero / .X-spotlight /
   .X-cinematic / .X-tonight / .X-live-now-wall / etc.) and its kicker / title / description / CTA elements.
2. Build a Wave 2 CSS BLOCK to APPEND to /root/mxstream-app/static/u4_unified.css —
   target every tab's hero container + its kicker/title/desc/CTAs by their bespoke class names
   (use comma-separated lists like Wave 1). Use !important where overriding bespoke styles.
3. STRIP bespoke per-tab hero/cinematic/spotlight CSS rules from each catalog page's
   inline <style> block (rules that set hero height, padding, background-overlay, kicker
   font, title font, CTA dimensions). KEEP the page's UNIQUE per-page bonus content
   (e.g. live scoreboard cells in Sports, Episode-picker grid in Series, Bucket strip
   in 18+, Channel-grid in Live TV) — those are non-hero design features.
4. STRIP leftover bespoke CTA classes IF they conflict (e.g. .v1a-btn-primary, .h1-btn-resume,
   .k4-play). Replace with .btn-primary / .btn-secondary class names IN THE HTML so the
   unified CSS owns them.
5. RENAME (in HTML) any bespoke kicker class names to a single canonical class
   (.hero-kicker) so the unified CSS targets them all uniformly. Do the same for
   title (.hero-title) and description (.hero-desc) and CTA wrapper (.hero-ctas).
6. BUMP the cache-bust on each page from `?v=10` to `?v=11` (the link tag is
   `<link rel="stylesheet" href="/static/u4_unified.css?v=10">` — change to `?v=11`).
7. Backup each page before editing as `<filename>.bak_w2`.

VERIFY:
  • For each page, run: google-chrome --headless --no-sandbox --disable-gpu \\
       --window-size=1440,900 --screenshot=/tmp/w2_<slug>.png \\
       'https://romantv.net/static/mockups/CATALOG/<page>'
  • Visually confirm: italic gold kicker, big white title, dim desc, 2 CTAs (red primary
    + gold-border secondary). Hero should be roughly the upper 60% of the viewport.
  • Run /root/mxstream_debug/u4_qc_audit.py and confirm no regressions
    (every page still ✓ OK with 1 search visible).

DELIVERABLE:
  • Updated u4_unified.css (with new Wave 2 block clearly demarcated by a comment header)
  • Updated 9 HTML files (canonical class names + cache-bust v=11 + bespoke CSS stripped)
  • Per-page report: bytes-stripped, classes-renamed, bespoke-rules-removed, screenshot path
  • Final summary: "Wave 2 PASS / FAIL"

CONSTRAINTS:
  • Don't break per-tab unique features (live scores, episode pickers, bucket strips, etc.)
  • Don't move or delete the topbar/nav — Wave 1 owns it
  • Don't introduce per-tab CSS overrides that the unified CSS has to fight later
  • Idempotent — running twice should be a no-op
"""

prompt_file = "/tmp/cursor_w2.txt"
out_file = "/tmp/cursor_w2.out"
Path(prompt_file).write_text(CTX)

print(f"Dispatching Cursor with {MODEL} for Wave 2 (will take 6-12 min)...")
cmd = f'{CURSOR} --model {MODEL} --print --force --yolo "$(cat {prompt_file})" > {out_file} 2>&1'
try:
    subprocess.run(["bash", "-c", cmd], timeout=1500)
    print("→ Cursor finished")
except subprocess.TimeoutExpired:
    print("⚠ Cursor timed out — check /tmp/cursor_w2.out")

out = Path(out_file).read_text() if Path(out_file).exists() else "(no output)"
print("\n=== CURSOR OUTPUT (last 100 lines) ===")
print("\n".join(out.split("\n")[-100:]))
