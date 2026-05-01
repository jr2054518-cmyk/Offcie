# PURPOSE: Auto-detect user region from CF-IPCountry, cache per-user, serve lang/audio/chip defaults
# BUILT_FOR: SPEC LT-19
# ADDED: 2026-04-28
from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)

router = APIRouter()

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "romantv.db"

# ── country → (region_bucket, lang_default, audio_pref) ──

_COUNTRY_MAP: dict[str, tuple[str, str, str]] = {
    "US": ("us",    "en", "en-US"),
    "MX": ("mx",    "es", "es-MX"),
    "GB": ("us",    "en", "en-GB"),
    "ES": ("es",    "es", "es-ES"),
}

_LATAM_CODES = frozenset({
    "AR", "CO", "CL", "PE", "EC", "VE", "HN", "PY", "CR",
    "GT", "PR", "BO", "SV", "NI", "PA", "UY", "CU", "DO",
})

_DEFAULT_BUCKET = ("other", "en", "en-US")

# region_bucket → default content chip
_CHIP_MAP: dict[str, str] = {
    "us":    "us-american",
    "mx":    "latam",
    "latam": "latam",
    "es":    "spain",
    "other": "us-american",
}


def _resolve_country(cc: str) -> tuple[str, str, str]:
    cc = (cc or "").strip().upper()
    if cc in _COUNTRY_MAP:
        return _COUNTRY_MAP[cc]
    if cc in _LATAM_CODES:
        return ("latam", "es", "es-LA")
    return _DEFAULT_BUCKET


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    p = db_path or str(DB_PATH)
    try:
        conn = sqlite3.connect(p, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_region_cache (
                user_id          INTEGER PRIMARY KEY,
                country_code     TEXT,
                region_bucket    TEXT,
                lang_default     TEXT,
                audio_pref       TEXT,
                detected_at      INTEGER,
                manual_override  INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
        log.info("user_region_cache table ready")
    except Exception:
        log.exception("init_db failed for user_region_cache")


def _get_user(request: Request) -> Optional[dict[str, Any]]:
    return getattr(request.state, "user", None)


def _cached_region(user_id: int) -> Optional[dict[str, Any]]:
    with _db() as conn:
        row = conn.execute(
            "SELECT country_code, region_bucket, lang_default, audio_pref, manual_override "
            "FROM user_region_cache WHERE user_id=?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return dict(row)


def _upsert_region(user_id: int, cc: str, bucket: str, lang: str, audio: str, manual: int = 0) -> None:
    now = int(time.time())
    with _db() as conn:
        conn.execute(
            "INSERT INTO user_region_cache (user_id, country_code, region_bucket, lang_default, audio_pref, detected_at, manual_override) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "country_code=excluded.country_code, region_bucket=excluded.region_bucket, "
            "lang_default=excluded.lang_default, audio_pref=excluded.audio_pref, "
            "detected_at=excluded.detected_at, manual_override=excluded.manual_override",
            (user_id, cc, bucket, lang, audio, now, manual),
        )
        conn.commit()


# ── endpoints ──

@router.get("/api/region/detect")
async def region_detect(request: Request):
    user = _get_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=404)

    user_id = int(user["id"])

    cached = _cached_region(user_id)
    if cached and cached.get("manual_override"):
        return {
            "country_code": cached["country_code"],
            "region_bucket": cached["region_bucket"],
            "lang_default": cached["lang_default"],
            "audio_pref": cached["audio_pref"],
            "source": "manual_override",
        }

    cf_country = (request.headers.get("CF-IPCountry") or "").strip().upper()
    if not cf_country or len(cf_country) != 2:
        if cached:
            return {
                "country_code": cached["country_code"],
                "region_bucket": cached["region_bucket"],
                "lang_default": cached["lang_default"],
                "audio_pref": cached["audio_pref"],
                "source": "cached",
            }
        cf_country = "US"

    bucket, lang, audio = _resolve_country(cf_country)

    if not cached or not cached.get("manual_override"):
        _upsert_region(user_id, cf_country, bucket, lang, audio, manual=0)

    return {
        "country_code": cf_country,
        "region_bucket": bucket,
        "lang_default": lang,
        "audio_pref": audio,
        "source": "cf-ipcountry",
    }


@router.post("/api/region/override")
async def region_override(request: Request):
    user = _get_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=404)

    user_id = int(user["id"])
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid_body"}, status_code=400)

    bucket = (body.get("region_bucket") or "").strip().lower()
    lang = (body.get("lang_default") or "").strip().lower()
    audio = (body.get("audio_pref") or "").strip()

    valid_buckets = {"us", "mx", "latam", "es", "other"}
    valid_langs = {"en", "es"}
    valid_audio = {"en-US", "en-GB", "es-MX", "es-LA", "es-ES"}

    if bucket not in valid_buckets:
        return JSONResponse({"error": "invalid_region_bucket", "valid": sorted(valid_buckets)}, status_code=400)
    if lang not in valid_langs:
        return JSONResponse({"error": "invalid_lang_default", "valid": sorted(valid_langs)}, status_code=400)
    if audio not in valid_audio:
        return JSONResponse({"error": "invalid_audio_pref", "valid": sorted(valid_audio)}, status_code=400)

    cached = _cached_region(user_id)
    cc = cached["country_code"] if cached else "XX"

    _upsert_region(user_id, cc, bucket, lang, audio, manual=1)
    log.info("region override user=%d bucket=%s lang=%s audio=%s", user_id, bucket, lang, audio)

    return {"ok": True, "region_bucket": bucket, "lang_default": lang, "audio_pref": audio, "manual_override": True}


@router.get("/api/region/lineup-default")
async def region_lineup_default(request: Request):
    user = _get_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=404)

    user_id = int(user["id"])
    cached = _cached_region(user_id)

    if cached:
        bucket = cached["region_bucket"]
    else:
        cf_country = (request.headers.get("CF-IPCountry") or "").strip().upper()
        if cf_country and len(cf_country) == 2:
            bucket, _, _ = _resolve_country(cf_country)
        else:
            bucket = "other"

    chip = _CHIP_MAP.get(bucket, "us-american")
    return {"region_bucket": bucket, "default_chip": chip}


init_db()
