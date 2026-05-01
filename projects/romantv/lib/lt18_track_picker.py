# PURPOSE: Audio/subtitle track auto-picker — selects best track per user lang/region pref
# BUILT_FOR: SPEC LT-18
# ADDED: 2026-04-28
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/track", tags=["track-picker"])

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "romantv.db"

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    p = db_path or str(DB_PATH)
    try:
        with sqlite3.connect(p, timeout=5.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_lang_pref (
                    user_id   INTEGER PRIMARY KEY,
                    audio_lang TEXT NOT NULL DEFAULT 'es-MX',
                    sub_lang   TEXT NOT NULL DEFAULT 'es-MX',
                    region     TEXT NOT NULL DEFAULT 'MX'
                )
            """)
            conn.commit()
        log.info("LT-18 user_lang_pref table ready")
    except Exception:
        log.exception("LT-18 init_db failed")


init_db()

# ---------------------------------------------------------------------------
# Priority chains
# ---------------------------------------------------------------------------

_PRIORITY: dict[str, dict[str, list[str]]] = {
    "es-MX": {
        "audio":    ["es-MX", "es-LA", "es-ES", "en-US", "_original"],
        "subtitle": ["es-MX", "es-LA", "es-ES", "en-US", "_none"],
    },
    "es-LA": {
        "audio":    ["es-LA", "es-MX", "es-ES", "en-US", "_original"],
        "subtitle": ["es-LA", "es-MX", "es-ES", "en-US", "_none"],
    },
    "es-ES": {
        "audio":    ["es-ES", "es-LA", "es-MX", "en-US", "_original"],
        "subtitle": ["es-ES", "es-LA", "es-MX", "en-US", "_none"],
    },
    "en-US": {
        "audio":    ["en-US", "en-GB", "_original"],
        "subtitle": ["en-US", "_none"],
    },
    "en-GB": {
        "audio":    ["en-GB", "en-US", "_original"],
        "subtitle": ["en-GB", "en-US", "_none"],
    },
}


def _build_chain(user_lang: str, kind: str) -> list[str]:
    """Build priority chain for a lang/kind combo. Falls back to generic logic."""
    key = user_lang.strip()
    preset = _PRIORITY.get(key, {}).get(kind)
    if preset:
        return list(preset)

    lang_base = key.split("-")[0].lower()
    if kind == "audio":
        return [key, lang_base, "en-US", "_original"]
    return [key, lang_base, "en-US", "_none"]


def _normalize(val: str) -> str:
    return (val or "").strip().lower()


def _track_tag(t: dict) -> str:
    """Canonical lang-REGION tag for a track, e.g. 'es-MX'."""
    lang = (t.get("lang") or "").strip()
    region = (t.get("region") or "").strip()
    if region:
        return f"{lang}-{region}"
    return lang


def pick_tracks(
    user_lang: str,
    tracks: list[dict[str, Any]],
) -> dict[str, Any]:
    audio_tracks = [t for t in tracks if _normalize(t.get("kind")) == "audio"]
    sub_tracks = [t for t in tracks if _normalize(t.get("kind")) == "subtitle"]

    audio_chain = _build_chain(user_lang, "audio")
    sub_chain = _build_chain(user_lang, "subtitle")

    audio_pick = _select(audio_tracks, audio_chain)
    sub_pick = _select(sub_tracks, sub_chain)

    fallback_ids: list[str] = []
    for chain, pool in [(audio_chain, audio_tracks), (sub_chain, sub_tracks)]:
        for tag in chain:
            if tag.startswith("_"):
                continue
            for t in pool:
                tid = str(t.get("id", ""))
                if tid and tid not in fallback_ids:
                    tt = _normalize(_track_tag(t))
                    tag_n = _normalize(tag)
                    if tt == tag_n or tt.startswith(tag_n + "-") or tt.split("-")[0] == tag_n:
                        fallback_ids.append(tid)

    return {
        "audio_pick_id": audio_pick,
        "subtitle_pick_id": sub_pick,
        "fallback_chain": fallback_ids,
    }


def _select(pool: list[dict], chain: list[str]) -> Optional[str]:
    if not pool:
        return None

    for tag in chain:
        if tag == "_original":
            for t in pool:
                if _normalize(t.get("label", "")).find("original") != -1:
                    return str(t["id"])
            return str(pool[-1]["id"])
        if tag == "_none":
            return None

        tag_n = _normalize(tag)
        tag_base = tag_n.split("-")[0]

        for t in pool:
            if _normalize(_track_tag(t)) == tag_n:
                return str(t["id"])

        if "-" in tag_n:
            for t in pool:
                if _normalize(_track_tag(t)).split("-")[0] == tag_base:
                    return str(t["id"])

    return str(pool[0]["id"]) if pool else None

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/pick")
async def track_pick(body: dict = Body(...)):
    user_lang = body.get("user_lang")
    tracks = body.get("tracks")
    if not user_lang or not isinstance(tracks, list):
        raise HTTPException(status_code=400, detail="user_lang (str) and tracks (list) required")
    return pick_tracks(user_lang, tracks)


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: int):
    with _db() as conn:
        row = conn.execute(
            "SELECT audio_lang, sub_lang, region FROM user_lang_pref WHERE user_id=?",
            (user_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="no preferences saved")
    return {"user_id": user_id, "audio_lang": row["audio_lang"], "sub_lang": row["sub_lang"], "region": row["region"]}


@router.post("/preferences")
async def set_preferences(body: dict = Body(...)):
    user_id = body.get("user_id")
    audio_lang = body.get("audio_lang", "es-MX")
    sub_lang = body.get("sub_lang", "es-MX")
    region = body.get("region", "MX")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    with _db() as conn:
        conn.execute(
            "INSERT INTO user_lang_pref (user_id, audio_lang, sub_lang, region) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET audio_lang=excluded.audio_lang, "
            "sub_lang=excluded.sub_lang, region=excluded.region",
            (int(user_id), audio_lang, sub_lang, region),
        )
        conn.commit()
    return {"ok": True, "user_id": user_id, "audio_lang": audio_lang, "sub_lang": sub_lang, "region": region}
