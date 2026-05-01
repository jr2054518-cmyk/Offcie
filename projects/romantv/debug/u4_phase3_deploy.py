#!/usr/bin/env python3
"""u4 Phase 3 — DEPLOY new catalog as the canonical RomanTV UI.

After this:
  • Old SPA index.html is gone (already deleted, vaulted)
  • New catalog mockups (9 tabs) are the production UI
  • Routes /, /movies, /series, /anime, /kids, /livetv, /sports, /esports,
    /premium-tv each serve the matching catalog HTML
  • The .cat-bar mockup-only header (with EN/ES toggle + APPROVED pill) is
    stripped — production users don't need it (lang toggle moves into the
    unified topbar / settings)
  • Backend routes still serve their JSON APIs unchanged
"""
import subprocess
from pathlib import Path

CURSOR = "/root/.local/bin/cursor-agent"
MODEL = "auto"

CTX = """RomanTV Phase 3 — DEPLOY new catalog as the canonical UI.

CRITICAL CONTEXT:
We just deleted the old SPA static/index.html (vaulted to
/root/_vault/old_ui_pre_catalog_20260428_1854.tar.gz). Any logged-in user
hitting `/` will now 404 because main.py still calls
`FileResponse(STATIC_DIR / "index.html")`.

The 9 NEW catalog tabs live at:
  /root/mxstream-app/static/mockups/CATALOG/home_APPROVED_v1a.html
  /root/mxstream-app/static/mockups/CATALOG/movies_APPROVED_v1.html
  /root/mxstream-app/static/mockups/CATALOG/series_APPROVED_h1.html
  /root/mxstream-app/static/mockups/CATALOG/anime_APPROVED_a1b.html
  /root/mxstream-app/static/mockups/CATALOG/kids_APPROVED_k4.html
  /root/mxstream-app/static/mockups/CATALOG/livetv_APPROVED_lt1.html
  /root/mxstream-app/static/mockups/CATALOG/sports_APPROVED_sp1.html
  /root/mxstream-app/static/mockups/CATALOG/esports_APPROVED_es1.html
  /root/mxstream-app/static/mockups/CATALOG/adult_APPROVED_eg1v2.html

These are mockup files with a `.cat-bar` mockup-only header at the very top
(small bar saying "★ APPROVED · HOME · v1A · 🇺🇸 ENGLISH / 🇪🇸 ESPAÑOL").
That bar is NOT for production. Strip it.

YOUR JOB — TWO DELIVERABLES:

═══════════════════════════════════════════════════════════════════
1. PRODUCTION HTML — strip .cat-bar from each of the 9 mockups, save as
   production-named files in /root/mxstream-app/static/:
═══════════════════════════════════════════════════════════════════

   home_APPROVED_v1a.html       → static/index.html
   movies_APPROVED_v1.html      → static/movies.html
   series_APPROVED_h1.html      → static/series.html
   anime_APPROVED_a1b.html      → static/anime.html
   kids_APPROVED_k4.html        → static/kids.html
   livetv_APPROVED_lt1.html     → static/livetv.html
   sports_APPROVED_sp1.html     → static/sports.html
   esports_APPROVED_es1.html    → static/esports.html
   adult_APPROVED_eg1v2.html    → static/premium-tv.html

   What to STRIP from each before saving:
     • The <div class="cat-bar"> ... </div> block (the mockup APPROVED
       header) — this includes the brand pill + APPROVED tag + EN/ES
       lang toggle buttons that drive the lang-wrap switching
     • The wrapper script that toggles `lang-wrap.active` based on the
       cat-bar buttons
     • The <div id="lang-es" class="lang-wrap"> entire SECOND copy
       (Spanish) — production should serve EN by default and Spanish via
       a different mechanism (cookie / Accept-Language)
     • The CSS rules `div.lang-wrap { display:none }` and
       `div.lang-wrap.active { display:block }` (no longer needed since
       only the EN copy survives)

   Do NOT strip:
     • The <link rel="stylesheet" href="/static/u4_unified.css?v=…">
       (this is critical — Wave 1+2+3 unified styles)
     • The <header class="X-topbar">…</header>
     • The hero sections (Wave 2)
     • The chip/tile/row sections (Wave 3)
     • Any JS handlers on tile clicks / chip clicks / nav clicks
     • <link rel="manifest"> / <link rel="icon"> if present
     • The `<style>` blocks specific to the page (#v1 etc) — those
       define page-unique styling

   Backup each original mockup as `*.bak_phase3` before stripping.

═══════════════════════════════════════════════════════════════════
2. main.py ROUTES — add/update so each tab is served by FastAPI:
═══════════════════════════════════════════════════════════════════

   File: /root/mxstream-app/main.py

   Find the block around line 13720-13745 that has:
     def _spa_index_file_response(request): ...
     @app.get("/")
     @app.get("/app")
     @app.get("/app/")
     def app_index(request: Request):
         return _spa_index_file_response(request)

   The `_spa_index_file_response` already does login/profile/sub checks and
   returns gate.html for anon — KEEP that logic. Just change the final
   `FileResponse(STATIC_DIR / "index.html")` line to still serve
   STATIC_DIR / "index.html" (which is now the new catalog home).

   ADD new tab routes RIGHT AFTER `app_index`:

     @app.get("/movies")
     @app.get("/movies/")
     def page_movies(request: Request):
         if not getattr(request.state, "user", None):
             return FileResponse(STATIC_DIR / "gate.html")
         return FileResponse(STATIC_DIR / "movies.html")

     @app.get("/series")
     @app.get("/series/")
     def page_series(request: Request):
         if not getattr(request.state, "user", None):
             return FileResponse(STATIC_DIR / "gate.html")
         return FileResponse(STATIC_DIR / "series.html")

     @app.get("/anime")
     @app.get("/anime/")
     def page_anime(request: Request):
         if not getattr(request.state, "user", None):
             return FileResponse(STATIC_DIR / "gate.html")
         return FileResponse(STATIC_DIR / "anime.html")

     @app.get("/kids")
     @app.get("/kids/")
     def page_kids(request: Request):
         if not getattr(request.state, "user", None):
             return FileResponse(STATIC_DIR / "gate.html")
         return FileResponse(STATIC_DIR / "kids.html")

     @app.get("/livetv")
     @app.get("/livetv/")
     def page_livetv(request: Request):
         if not getattr(request.state, "user", None):
             return FileResponse(STATIC_DIR / "gate.html")
         return FileResponse(STATIC_DIR / "livetv.html")

     @app.get("/sports")
     @app.get("/sports/")
     def page_sports(request: Request):
         if not getattr(request.state, "user", None):
             return FileResponse(STATIC_DIR / "gate.html")
         return FileResponse(STATIC_DIR / "sports.html")

     @app.get("/esports")
     @app.get("/esports/")
     def page_esports(request: Request):
         if not getattr(request.state, "user", None):
             return FileResponse(STATIC_DIR / "gate.html")
         return FileResponse(STATIC_DIR / "esports.html")

     @app.get("/premium-tv")
     @app.get("/premium-tv/")
     def page_premium_tv(request: Request):
         # 18+ tab — gated by adult_18plus feature flag (already in user_features)
         user = getattr(request.state, "user", None)
         if not user:
             return FileResponse(STATIC_DIR / "gate.html")
         # Check feature flag
         try:
             from fastapi import HTTPException
             with _db() as conn:
                 row = conn.execute(
                     "SELECT 1 FROM user_features WHERE user_id=? AND feature='adult_18plus' AND enabled=1",
                     (int(user["id"]),)
                 ).fetchone()
             if not row:
                 raise HTTPException(status_code=404)
         except Exception:
             raise HTTPException(status_code=404)
         return FileResponse(STATIC_DIR / "premium-tv.html")

   Don't break existing routes. The /detail/movie, /detail/series,
   /detail/anime SPA routes still exist — leave them alone for now (they
   point to the missing index.html — Phase 4 will replace with proper
   detail pages).

═══════════════════════════════════════════════════════════════════
3. RESTART + VERIFY:
═══════════════════════════════════════════════════════════════════

   sudo systemctl restart mxstream-app

   Then verify each route:
     for path in "" movies series anime kids livetv sports esports; do
       code=$(curl -sL -o /dev/null -w "%{http_code}" "https://romantv.net/$path")
       echo "/$path → $code"
     done
     # /premium-tv requires feature flag — expect 404 anonymously

   For each route returning 200, also screenshot at 1440x900:
     google-chrome --headless --no-sandbox --disable-gpu --window-size=1440,900 \\
       --screenshot=/tmp/p3_<route>.png 'https://romantv.net/<route>'

   Expected:
     /            → 200, anon → gate.html | logged-in → home catalog
     /movies      → 200, anon → gate.html | logged-in → movies catalog
     /series      → 200, anon → gate.html | logged-in → series catalog
     ...
     /premium-tv  → 404 unless user has adult_18plus flag

═══════════════════════════════════════════════════════════════════
4. REPORT
═══════════════════════════════════════════════════════════════════

   Write /tmp/phase3_report.md with:
     - bytes-stripped per file (original size → new production size)
     - which lang block was kept (EN)
     - new main.py routes added (count)
     - per-route status code from curl
     - per-route screenshot path
     - any errors

Constraints:
  • Don't break existing API endpoints
  • Don't break the anon → gate.html flow
  • Don't break /account, /profiles/picker, /admin/* routes
  • Backups: each original as *.bak_phase3

When done, return a final line: "Phase 3 deploy: PASS" or "FAIL — <reason>"
"""

prompt_file = "/tmp/cursor_phase3.txt"
out_file = "/tmp/cursor_phase3.out"
Path(prompt_file).write_text(CTX)

print(f"Dispatching Cursor with {MODEL} for Phase 3 deploy (will take 10-15 min)...")
cmd = f'{CURSOR} --model {MODEL} --print --force --yolo "$(cat {prompt_file})" > {out_file} 2>&1'
try:
    subprocess.run(["bash", "-c", cmd], timeout=1500)
    print("→ Cursor finished")
except subprocess.TimeoutExpired:
    print("⚠ Cursor timed out — check /tmp/cursor_phase3.out")

out = Path(out_file).read_text() if Path(out_file).exists() else "(no output)"
print("\n=== CURSOR OUTPUT (last 100 lines) ===")
print("\n".join(out.split("\n")[-100:]))
