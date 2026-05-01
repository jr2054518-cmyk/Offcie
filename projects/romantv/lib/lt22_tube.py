# PURPOSE: Erome + Fapello scrapers → tube_clips / tube_models tables + adult tube API
# BUILT_FOR: SPEC LT-22
# ADDED: 2026-04-28
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
import sqlite3
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any, Optional

import requests
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)

router = APIRouter()

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "romantv.db"
_SIGN_SECRET = secrets.token_hex(32)
_SIGN_TTL_S = 300

_CATEGORIES = [
    "latina", "milf", "teen", "amateur", "pov",
    "casting", "cosplay", "fetish", "couples", "solo",
]

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
_SCRAPE_LOCK = threading.Lock()
_SCRAPE_RUNNING = False

EROME_CLIP_LIMIT = 5000
EROME_MODEL_LIMIT = 2000
FAPELLO_MODEL_LIMIT = 3000


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


def init_db(db_path: Optional[str] = None) -> None:
    if db_path:
        global DB_PATH
        DB_PATH = Path(db_path)
    try:
        with _db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tube_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    source TEXT,
                    country TEXT,
                    follower_estimate INTEGER,
                    last_seen_at INTEGER,
                    hidden INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tube_clips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER REFERENCES tube_models(id),
                    slug TEXT UNIQUE NOT NULL,
                    title TEXT,
                    source TEXT,
                    duration_sec INTEGER,
                    view_count INTEGER DEFAULT 0,
                    thumb_url TEXT,
                    stream_url TEXT,
                    tags_json TEXT,
                    posted_at INTEGER,
                    scraped_at INTEGER
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tc_source ON tube_clips(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tc_views ON tube_clips(view_count DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tc_model ON tube_clips(model_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tc_posted ON tube_clips(posted_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tm_source ON tube_models(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tm_slug ON tube_models(slug)")
            conn.commit()
        log.info("LT-22 tube tables ready")
    except Exception:
        log.exception("LT-22 init_db failed")


# ---------------------------------------------------------------------------
# Auth gate
# ---------------------------------------------------------------------------

def _gate_user(request: Request) -> Optional[dict]:
    user = getattr(request.state, "user", None)
    if not user:
        return None
    if not user.get("is_18_plus_active"):
        return None
    return user


def _denied() -> JSONResponse:
    return JSONResponse({"error": "not_found"}, status_code=404)


# ---------------------------------------------------------------------------
# Signed playback URLs
# ---------------------------------------------------------------------------

def _sign_url(clip_id: int) -> str:
    expires = int(time.time()) + _SIGN_TTL_S
    payload = f"{clip_id}:{expires}"
    sig = hmac.new(_SIGN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{clip_id}?exp={expires}&sig={sig}"


def _verify_sig(clip_id: int, exp: int, sig: str) -> bool:
    if int(time.time()) > exp:
        return False
    payload = f"{clip_id}:{exp}"
    expected = hmac.new(_SIGN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(sig, expected)


# ---------------------------------------------------------------------------
# Scraper: Erome
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: int = 15) -> Optional[str]:
    try:
        r = requests.get(url, headers={"User-Agent": _UA}, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception as exc:
        log.debug("HTTP GET %s failed: %s", url, exc)
    return None


def _scrape_erome(conn: sqlite3.Connection) -> tuple[int, int]:
    now = int(time.time())
    clips_added = 0
    models_added = 0

    for page in range(1, 51):
        if clips_added >= EROME_CLIP_LIMIT:
            break
        html = _http_get(f"https://www.erome.com/?page={page}")
        if not html:
            break

        album_urls = re.findall(r'href="(https://www\.erome\.com/a/[A-Za-z0-9_-]+)"', html)
        seen = set()
        for album_url in album_urls:
            if album_url in seen or clips_added >= EROME_CLIP_LIMIT:
                continue
            seen.add(album_url)
            slug = album_url.rsplit("/", 1)[-1]

            ahtml = _http_get(album_url)
            if not ahtml:
                continue

            title_m = re.search(r'<title>([^<]+)</title>', ahtml)
            title = title_m.group(1).strip() if title_m else slug

            user_m = re.search(r'href="https://www\.erome\.com/([^"/?]+)"[^>]*class="[^"]*username', ahtml)
            model_slug = user_m.group(1).strip() if user_m else None

            model_id = None
            if model_slug and models_added < EROME_MODEL_LIMIT:
                existing = conn.execute(
                    "SELECT id FROM tube_models WHERE slug=? AND source='erome'", (model_slug,)
                ).fetchone()
                if existing:
                    model_id = existing["id"]
                    conn.execute(
                        "UPDATE tube_models SET last_seen_at=? WHERE id=?", (now, model_id)
                    )
                else:
                    cur = conn.execute(
                        "INSERT OR IGNORE INTO tube_models (slug, display_name, source, last_seen_at) "
                        "VALUES (?, ?, 'erome', ?)",
                        (model_slug, model_slug, now),
                    )
                    if cur.lastrowid:
                        model_id = cur.lastrowid
                        models_added += 1

            thumb_m = re.search(r'<img[^>]+src="(https://[^"]+\.(?:jpg|jpeg|png|webp))"[^>]*class="[^"]*album', ahtml)
            thumb = thumb_m.group(1) if thumb_m else None

            vid_m = re.search(r'<source\s+src="(https://[^"]+\.mp4[^"]*)"', ahtml)
            stream = vid_m.group(1) if vid_m else None

            views_m = re.search(r'(\d[\d,]*)\s*(?:views|vistas)', ahtml, re.I)
            views = int(views_m.group(1).replace(",", "")) if views_m else 0

            tags = []
            for cat in _CATEGORIES:
                if cat in ahtml.lower():
                    tags.append(cat)

            try:
                conn.execute(
                    "INSERT OR IGNORE INTO tube_clips "
                    "(model_id, slug, title, source, view_count, thumb_url, stream_url, "
                    " tags_json, scraped_at) "
                    "VALUES (?, ?, ?, 'erome', ?, ?, ?, ?, ?)",
                    (model_id, f"erome_{slug}", title, views, thumb, stream,
                     json.dumps(tags) if tags else None, now),
                )
                clips_added += 1
            except sqlite3.IntegrityError:
                pass

        conn.commit()

    return clips_added, models_added


# ---------------------------------------------------------------------------
# Scraper: Fapello
# ---------------------------------------------------------------------------

def _scrape_fapello(conn: sqlite3.Connection) -> int:
    now = int(time.time())
    models_added = 0

    for page in range(1, 101):
        if models_added >= FAPELLO_MODEL_LIMIT:
            break
        html = _http_get(f"https://fapello.com/top-creators/{page}/")
        if not html:
            break

        links = re.findall(r'href="https://fapello\.com/([a-zA-Z0-9._-]+)/?"', html)
        if not links:
            break

        for model_slug in links:
            if models_added >= FAPELLO_MODEL_LIMIT:
                break
            if model_slug in ("top-creators", "trending", "new", "popular", "login", "register"):
                continue

            existing = conn.execute(
                "SELECT id FROM tube_models WHERE slug=? AND source='fapello'", (model_slug,)
            ).fetchone()
            if existing:
                conn.execute("UPDATE tube_models SET last_seen_at=? WHERE id=?", (now, existing["id"]))
                continue

            display = model_slug.replace("-", " ").replace("_", " ").title()

            follower_m = None
            detail = _http_get(f"https://fapello.com/{model_slug}/")
            if detail:
                fm = re.search(r'(\d[\d,.]*)\s*(?:followers|seguidores)', detail, re.I)
                if fm:
                    raw = fm.group(1).replace(",", "").replace(".", "")
                    try:
                        follower_m = int(raw)
                    except ValueError:
                        pass

            try:
                conn.execute(
                    "INSERT OR IGNORE INTO tube_models "
                    "(slug, display_name, source, follower_estimate, last_seen_at) "
                    "VALUES (?, ?, 'fapello', ?, ?)",
                    (model_slug, display, follower_m, now),
                )
                models_added += 1
            except sqlite3.IntegrityError:
                pass

        conn.commit()

    return models_added


# ---------------------------------------------------------------------------
# Background scrape
# ---------------------------------------------------------------------------

def _run_scrape() -> None:
    global _SCRAPE_RUNNING
    with _SCRAPE_LOCK:
        if _SCRAPE_RUNNING:
            return
        _SCRAPE_RUNNING = True
    try:
        with _db() as conn:
            existing = conn.execute("SELECT COUNT(*) AS c FROM tube_clips").fetchone()["c"]
            if existing > 100:
                log.info("LT-22 tube already has %d clips, skipping initial scrape", existing)
                return
        log.info("LT-22 starting initial tube scrape")
        with _db() as conn:
            ec, em = _scrape_erome(conn)
            log.info("LT-22 erome: %d clips, %d models", ec, em)
        with _db() as conn:
            fm = _scrape_fapello(conn)
            log.info("LT-22 fapello: %d models", fm)
        log.info("LT-22 initial scrape complete")
    except Exception:
        log.exception("LT-22 scrape failed")
    finally:
        with _SCRAPE_LOCK:
            _SCRAPE_RUNNING = False


def _start_background_scrape() -> None:
    t = threading.Thread(target=_run_scrape, daemon=True, name="lt22-tube-scrape")
    t.start()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/adult/tube/clips/list")
async def tube_clips_list(
    request: Request,
    category: str = Query("", alias="category"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not _gate_user(request):
        return _denied()
    q = "SELECT id, slug, title, source, duration_sec, view_count, thumb_url, tags_json, posted_at FROM tube_clips WHERE 1=1"
    params: list[Any] = []
    if category:
        cat_lower = category.strip().lower()
        q += " AND tags_json LIKE ?"
        params.append(f'%"{cat_lower}"%')
    q += " ORDER BY view_count DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with _db() as conn:
        rows = conn.execute(q, params).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM tube_clips" +
            (" WHERE tags_json LIKE ?" if category else ""),
            ([f'%"{category.strip().lower()}"%'] if category else []),
        ).fetchone()["c"]
    return {
        "clips": [
            {
                "id": r["id"],
                "slug": r["slug"],
                "title": r["title"],
                "source": r["source"],
                "duration_sec": r["duration_sec"],
                "view_count": r["view_count"],
                "thumb_url": r["thumb_url"],
                "tags": json.loads(r["tags_json"]) if r["tags_json"] else [],
                "posted_at": r["posted_at"],
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/api/adult/tube/models/list")
async def tube_models_list(
    request: Request,
    country: str = Query("", alias="country"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not _gate_user(request):
        return _denied()
    q = "SELECT id, slug, display_name, source, country, follower_estimate, last_seen_at FROM tube_models WHERE hidden=0"
    params: list[Any] = []
    if country:
        q += " AND country=?"
        params.append(country.strip().upper())
    q += " ORDER BY follower_estimate DESC NULLS LAST LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with _db() as conn:
        rows = conn.execute(q, params).fetchall()
        count_q = "SELECT COUNT(*) AS c FROM tube_models WHERE hidden=0"
        count_p: list[Any] = []
        if country:
            count_q += " AND country=?"
            count_p.append(country.strip().upper())
        total = conn.execute(count_q, count_p).fetchone()["c"]
    return {
        "models": [
            {
                "id": r["id"],
                "slug": r["slug"],
                "display_name": r["display_name"],
                "source": r["source"],
                "country": r["country"],
                "follower_estimate": r["follower_estimate"],
                "last_seen_at": r["last_seen_at"],
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/api/adult/tube/model/{slug}/clips")
async def tube_model_clips(
    request: Request,
    slug: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not _gate_user(request):
        return _denied()
    with _db() as conn:
        model = conn.execute(
            "SELECT id, slug, display_name, source FROM tube_models WHERE slug=? AND hidden=0",
            (slug,),
        ).fetchone()
        if not model:
            return JSONResponse({"error": "model_not_found"}, status_code=404)
        rows = conn.execute(
            "SELECT id, slug, title, source, duration_sec, view_count, thumb_url, tags_json, posted_at "
            "FROM tube_clips WHERE model_id=? ORDER BY view_count DESC LIMIT ? OFFSET ?",
            (model["id"], limit, offset),
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM tube_clips WHERE model_id=?", (model["id"],)
        ).fetchone()["c"]
    return {
        "model": {
            "id": model["id"],
            "slug": model["slug"],
            "display_name": model["display_name"],
            "source": model["source"],
        },
        "clips": [
            {
                "id": r["id"],
                "slug": r["slug"],
                "title": r["title"],
                "source": r["source"],
                "duration_sec": r["duration_sec"],
                "view_count": r["view_count"],
                "thumb_url": r["thumb_url"],
                "tags": json.loads(r["tags_json"]) if r["tags_json"] else [],
                "posted_at": r["posted_at"],
            }
            for r in rows
        ],
        "total": total,
    }


@router.get("/api/adult/tube/play/{clip_id}")
async def tube_play(
    request: Request,
    clip_id: int,
    exp: Optional[int] = Query(None),
    sig: Optional[str] = Query(None),
):
    if not _gate_user(request):
        return _denied()

    if exp is not None and sig is not None:
        if not _verify_sig(clip_id, exp, sig):
            return JSONResponse({"error": "link_expired"}, status_code=403)
        with _db() as conn:
            row = conn.execute(
                "SELECT stream_url, thumb_url, title FROM tube_clips WHERE id=?", (clip_id,)
            ).fetchone()
        if not row or not row["stream_url"]:
            return JSONResponse({"error": "clip_not_found"}, status_code=404)
        return {"stream_url": row["stream_url"], "title": row["title"], "thumb_url": row["thumb_url"]}

    with _db() as conn:
        row = conn.execute("SELECT id, title, thumb_url FROM tube_clips WHERE id=?", (clip_id,)).fetchone()
    if not row:
        return JSONResponse({"error": "clip_not_found"}, status_code=404)
    signed = _sign_url(clip_id)
    return {
        "clip_id": row["id"],
        "title": row["title"],
        "thumb_url": row["thumb_url"],
        "play_url": f"/api/adult/tube/play/{signed}",
        "expires_in_sec": _SIGN_TTL_S,
    }


@router.get("/api/adult/tube/categories")
async def tube_categories(request: Request):
    if not _gate_user(request):
        return _denied()
    with _db() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM tube_clips").fetchone()["c"]
        cats = []
        for cat in _CATEGORIES:
            cnt = conn.execute(
                "SELECT COUNT(*) AS c FROM tube_clips WHERE tags_json LIKE ?",
                (f'%"{cat}"%',),
            ).fetchone()["c"]
            cats.append({"name": cat, "count": cnt})
    return {"categories": cats, "total_clips": total}


@router.get("/api/adult/tube/trending")
async def tube_trending(
    request: Request,
    window: str = Query("24h"),
    limit: int = Query(30, ge=1, le=100),
):
    if not _gate_user(request):
        return _denied()
    hours = 168 if window == "7d" else 24
    cutoff = int(time.time()) - (hours * 3600)
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, slug, title, source, duration_sec, view_count, thumb_url, tags_json, posted_at, scraped_at "
            "FROM tube_clips WHERE scraped_at >= ? ORDER BY view_count DESC LIMIT ?",
            (cutoff, limit),
        ).fetchall()
    return {
        "window": window,
        "clips": [
            {
                "id": r["id"],
                "slug": r["slug"],
                "title": r["title"],
                "source": r["source"],
                "duration_sec": r["duration_sec"],
                "view_count": r["view_count"],
                "thumb_url": r["thumb_url"],
                "tags": json.loads(r["tags_json"]) if r["tags_json"] else [],
                "posted_at": r["posted_at"],
            }
            for r in rows
        ],
    }


@router.post("/api/adult/tube/refresh")
async def tube_refresh(request: Request):
    user = _gate_user(request)
    if not user:
        return _denied()
    if not (user.get("is_owner") or user.get("is_admin")):
        return JSONResponse({"error": "not_found"}, status_code=404)
    if _SCRAPE_RUNNING:
        return {"status": "already_running"}
    _start_background_scrape()
    return {"status": "started"}


# ---------------------------------------------------------------------------
# Init on import
# ---------------------------------------------------------------------------

init_db()
_start_background_scrape()
