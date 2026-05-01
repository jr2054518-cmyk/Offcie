#!/usr/bin/env python3
"""u4 Wave 3 — UNIFIED TILES + CHIPS across 9 tabs.

Builds on Wave 1 (topbar) + Wave 2 (hero) without breaking either.

Visible problems Wave 3 must fix:
  • Live TV "Also live right now" sub-row cards show oversized truncated
    titles (Noticier..., TUDN..., Las...) — Wave 2 hero-title bleeds into them
  • Each tab uses bespoke tile classes (.movie-card / .h1-poster / .a1b-tile /
    .lt-channel / .sp1-fixture / .es1-match-card / .creator-tile / .k4-thumb)
  • Each tab uses bespoke chip classes (filter pills, age chips, region pills,
    audio chips, language toggles)
"""
import subprocess
from pathlib import Path

CURSOR = "/root/.local/bin/cursor-agent"
MODEL = "auto"

CTX = """RomanTV catalog Wave 3 — UNIFIED TILES + CHIPS across 9 tabs.

CONTEXT:
Waves 1 (topbar) + 2 (hero) shipped + verified. /root/mxstream-app/static/u4_unified.css
(cache-bust v=15) is the SINGLE source of truth for topbar + hero.
Per Juan's "fresh-start" rule: strip bespoke per-tab CSS, do not layer overrides.

═══════════════════════════════════════════════════════════════════
GOAL — Wave 3
═══════════════════════════════════════════════════════════════════
Apply ONE canonical tile + chip vocabulary to all 9 catalog pages so:
  • All movie/series/anime/kids posters use .tile.tile--poster
  • All channel/sports/esports landscape cards use .tile.tile--landscape
  • All creator avatars use .tile.tile--square
  • All filter/age/region/audio/language pills use .chip (with .is-active)

═══════════════════════════════════════════════════════════════════
SPEC — append to /root/mxstream-app/static/u4_unified.css under
"Wave 3 — Unified Tiles + Chips" header
═══════════════════════════════════════════════════════════════════

/* TILE base */
.tile {
  position: relative; display: block; border-radius: 16px !important;
  background: var(--panel2); border: 1px solid var(--line);
  overflow: hidden; cursor: pointer;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
  text-decoration: none; color: inherit;
}
.tile:hover, .tile:focus-visible {
  transform: translateY(-6px) !important;
  border-color: rgba(255, 214, 107, 0.6) !important;
  box-shadow: 0 12px 32px rgba(0,0,0,0.5), 0 0 0 4px rgba(255, 214, 107, 0.4) !important;
  outline: none !important;
}
.tile__media { position: relative; width: 100%; background: var(--panel); }
.tile__media img { width: 100%; height: 100%; display: block; object-fit: cover; }
.tile__body { padding: 12px 14px; }
.tile-title {
  font: 600 14px/1.3 -apple-system, sans-serif !important;
  color: var(--text) !important;
  margin: 0 0 4px !important;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
.tile-meta {
  font: 500 12px/1.2 -apple-system, sans-serif !important;
  color: var(--dim) !important;
  margin: 0 !important;
}

/* TILE variants */
.tile--poster      { aspect-ratio: 2/3 / auto; width: 160px; }
.tile--poster .tile__media { aspect-ratio: 2/3; }
.tile--landscape   { width: 320px; }
.tile--landscape .tile__media { aspect-ratio: 16/9; }
.tile--square      { width: 200px; }
.tile--square .tile__media   { aspect-ratio: 1/1; }

/* CHIP */
.chip {
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  height: 52px !important;
  padding: 0 18px !important;
  border-radius: 999px !important;
  border: 1px solid var(--line) !important;
  background: transparent !important;
  color: var(--text) !important;
  font: 600 14px/1 -apple-system, sans-serif !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  transition: background .15s, border-color .15s, color .15s !important;
  text-decoration: none !important;
}
.chip:hover { background: rgba(255, 255, 255, 0.08) !important; border-color: var(--dim) !important; }
.chip.is-active, .chip.active, .chip[aria-pressed="true"], .chip.is-on, .chip.on {
  background: rgba(255, 214, 107, 0.15) !important;
  border-color: var(--gold) !important;
  color: var(--gold) !important;
}
.chip__icon { font-size: 16px; line-height: 1; }
.chip__count { font-size: 11px; color: var(--dim); margin-left: 4px; padding: 2px 6px; background: rgba(255,255,255,0.08); border-radius: 999px; }

/* MOBILE @max-width 480 */
@media (max-width: 480px) {
  .tile--poster    { width: 120px; }
  .tile--landscape { width: 240px; }
  .tile--square    { width: 140px; }
  .chip            { height: 44px !important; padding: 0 14px !important; font-size: 13px !important; }
}
/* TV @min-width 1920 */
@media (min-width: 1920px) {
  .tile--poster    { width: 220px; }
  .tile--landscape { width: 420px; }
  .tile--square    { width: 280px; }
  .chip            { height: 60px !important; padding: 0 22px !important; font-size: 16px !important; }
}

═══════════════════════════════════════════════════════════════════
PER-TAB ALIASES — make unified rules win over bespoke selectors
═══════════════════════════════════════════════════════════════════
Add these alias selectors so existing class names also pick up unified styles
WITHOUT requiring HTML rewrites:

.tile, .v1a-tile, .rv-poster, .h1-poster, .a1b-tile, .k4-thumb,
.lt-channel-card, .sp1-fixture, .es1-match-card, .creator-tile,
.movie-card, .show-card, .program-card, .channel-card, .match-card { /* tile base */ }

.chip, .v1a-chip, .rv-chip, .h1-chip, .a1b-chip, .k4-chip, .lt-pill, .lt-chip,
.sp1-chip, .es1-chip, .filter-pill, .audio-chip, .age-chip, .region-pill,
.lang-toggle, .genre-pill { /* chip base */ }

═══════════════════════════════════════════════════════════════════
STRIP BESPOKE RULES (per Juan's fresh-start rule)
═══════════════════════════════════════════════════════════════════
For each of the 9 catalog HTML files at /root/mxstream-app/static/mockups/CATALOG/,
inspect the inline <style> blocks and STRIP rules that:
  • Set border-radius / aspect-ratio / dimensions on tile/poster/card classes
    (Wave 3 unified now owns these)
  • Set hover transforms / box-shadows on tile classes (unified owns)
  • Set chip dimensions / padding / radius / colors (unified owns)
  • Set active-state styling on chips (unified .chip.is-active wins now)
KEEP rules that:
  • Set per-tab UNIQUE coloring (e.g. Kids age-chip palette: peach/teal/blue
    -- this is intentional Kids palette, KEEP IT but only for the
    .k4-chip[data-age="X"].is-active variants which don't conflict with
    unified .chip.is-active gold)
  • Set bespoke per-bucket styling (Sports sport-color borders, Live TV
    EPG strip, Esports tournament-tier badges)

═══════════════════════════════════════════════════════════════════
SPECIFIC FIX — Live TV "Also live right now" sub-row card title bleed
═══════════════════════════════════════════════════════════════════
File: /root/mxstream-app/static/mockups/CATALOG/livetv_APPROVED_lt1.html

The "Also live right now · top picks" sub-row currently shows TOP NEWS / TOP
SPORTS / TOP NOVELA cards where the title text is rendered at hero-title
size (72px) instead of tile-title size (14px). Reason: those cards reuse
the .hero-title class internally.

Fix: change those card headlines from <h2 class="hero-title"> to
<h3 class="tile-title">. The card kicker (TOP NEWS etc) should be class
"tile-meta" not "hero-kicker". The card should use .tile.tile--landscape.

Apply to both lang-en + lang-es copies.

═══════════════════════════════════════════════════════════════════
ALSO BUMP cache-bust on each page from `?v=15` to `?v=16` (whatever's there).
═══════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════
VERIFY GATES (must check each before declaring PASS):
═══════════════════════════════════════════════════════════════════
For each of the 9 tabs:
  1. Visit page in chrome --headless at 1440x900
  2. Query computed styles of:
     - first .tile (or .X-tile alias): MUST have border-radius >= 12px
     - first .chip (or alias): MUST have height >= 44px
     - first .chip.is-active: MUST have border-color including gold (close to rgb(255, 214, 107))
  3. For Live TV specifically:
     - .lt-spot-body .tile-title (or whatever the Also-live card title selector is)
       MUST have font-size <= 24px (not 72px)
  4. Take screenshot to /tmp/w3_<slug>.png at 1440x900
  5. Hero from Wave 2 MUST still pass (font-size 56+, color white)
     -- regression check: don't break Wave 2.

DELIVERABLE: /tmp/w3_report.md with the gates printed for each tab + a
final "Wave 3 X of 9 PASS" line. Do NOT declare PASS overall unless all 9
gates pass for tile + chip + Wave 2 regression.

CONSTRAINTS:
- Don't break topbar (Wave 1) or hero (Wave 2) on any tab
- Backups: each file as `*.bak_w3`
- Idempotent
"""
prompt_file = "/tmp/cursor_w3.txt"
out_file = "/tmp/cursor_w3.out"
Path(prompt_file).write_text(CTX)

print(f"Dispatching Cursor with {MODEL} for Wave 3 (will take 8-15 min)...")
cmd = f'{CURSOR} --model {MODEL} --print --force --yolo "$(cat {prompt_file})" > {out_file} 2>&1'
try:
    subprocess.run(["bash", "-c", cmd], timeout=1500)
    print("→ Cursor finished")
except subprocess.TimeoutExpired:
    print("⚠ Cursor timed out — check /tmp/cursor_w3.out")

out = Path(out_file).read_text() if Path(out_file).exists() else "(no output)"
print("\n=== CURSOR OUTPUT (last 100 lines) ===")
print("\n".join(out.split("\n")[-100:]))
