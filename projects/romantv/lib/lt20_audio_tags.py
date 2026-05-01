# PURPOSE: Heuristic audio-tag mapping from Nigma category names → language codes for tile badges
# BUILT_FOR: SPEC LT-20
# ADDED: 2026-04-28
from __future__ import annotations

import logging
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "romantv.db"

router = APIRouter(prefix="/api/audio-tags", tags=["audio-tags"])

_TABLES = ("nigma_vod", "nigma_series")

_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^EN\s*-\s*(?:MANGA|ANIME)", re.I), "ja;en"),
    (re.compile(r"^EN\s*-\s", re.I),                  "en-US"),
    (re.compile(r"^ES\s*-\s", re.I),                   "es-LA;es-ES"),
    (re.compile(r"^MX\s*-\s", re.I),                   "es-MX"),
    (re.compile(r"^DE\s*-\s", re.I),                   "de-DE"),
    (re.compile(r"^FR\s*-\s", re.I),                   "fr-FR"),
    (re.compile(r"^IT\s*-\s", re.I),                   "it-IT"),
    (re.compile(r"^GR\s*-\s", re.I),                   "el-GR"),
    (re.compile(r"^PT/BR[\s-]", re.I),                 "pt-BR"),
    (re.compile(r"^TR\s*-\s", re.I),                   "tr-TR"),
    (re.compile(r"TURKISH|TURKEY|TURKSIH", re.I),      "tr-TR"),
    (re.compile(r"^ENGLISH\b", re.I),                  "en-US"),
    (re.compile(r"^ESPAÑA\b", re.I),                   "es-LA;es-ES"),
    (re.compile(r"^LATINO\b", re.I),                   "es-LA"),
    (re.compile(r"^FRANCE\b", re.I),                   "fr-FR"),
    (re.compile(r"^GERMAN[YE]\b", re.I),               "de-DE"),
    (re.compile(r"^GREECE\b|^GREEK\b", re.I),          "el-GR"),
    (re.compile(r"^ITALY\b", re.I),                    "it-IT"),
    (re.compile(r"^NEDERLAND|^NETHERLANDS\b", re.I),   "nl-NL"),
]


def _classify(category_name: str) -> Optional[str]:
    if not category_name:
        return None
    for pattern, tag in _RULES:
        if pattern.search(category_name):
            return tag
    return None


def _connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    conn = _connect(db_path)
    try:
        for table in _TABLES:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN audio_tags TEXT DEFAULT NULL")
                conn.commit()
                log.info("Added audio_tags column to %s", table)
            except sqlite3.OperationalError:
                pass
    finally:
        conn.close()


def rebuild_audio_tags(db_path: Optional[str] = None) -> dict[str, Any]:
    conn = _connect(db_path)
    t0 = time.monotonic()
    total = 0
    try:
        for table in _TABLES:
            cats = [r[0] for r in conn.execute(
                f"SELECT DISTINCT category_name FROM {table}"
            ).fetchall()]
            for cat in cats:
                tag = _classify(cat)
                if tag is not None:
                    cur = conn.execute(
                        f"UPDATE {table} SET audio_tags = ? "
                        f"WHERE category_name IS ? AND (audio_tags IS NULL OR audio_tags != ?)",
                        (tag, cat, tag),
                    )
                else:
                    cur = conn.execute(
                        f"UPDATE {table} SET audio_tags = NULL "
                        f"WHERE category_name IS ? AND audio_tags IS NOT NULL",
                        (cat,),
                    )
                total += cur.rowcount
            conn.commit()
    finally:
        conn.close()
    ms = round((time.monotonic() - t0) * 1000)
    log.info("audio-tags rebuild: %d rows updated in %d ms", total, ms)
    return {"rows_updated": total, "ms": ms}


@router.post("/rebuild")
def api_rebuild() -> dict[str, Any]:
    result = rebuild_audio_tags()
    return result


@router.get("/title/{title_id}")
def api_title_tags(title_id: int) -> dict[str, Any]:
    conn = _connect()
    try:
        for table in _TABLES:
            row = conn.execute(
                f"SELECT id, name, category_name, audio_tags FROM {table} WHERE id = ?",
                (title_id,),
            ).fetchone()
            if row:
                raw = row["audio_tags"] or ""
                tags = [t for t in raw.split(";") if t]
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "category_name": row["category_name"],
                    "table": table,
                    "audio_tags": tags,
                }
    finally:
        conn.close()
    raise HTTPException(status_code=404, detail="title not found")


def _boot() -> None:
    try:
        init_db()
        rebuild_audio_tags()
    except Exception:
        log.exception("lt20 audio-tags boot failed")


threading.Thread(target=_boot, daemon=True, name="lt20-audio-tags-boot").start()
