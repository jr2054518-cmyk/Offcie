#!/usr/bin/env python3
"""u4 Phase 4 — pipe backend feeds into catalog + add v6 pipeline panels.

Two deliverables in one pass:
  A) Replace placeholder content in static/{index,movies,series,anime,kids,
     livetv,sports,esports,premium-tv}.html with REAL data fetched from
     existing backend APIs. JS-side fetch + replace.
  B) Add new War Room v6 panels showing each catalog tab → which pipe(s)
     feed it, last-fetch timestamps, and counts.
"""
import subprocess
from pathlib import Path

CURSOR = "/root/.local/bin/cursor-agent"
MODEL = "auto"

CTX = """RomanTV Phase 4 — pipe backend feeds INTO new catalog + add v6 pipeline panels.

CONTEXT:
Phase 3 just deployed 9 catalog HTML pages at /root/mxstream-app/static/:
  index.html, movies.html, series.html, anime.html, kids.html,
  livetv.html, sports.html, esports.html, premium-tv.html

They serve via routes / /movies /series /anime /kids /livetv /sports
/esports /premium-tv. All return 200 (premium-tv 404 anon — feature-gated).

PROBLEM: each tab still shows HARD-CODED placeholder content (e.g.
"Project Hail Mary", "Breaking Bad", static channel names). We need to
swap placeholder content for REAL data from the existing backend APIs.

═══════════════════════════════════════════════════════════════════
PART A — DATA PIPING (per-tab JS fetchers)
═══════════════════════════════════════════════════════════════════
For each catalog HTML page, ADD a <script> at the bottom of <body> that:
  1. fetch()s the relevant existing /api/... endpoint(s)
  2. replaces the placeholder rows with real tile data
  3. preserves the unified .tile / .tile-title / .tile-meta classes

Existing API endpoints to use (verified via grep on main.py):

  /api/rows                        # generic row endpoint — pass tab=movies/series/anime/kids
                                   # returns rows of { rowTitle, items: [{ id, title, poster, year, ... }] }
  /api/discover/catalogs           # list available catalogs
  /api/discover                    # discover items
  /api/featured/picks              # featured picks (hero rotation)
  /api/featured                    # general featured
  /api/anime/schedule              # anime upcoming episodes
  /api/of/creators                 # OF creators (powering /premium-tv)
  /api/livetv/now                  # what's-on-now multiplex (search main.py
                                   # for actual route name — could be
                                   # /api/livetv or /livetv-now etc; use grep)

If a tab has multiple rows, fetch each row's data and replace its tile
container's innerHTML. If an endpoint doesn't exist for a tab, leave the
placeholder and add a `data-pipe-status="placeholder-only"` attribute on
the row so the v6 dashboard can flag it.

Per-tab pipe map (your hint — verify by reading main.py):
  index.html (Home)        — /api/featured/picks (hero), /api/rows?tab=home (rows)
  movies.html              — /api/rows?tab=movies
  series.html              — /api/rows?tab=series
  anime.html               — /api/anime/schedule + /api/rows?tab=anime
  kids.html                — /api/rows?tab=kids (filter by family-safe)
  livetv.html              — /api/livetv/now + iptv-org streams
  sports.html              — /api/sports (sports_feed.py likely has the route)
  esports.html             — /api/esports (esports_feed.py)
  premium-tv.html          — /api/of/creators + /api/of-files/{handle}

Strategy:
  1. Open each page, identify each row container by its existing class
     (e.g. .v1a-row-rail, .rv-row-rail, .h1-rail, .a1b-rail, .k4-row,
     .lt-now-rail, .sp1-feed, .es1-bracket, .of-rail)
  2. Append a <script> at end of body that:
     - fetches the right endpoint
     - on success, clears the row's innerHTML and rebuilds with .tile
       elements bound to real items
     - on error / 404 / empty, leaves the placeholder + adds
       `data-pipe-status="placeholder-only"` to the row container
  3. Use the same .tile / .tile__media / .tile__body / .tile-title /
     .tile-meta classes from /static/u4_unified.css so styling is
     unchanged
  4. Tile click handler: window.location = `/detail/{type}/{id}` for
     real items; toast() for placeholder (existing handler stays)

Pseudocode pattern (one row):
  async function pipeRow(rowSelector, endpoint, mapItemFn) {
    const row = document.querySelector(rowSelector);
    if (!row) return;
    try {
      const r = await fetch(endpoint, { credentials: 'include' });
      if (!r.ok) throw new Error(r.status);
      const data = await r.json();
      const items = Array.isArray(data) ? data : (data.items || []);
      if (items.length === 0) {
        row.dataset.pipeStatus = 'empty';
        return;
      }
      row.innerHTML = items.slice(0, 20).map(mapItemFn).join('');
      row.dataset.pipeStatus = 'live';
    } catch (e) {
      row.dataset.pipeStatus = 'error:' + e.message;
    }
  }

Bump cache-bust on each catalog HTML's <link rel=stylesheet
href=/static/u4_unified.css?v=18> to v=19 to force browser refresh.

═══════════════════════════════════════════════════════════════════
PART B — WAR ROOM V6 CATALOG PIPELINES PANEL
═══════════════════════════════════════════════════════════════════
The War Room dashboard at /warroom/v6 has a panel registry at
/root/syndicate/config/panel_registry.json (per memory).

ADD new panels to that registry showing the Phase 3+4 catalog pipeline:

  Panel ID: `catalog_pipelines`
  Section: "Catalog Pipelines (Phase 3-4)"
  For each of 9 tabs, show:
    - tab name
    - route URL (/movies, /series, etc)
    - feeding pipes (list of /api/... endpoints + Nigma/TMDB/iptv-org/LT-17/18/21/22 sources)
    - row count ("8 rows configured")
    - last successful fetch (when did the page last get data — track via
      timestamp in /api/_pipe_health endpoint that we'll create)
    - status: green (live) / yellow (some rows empty) / red (all rows broken)

  Also create /api/warroom/catalog_pipelines that returns this status JSON.

The panel HTML/JS goes in dashboard.py (the warroom server). Per memory:
  • Dashboard restart needed: `systemctl restart kalshi-dashboard` after dashboard.py changes
  • War Room v6 lives at https://romantv.net/warroom/v6 (or similar — verify)

If panel_registry.json or the warroom dashboard is in a different repo
(e.g. /root/syndicate/), do the v6 work there. Backups: `*.bak_phase4`.

═══════════════════════════════════════════════════════════════════
VERIFY GATES (must PASS before declaring done):
═══════════════════════════════════════════════════════════════════
  1. For each of 9 catalog HTML files, count <script> tags that fetch
     /api/... — must be >= 1 per tab (Premium-TV may be more)
  2. curl each catalog route (with valid login cookie) and confirm
     200. Then via headless chrome with `--virtual-time-budget=4000`,
     screenshot at 1440x900. The tile rows should show REAL items
     (not the hardcoded placeholders).
  3. curl /api/warroom/catalog_pipelines and confirm JSON returns
     status for all 9 tabs.
  4. Visit https://romantv.net/warroom/v6 (or the actual path) and
     verify the new "Catalog Pipelines" panel appears.

REPORT to /tmp/phase4_report.md:
  - Per-tab: which endpoint(s) wired, status (LIVE/EMPTY/ERROR), screenshot path
  - Whether v6 panel deployed + screenshot
  - Final verdict: "Phase 4: PASS / FAIL — <reason>"

CONSTRAINTS:
  - Do NOT remove the placeholder content (only swap it out client-side
    via JS) — if a fetch fails, placeholder stays as fallback
  - Do NOT break the unified u4 styles — keep .tile / .chip / .hero-* classes
  - Backups: each touched HTML as `*.bak_phase4`
  - Idempotent
"""

prompt_file = "/tmp/cursor_phase4.txt"
out_file = "/tmp/cursor_phase4.out"
Path(prompt_file).write_text(CTX)

print(f"Dispatching Cursor with {MODEL} for Phase 4 (data pipe + v6 panels) — 15-25 min...")
cmd = f'{CURSOR} --model {MODEL} --print --force --yolo "$(cat {prompt_file})" > {out_file} 2>&1'
try:
    subprocess.run(["bash", "-c", cmd], timeout=2400)
    print("→ Cursor finished")
except subprocess.TimeoutExpired:
    print("⚠ Cursor timed out — check /tmp/cursor_phase4.out")

out = Path(out_file).read_text() if Path(out_file).exists() else "(no output)"
print("\n=== CURSOR OUTPUT (last 120 lines) ===")
print("\n".join(out.split("\n")[-120:]))
