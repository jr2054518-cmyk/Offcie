# RomanTV — Session Log

## Apr 28 - May 1 2026 — Catalog deployment session

### What got built
1. **9-tab catalog mockups → production** (the big move)
2. **Old UI erased** — 12 MB vaulted to `/root/_vault/old_ui_pre_catalog_20260428_1854.tar.gz`
   - 73 `main.py.bak_*` files purged
   - 31 `index.html.bak_*` purged
   - ~50 `app_stremio_core.js.bak_*` purged
   - ~15 `stremio_core.css.bak_*` purged
   - Old SPA `index.html`, `app.js`, `style.css`, `live.html/css/js`
   - 15 intermediate mockup `.html` files
   - All session debug junk
   - Static dir: 55 MB → 39 MB

3. **Phase 3 routes wired** — `main.py` lines 13680-13800
   - `/`, `/movies`, `/series`, `/anime`, `/kids`, `/livetv`, `/sports`, `/esports` → `FileResponse` of corresponding production HTML
   - `/premium-tv` → feature-flag gated (404 anon, 200 with `user_features.adult_18plus=1`)

4. **Phase 4 data piping** — `/static/phase4_catalog_pipes.js`
   - Fetches `/api/rows?tab=...`, `/api/featured/picks`, `/api/anime/schedule`, `/api/of/creators`
   - Replaces placeholder tile content with real Nigma VOD, TMDB, Coomer data
   - Sets `data-pipe-status="live|empty|error|placeholder-only"` on each row
   - Health: `/api/_pipe_health` (mxstream-app), `/warroom/api/catalog_pipelines` (kalshi-dashboard)

5. **OF creator seeding** — 110 top OnlyFans creators starred:
   - 100 GLOBAL (top by Coomer favorited count: belledelphine, sweetiefox_of, hannahowo, etc.)
   - 5 MX (karelyruizoficial, karely76, yerimua, shantal420, celialoraoficial)
   - 4 US (bellathorne, larsapippen, demirose, amouranth)
   - 1 BR (andressaurach)
   - 1 UK (ellieleen1)
   - Table: `of_creators_starred(slug, service, country, rank)`
   - Note: marlene2995 NOT on Coomer (only on direct OnlyFans)

### Bug fixes shipped this session

| # | Bug | Fix | Cache |
|---|---|---|---|
| 1 | Pseudo-element `::-webkit-scrollbar` only attached to LAST selector → topbar `display:none` on every tab | Distributed pseudo across all 9 selectors via `desc()` helper | v=8 → v=9 |
| 2 | `.h1-navtab.is-active` red-pill leftover (Cursor missed child class) | Stripped from series HTML | v=6 → v=7 |
| 3 | Sports inline `<span>ACTIVE</span>` text | Removed | v=7 → v=8 |
| 4 | 14 active-class aliases (Home `is-on`, Esports `es1-active` etc.) | Extended unified CSS active selectors | v=10 |
| 5 | Search bars doubled (Movies/Live TV had own sibling `<span>` icons) | Stripped sibling icons + their CSS rules from both | v=11 |
| 6 | 18+ had body-level `<form class=search-wide>` duplicate | Removed both occurrences | v=12 |
| 7 | Esports had fake `<div class=es1-search>` placeholder, not real `<input>` | Replaced with real `<input type=search>` form | v=12 |
| 8 | Live TV hero dim/ghosted (missing `.lt-hero-head` wrapper) | Added wrapper, content layered correctly | v=13 |
| 9 | 6 of 9 tabs had undersized hero titles (32-40px instead of 64-84px) — bespoke per-tab `.hero-title` rules winning over unified | Stripped per-tab font-size rules in each | v=14 |
| 10 | Tiles rendered 1289×1993 (no width constraint) — JS missed `.tile--poster` modifier | Added `.tile--poster` class in JS pipe | v=18→19 |
| 11 | Rail containers `.rv-rail` rendered as `display:block` not flex | Added `display:flex; flex-direction:row; overflow-x:auto` to rail selectors | v=19→20 |
| 12 | ES duplicate content in `movies.html` (chip-row + provider-row + continue-watching duplicated for stripped lang-es wrapper) | `strip_es_dup.py` removed the duplicate blocks | v=21 |
| 13 | `section.design { min-height: 100vh }` forcing 800-1200px gap below hero | Override `min-height: auto !important` | v=21→22 |
| 14 | Hero touching chips with 0px gap | Added `margin-bottom: 32px` to hero | v=22 |
| 15 | Hero description truncated to 1 line via `white-space: nowrap` | Changed to `-webkit-line-clamp: 3 / max-width: 90ch / white-space: normal` | v=23 |
| 16 | Cursor's pull-quote pseudo-element clipped behind poster | Removed pull-quote `::after` rule | v=24→25 |
| 17 | Home rotating spotlight desync — title locked on "Project Hail Mary" while bg cycled (JS queried `.v1a-hero-title` but Wave 2 renamed to `.hero-title`) | Updated JS selectors: `.hero-title`, `.hero-desc`, `.btn-primary`, `.btn-secondary` | v=26 |

### Open / partial
- **Topbar nav doesn't navigate** — all 9 tabs have `<a href="#">` or `<button onclick=toast()>` placeholders instead of `<a href="/movies">` etc. **NOT YET FIXED**
- **Series + Anime hero column layout** — may still be misaligned on certain viewports (verified Movies works as reference; others may need re-test)
- **Mobile + TV box** — not yet verified for any tab
- **Continue Watching tile heights** — inconsistent on Home (some 16:9, some weird)
- **"View queue" button position** on Home hero — floats orphaned, needs better placement

### Session screenshots saved
On netcup VPS:
- `/tmp/w1_AFTER_*.png` (5 — Wave 1 verification)
- `/tmp/w2_*.png`, `/tmp/wv2h_*.png`, `/tmp/w2_2_*.png` (Wave 2 + hardening + dim fix)
- `/tmp/w3_*.png` (Wave 3 verification)
- `/tmp/p3_*.png` (Phase 3 deploy verification)
- `/tmp/polish_*.png`, `/tmp/hero_v25.png` (Wave 4 polish)
- `/tmp/v17_*.png` through `/tmp/v25_*.png` (cache-bust iteration screenshots)
- `/static/u4_compare/*.png` (gallery — Juan-accessible)

Gallery URL (Juan-accessible): `https://romantv.net/static/u4_compare/v10.html`

### Backups saved on VPS
- `/root/_vault/old_ui_pre_catalog_20260428_1854.tar.gz` — 12 MB, all old UI files
- `*.bak_freshstart` — Cursor's Wave 1 strip backups (per catalog HTML file)
- `*.bak_w2`, `*.bak_w2_fix_2`, `*.bak_w2_dim_fix`, `*.bak_w2_dim_fix_es`, `*.bak_w2_harden` — Wave 2 backups
- `*.bak_w3` — Wave 3 strip backups
- `*.bak_phase3` — Phase 3 deploy backups (mockup before strip)
- `*.bak_phase4` — Phase 4 backups
- `*.bak_es_strip` — duplicate-strip backups
- `*.bak_stale_selectors` — stale selector fix backups
