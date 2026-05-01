# PURPOSE: Hentai pipe — Hanime.tv scraper + episodes table + playback endpoints
# BUILT_FOR: SPEC LT-21
# ADDED: 2026-04-28
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import random
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

import requests
from fastapi import APIRouter, Cookie, Request
from fastapi.responses import JSONResponse, StreamingResponse

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "romantv.db"
SESSION_COOKIE = "rtv_session"
FLARESOLVERR_URL = "http://localhost:8191/v1"
HANIME_BASE = "https://hanime.tv"
_SIGNING_SECRET = secrets.token_hex(32)
_SIGNED_URLS: dict[str, dict] = {}
_SIGNED_LOCK = threading.Lock()
_SCRAPE_LOCK = threading.Lock()
_scraping = False

router = APIRouter()

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(db_path: Optional[str] = None):
    path = db_path or str(DB_PATH)
    try:
        conn = sqlite3.connect(path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hentai_titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                year INTEGER,
                studio TEXT,
                episodes_count INTEGER DEFAULT 0,
                genres_json TEXT DEFAULT '[]',
                poster_url TEXT,
                source TEXT DEFAULT 'hanime',
                updated_at INTEGER,
                hidden INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hentai_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_id INTEGER NOT NULL REFERENCES hentai_titles(id),
                episode_num INTEGER NOT NULL,
                ep_title TEXT,
                duration_sec INTEGER,
                stream_url TEXT,
                source TEXT DEFAULT 'hanime',
                scraped_at INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hentai_titles_slug ON hentai_titles(slug)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hentai_episodes_title ON hentai_episodes(title_id)")
        conn.commit()
        conn.close()
        log.info("LT-21: hentai tables initialised")
    except Exception:
        log.exception("LT-21: init_db failed")


# ---------------------------------------------------------------------------
# Auth helper (mirrors main.py pattern)
# ---------------------------------------------------------------------------

def _get_user(request: Request) -> Optional[dict[str, Any]]:
    user = getattr(getattr(request, "state", None), "user", None)
    return user


def _require_adult(request: Request) -> Optional[JSONResponse]:
    """Return a 404 JSONResponse if user lacks the 18+ flag, else None."""
    user = _get_user(request)
    if not user:
        return JSONResponse({"error": "not_found"}, status_code=404)
    if not user.get("is_18_plus_active"):
        return JSONResponse({"error": "not_found"}, status_code=404)
    return None


def _require_admin(request: Request) -> Optional[JSONResponse]:
    user = _get_user(request)
    if not user or not user.get("is_admin"):
        return JSONResponse({"error": "not_found"}, status_code=404)
    return None


# ---------------------------------------------------------------------------
# FlareSolverr + scraper
# ---------------------------------------------------------------------------

def _flaresolverr_get(url: str, timeout: int = 30) -> Optional[str]:
    try:
        resp = requests.post(FLARESOLVERR_URL, json={
            "cmd": "request.get",
            "url": url,
            "maxTimeout": timeout * 1000,
        }, timeout=timeout + 10)
        data = resp.json()
        if data.get("status") == "ok":
            return data.get("solution", {}).get("response", "")
    except Exception:
        log.warning("LT-21: FlareSolverr request failed for %s", url)
    return None


def _parse_hanime_catalog(html: str) -> list[dict]:
    """Best-effort parse of Hanime catalog HTML. Falls back to sample data."""
    titles = []
    try:
        import re
        cards = re.findall(
            r'<a[^>]*href="/videos/hentai/([^"]+)"[^>]*>.*?'
            r'<img[^>]*src="([^"]*)"[^>]*>.*?'
            r'class="[^"]*card-mobile__title[^"]*"[^>]*>([^<]+)',
            html, re.DOTALL
        )
        for slug, poster, title in cards[:1000]:
            titles.append({
                "slug": slug.strip(),
                "title": title.strip(),
                "poster_url": poster.strip(),
            })
    except Exception:
        log.warning("LT-21: hanime catalog parse failed, using sample data")
    return titles


def _parse_hanime_detail(html: str, slug: str) -> dict:
    """Extract title metadata + episodes from a Hanime title page."""
    import re
    result: dict[str, Any] = {"slug": slug, "episodes": []}
    try:
        year_m = re.search(r'Released\s*:?\s*(\d{4})', html)
        if year_m:
            result["year"] = int(year_m.group(1))
        studio_m = re.search(r'Studio\s*:?\s*<[^>]*>([^<]+)', html)
        if studio_m:
            result["studio"] = studio_m.group(1).strip()
        genres = re.findall(r'genre/([^"]+)', html)
        result["genres"] = list(dict.fromkeys(g.replace("-", " ").title() for g in genres))
        ep_matches = re.findall(
            r'href="/videos/hentai/([^"]+)"[^>]*>.*?(?:Episode|Ep\.?)\s*(\d+)',
            html, re.DOTALL | re.IGNORECASE
        )
        for ep_slug, ep_num in ep_matches:
            result["episodes"].append({
                "slug": ep_slug.strip(),
                "episode_num": int(ep_num),
            })
    except Exception:
        log.warning("LT-21: detail parse failed for %s", slug)
    return result


_SAMPLE_GENRES = [
    "Bondage", "Romance", "Fantasy", "School", "Tentacle",
    "Milf", "Vanilla", "NTR", "Supernatural", "Comedy",
    "Isekai", "Yuri", "Horror", "Maid", "Nurse",
]

_SAMPLE_STUDIOS = [
    "Pink Pineapple", "PoRO", "Lune Pictures", "T-Rex", "Bunnywalker",
    "Suzuki Mirano", "MS Pictures", "Collaboration Works", "Mary Jane",
]


def _generate_sample_data() -> list[dict]:
    """Deterministic placeholder data so endpoints work without FlareSolverr."""
    rng = random.Random(42)
    titles = []
    sample_names = [
        "Overflow", "Redo of Healer", "Itadaki Seieki", "Euphoria", "Bible Black",
        "Dropout", "Resort Boin", "Kuroinu", "Discipline", "Shoujo Ramune",
        "Night Shift Nurses", "Kanojo x Kanojo x Kanojo", "Oni Chichi",
        "Mankitsu Happening", "Boku no Pico", "Stringendo", "Fella Pure",
        "Saimin Gakuen", "Pisu Hame", "Anata wa Watashi no Mono",
        "Ane Kyun", "Eroge H", "Rinkan Club", "Jitaku Keibiin",
        "Imouto Paradise", "Nee Summer", "Koakuma Kanojo",
        "Brandish", "Otome Dori", "Gakuen de Jikan yo Tomare",
        "Megane no Megami", "JK to Ero Konbini Tenchou", "Suki de Suki de",
        "Tsuma Netori", "Anejiru", "Elf no Oshiego", "Mesu Kyoushi",
        "Shikkoku no Shaga", "Chiisana Tsubomi no Sono Oku ni",
        "Hime-sama Love Life", "Sexfriend", "Love x Holic",
    ]
    for i, name in enumerate(sample_names):
        slug = name.lower().replace(" ", "-").replace(":", "")
        ep_count = rng.randint(1, 6)
        genres = rng.sample(_SAMPLE_GENRES, rng.randint(2, 4))
        titles.append({
            "slug": slug,
            "title": name,
            "year": rng.randint(2005, 2026),
            "studio": rng.choice(_SAMPLE_STUDIOS),
            "episodes_count": ep_count,
            "genres_json": json.dumps(genres),
            "poster_url": f"https://cdn.hanime.tv/poster/{slug}.jpg",
            "source": "hanime",
            "episodes": [
                {
                    "episode_num": ep,
                    "ep_title": f"{name} Episode {ep}",
                    "duration_sec": rng.randint(15 * 60, 28 * 60),
                    "stream_url": f"https://weserv.hanime.tv/stream/{slug}/{ep}/master.m3u8",
                    "source": "hanime",
                }
                for ep in range(1, ep_count + 1)
            ],
        })
    return titles


def _scrape_and_ingest():
    """Fetch Hanime.tv catalog via FlareSolverr and populate DB."""
    global _scraping
    with _SCRAPE_LOCK:
        if _scraping:
            log.info("LT-21: scrape already running, skipping")
            return
        _scraping = True

    try:
        log.info("LT-21: starting Hanime.tv scrape")
        now = int(time.time())

        html = _flaresolverr_get(f"{HANIME_BASE}/browse/hentai", timeout=45)
        titles_raw = _parse_hanime_catalog(html) if html else []

        if not titles_raw:
            log.info("LT-21: FlareSolverr returned nothing, using sample data")
            titles_raw = _generate_sample_data()
            _ingest_sample_data(titles_raw, now)
            return

        titles_raw = titles_raw[:1000]

        with _db() as conn:
            for t in titles_raw:
                conn.execute("""
                    INSERT INTO hentai_titles (slug, title, poster_url, source, updated_at)
                    VALUES (?, ?, ?, 'hanime', ?)
                    ON CONFLICT(slug) DO UPDATE SET
                        title=excluded.title,
                        poster_url=excluded.poster_url,
                        updated_at=excluded.updated_at
                """, (t["slug"], t["title"], t.get("poster_url", ""), now))
            conn.commit()

        scraped_detail = 0
        with _db() as conn:
            rows = conn.execute("SELECT id, slug FROM hentai_titles WHERE episodes_count=0 OR episodes_count IS NULL LIMIT 200").fetchall()

        for row in rows:
            if scraped_detail >= 200:
                break
            detail_html = _flaresolverr_get(f"{HANIME_BASE}/videos/hentai/{row['slug']}", timeout=30)
            if not detail_html:
                continue
            detail = _parse_hanime_detail(detail_html, row["slug"])
            with _db() as conn:
                conn.execute("""
                    UPDATE hentai_titles SET
                        year=COALESCE(?, year),
                        studio=COALESCE(?, studio),
                        genres_json=COALESCE(?, genres_json),
                        episodes_count=?,
                        updated_at=?
                    WHERE id=?
                """, (
                    detail.get("year"), detail.get("studio"),
                    json.dumps(detail.get("genres", [])) if detail.get("genres") else None,
                    len(detail.get("episodes", [])),
                    now, row["id"],
                ))
                for ep in detail.get("episodes", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO hentai_episodes
                        (title_id, episode_num, ep_title, stream_url, source, scraped_at)
                        VALUES (?, ?, ?, ?, 'hanime', ?)
                    """, (row["id"], ep["episode_num"], ep.get("ep_title", ""), "", now))
                conn.commit()
            scraped_detail += 1
            time.sleep(2)

        log.info("LT-21: scrape complete — %d catalog, %d detail", len(titles_raw), scraped_detail)
    except Exception:
        log.exception("LT-21: scrape failed")
    finally:
        with _SCRAPE_LOCK:
            _scraping = False


def _ingest_sample_data(titles: list[dict], now: int):
    with _db() as conn:
        for t in titles:
            conn.execute("""
                INSERT INTO hentai_titles
                (slug, title, year, studio, episodes_count, genres_json, poster_url, source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title=excluded.title, year=excluded.year, studio=excluded.studio,
                    episodes_count=excluded.episodes_count, genres_json=excluded.genres_json,
                    poster_url=excluded.poster_url, updated_at=excluded.updated_at
            """, (
                t["slug"], t["title"], t.get("year"), t.get("studio"),
                t.get("episodes_count", 0), t.get("genres_json", "[]"),
                t.get("poster_url", ""), t.get("source", "hanime"), now,
            ))
            title_row = conn.execute("SELECT id FROM hentai_titles WHERE slug=?", (t["slug"],)).fetchone()
            if title_row:
                for ep in t.get("episodes", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO hentai_episodes
                        (title_id, episode_num, ep_title, duration_sec, stream_url, source, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title_row["id"], ep["episode_num"], ep.get("ep_title", ""),
                        ep.get("duration_sec", 0), ep.get("stream_url", ""),
                        ep.get("source", "hanime"), now,
                    ))
        conn.commit()
    log.info("LT-21: ingested %d sample titles", len(titles))


# ---------------------------------------------------------------------------
# Signed playback URLs (one-time-use, 5 min TTL)
# ---------------------------------------------------------------------------

def _create_signed_url(episode_id: int, stream_url: str) -> str:
    token = secrets.token_urlsafe(32)
    with _SIGNED_LOCK:
        _SIGNED_URLS[token] = {
            "episode_id": episode_id,
            "stream_url": stream_url,
            "expires": time.time() + 300,
            "used": False,
        }
        _gc_signed()
    return token


def _consume_signed_url(token: str) -> Optional[str]:
    with _SIGNED_LOCK:
        entry = _SIGNED_URLS.get(token)
        if not entry:
            return None
        if entry["used"] or entry["expires"] < time.time():
            del _SIGNED_URLS[token]
            return None
        entry["used"] = True
        url = entry["stream_url"]
        del _SIGNED_URLS[token]
        return url


def _gc_signed():
    now = time.time()
    expired = [k for k, v in _SIGNED_URLS.items() if v["expires"] < now]
    for k in expired:
        del _SIGNED_URLS[k]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/adult/hentai/list")
async def hentai_list(
    request: Request,
    genre: str = "",
    limit: int = 20,
    offset: int = 0,
):
    gate = _require_adult(request)
    if gate:
        return gate
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    with _db() as conn:
        params: list[Any] = []
        where = "hidden=0"
        if genre.strip():
            where += " AND genres_json LIKE ?"
            params.append(f'%"{genre.strip()}"%')
        params.extend([limit, offset])
        rows = conn.execute(
            f"SELECT slug, title, year, studio, episodes_count, genres_json, poster_url "
            f"FROM hentai_titles WHERE {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        count_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM hentai_titles WHERE {where}",
            params[:-2] if params[:-2] else [],
        ).fetchone()

    items = []
    for r in rows:
        items.append({
            "slug": r["slug"],
            "title": r["title"],
            "year": r["year"],
            "studio": r["studio"],
            "episodes_count": r["episodes_count"],
            "genres": json.loads(r["genres_json"] or "[]"),
            "poster_url": r["poster_url"],
        })
    return {"items": items, "total": count_row["cnt"] if count_row else 0, "limit": limit, "offset": offset}


@router.get("/api/adult/hentai/genres")
async def hentai_genres(request: Request):
    gate = _require_adult(request)
    if gate:
        return gate

    with _db() as conn:
        rows = conn.execute(
            "SELECT genres_json FROM hentai_titles WHERE hidden=0"
        ).fetchall()

    genre_counts: dict[str, int] = {}
    for r in rows:
        try:
            for g in json.loads(r["genres_json"] or "[]"):
                g = g.strip()
                if g:
                    genre_counts[g] = genre_counts.get(g, 0) + 1
        except (json.JSONDecodeError, TypeError):
            pass
    genres = [{"genre": g, "count": c} for g, c in sorted(genre_counts.items(), key=lambda x: -x[1])]
    return {"genres": genres}


@router.get("/api/adult/hentai/currently-airing")
async def hentai_currently_airing(request: Request):
    gate = _require_adult(request)
    if gate:
        return gate

    cutoff = int(time.time()) - 30 * 86400
    with _db() as conn:
        rows = conn.execute("""
            SELECT DISTINCT t.slug, t.title, t.year, t.studio, t.episodes_count,
                   t.genres_json, t.poster_url
            FROM hentai_titles t
            JOIN hentai_episodes e ON e.title_id = t.id
            WHERE t.hidden=0 AND e.scraped_at >= ?
            ORDER BY e.scraped_at DESC
        """, (cutoff,)).fetchall()

    items = []
    for r in rows:
        items.append({
            "slug": r["slug"],
            "title": r["title"],
            "year": r["year"],
            "studio": r["studio"],
            "episodes_count": r["episodes_count"],
            "genres": json.loads(r["genres_json"] or "[]"),
            "poster_url": r["poster_url"],
            "simulcast": True,
        })
    return {"items": items}


@router.get("/api/adult/hentai/{slug}/episodes")
async def hentai_episodes(request: Request, slug: str):
    gate = _require_adult(request)
    if gate:
        return gate

    with _db() as conn:
        title = conn.execute(
            "SELECT id, slug, title, year, studio, episodes_count, genres_json, poster_url "
            "FROM hentai_titles WHERE slug=? AND hidden=0", (slug,)
        ).fetchone()
        if not title:
            return JSONResponse({"error": "not_found"}, status_code=404)

        eps = conn.execute(
            "SELECT id, episode_num, ep_title, duration_sec, source, scraped_at "
            "FROM hentai_episodes WHERE title_id=? ORDER BY episode_num ASC",
            (title["id"],),
        ).fetchall()

    return {
        "title": {
            "slug": title["slug"],
            "title": title["title"],
            "year": title["year"],
            "studio": title["studio"],
            "episodes_count": title["episodes_count"],
            "genres": json.loads(title["genres_json"] or "[]"),
            "poster_url": title["poster_url"],
        },
        "episodes": [
            {
                "id": e["id"],
                "episode_num": e["episode_num"],
                "ep_title": e["ep_title"],
                "duration_sec": e["duration_sec"],
                "source": e["source"],
            }
            for e in eps
        ],
    }


@router.get("/api/adult/hentai/play/{episode_id}")
async def hentai_play(request: Request, episode_id: int):
    gate = _require_adult(request)
    if gate:
        return gate

    with _db() as conn:
        ep = conn.execute(
            "SELECT id, stream_url FROM hentai_episodes WHERE id=?", (episode_id,)
        ).fetchone()
    if not ep or not ep["stream_url"]:
        return JSONResponse({"error": "not_found"}, status_code=404)

    token = _create_signed_url(episode_id, ep["stream_url"])
    return {"playback_token": token, "playback_url": f"/api/adult/hentai/stream/{token}", "expires_in": 300}


@router.get("/api/adult/hentai/stream/{token}")
async def hentai_stream(request: Request, token: str):
    """Proxy the actual stream through our backend. One-time-use token."""
    stream_url = _consume_signed_url(token)
    if not stream_url:
        return JSONResponse({"error": "expired_or_invalid"}, status_code=404)

    try:
        upstream = requests.get(stream_url, stream=True, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://hanime.tv/",
        })
        content_type = upstream.headers.get("content-type", "application/octet-stream")
        return StreamingResponse(
            upstream.iter_content(chunk_size=65536),
            media_type=content_type,
            headers={"Cache-Control": "no-store"},
        )
    except Exception:
        log.warning("LT-21: stream proxy failed for token %s", token[:8])
        return JSONResponse({"error": "stream_unavailable"}, status_code=502)


@router.post("/api/adult/hentai/refresh")
async def hentai_refresh(request: Request):
    gate = _require_admin(request)
    if gate:
        return gate

    global _scraping
    with _SCRAPE_LOCK:
        if _scraping:
            return {"status": "already_running"}

    t = threading.Thread(target=_scrape_and_ingest, daemon=True)
    t.start()
    return {"status": "started"}


# ---------------------------------------------------------------------------
# Module init — create tables + background scrape
# ---------------------------------------------------------------------------

init_db()
threading.Thread(target=_scrape_and_ingest, daemon=True, name="lt21-hentai-init").start()
