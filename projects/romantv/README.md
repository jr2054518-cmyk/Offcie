# RomanTV — Project State Snapshot

**What it is:** Private family streaming app at https://romantv.net
**Backend:** FastAPI on netcup VPS — `/root/mxstream-app/` port 7006 (uvicorn)
**Database:** SQLite WAL mode at `/root/mxstream-app/data/romantv.db`
**Service:** `systemctl restart mxstream-app.service`
**Family users:** Juan (id 9034) · Dyana (9040, wife) · Mateo (9043, son)

---

## Current State (as of last sync — see SESSION_LOG for date)

### Catalog (9 tabs) — DEPLOYED + PIPED
Routes live in production:
- `/` → Home (rotating spotlight + Continue Watching)
- `/movies` → Movies (TMDB/Cinemeta/Nigma)
- `/series` → Series (Resume-First)
- `/anime` → Anime (Latin-Am dub focus)
- `/kids` → Kids (Family-Watch + Age chips)
- `/livetv` → Live TV (channel grid + EPG)
- `/sports` → Sports (LIVE-NOW WALL + multiplex)
- `/esports` → Esports (Tournament-Centric, GRID/PandaScore/bo3)
- `/premium-tv` → 18+ (Creators/Hentai/Tube — feature-flagged via `user_features.adult_18plus`)

All 8 routes return 200 for logged-in users · `/premium-tv` returns 404 anon (correctly gated).

### Unified design system
Single source of truth: `/static/u4_unified.css` (cache-bust `?v=26`)
- **Wave 1**: top-bar across all tabs (single magnifier, gold underline on active tab)
- **Wave 2**: hero (italic gold kicker + bold white title + 3-line desc + 2-3 CTAs)
- **Wave 3**: tiles + chips (`.tile.tile--poster` 160px, `.chip` 52px gold-active)
- **Wave 4**: hero polish (32px breathing margin, hero-poster prominence)

### Data piping
`/static/phase4_catalog_pipes.js` injects real backend data into placeholder rows on each catalog page:
- Movies/Series/Anime/Kids → `/api/rows?tab=<slug>` (Nigma VOD + TMDB)
- Anime → `/api/anime/schedule` + rows
- Premium TV → `/api/of/creators` (Coomer 328k index + 110 starred top creators per country)
- Health endpoint: `/api/_pipe_health`

### War Room v6 panel
- `/warroom/api/catalog_pipelines` (auth-gated, served by kalshi-dashboard on :9999)
- `panel_registry.json` updated with "Catalog Pipelines (Phase 3-4)" section

---

## Files in this snapshot

```
projects/romantv/
├── README.md                       # this file
├── SESSION_LOG.md                  # detailed log of work done
├── BUGS_OPEN.md                    # known open issues
├── catalog/                        # production HTML + CSS + JS
│   ├── index.html                  # Home
│   ├── movies.html, series.html, anime.html, kids.html
│   ├── livetv.html, sports.html, esports.html, premium-tv.html
│   ├── u4_unified.css              # Wave 1+2+3+4 unified styles
│   └── phase4_catalog_pipes.js     # data fetcher
├── lib/                            # backend modules (LT-17..22)
│   ├── lt17_title_dedup.py         # canonical title mapping (133k titles)
│   ├── lt18_track_picker.py        # audio/sub auto-pick (es-MX → a1 Latino)
│   ├── lt19_region_detect.py       # CF-IPCountry → region bucket
│   ├── lt20_audio_tags.py          # heuristic audio_tags column
│   ├── lt21_hentai.py              # Hanime.tv via FlareSolverr
│   └── lt22_tube.py                # Erome + Fapello scrapers
├── backend_routes_snippet.py       # FastAPI route block (lines 13680-13800 of main.py)
└── debug/                          # all my session scripts
    ├── u4_wave1_topbar_v2.py
    ├── u4_w2_hero_dispatch.py
    ├── u4_w2_harden.py
    ├── u4_w3_tiles_chips.py
    ├── u4_phase3_deploy.py
    ├── u4_phase4_pipe_v6.py
    ├── seed_top_of_per_country.py  # 110 starred OF creators
    ├── strip_es_dup.py             # remove duplicate ES content
    └── ... (Cursor dispatchers + audit scripts)
```

---

## Backend integration points

- **Main.py routes:** see `backend_routes_snippet.py` for the new tab routes added at line 13680+
- **DB tables:** `users`, `profiles`, `user_features`, `of_creators`, `of_creators_index` (328,068 rows), `of_creators_starred` (110 rows GLOBAL+MX+US+UK+BR), `nigma_vod`, `nigma_series`, etc.
- **Service file:** `/root/mxstream-app/mxstream-app.service` (systemd)
- **Cache rules:** every change to `u4_unified.css` requires bumping `?v=NN` across all 9 catalog HTML files

---

## OPEN ISSUES — see BUGS_OPEN.md

Critical (functional):
- Topbar nav tabs don't navigate (use mockup `<button onclick=toast()>` instead of real `<a href>`) — **fix dispatched but not yet verified**

Visual (per device):
- Hero rotation now correctly cycles title+desc+image (Wave 2.7 fix, verified live)
- Sports + Live TV heroes promoted to full-width
- Series + Anime hero columns may still be misaligned on certain viewports
- Mobile + TV box layouts NOT YET VERIFIED for all tabs

---

## How to resume this work

1. From any device with this repo cloned: `cd projects/romantv`
2. SSH into netcup: `ssh netcup` (key auth)
3. Working directory on VPS: `/root/mxstream-app`
4. Debug scripts: `/root/mxstream_debug/`
5. Logs: `journalctl -u mxstream-app -f` (live mxstream-app logs)
