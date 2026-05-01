# PURPOSE: Canonical-title mapping — groups regional duplicates under one ID
# BUILT_FOR: SPEC LT-17
# ADDED: 2026-04-28
from __future__ import annotations

import logging
import re
import sqlite3
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "romantv.db"

router = APIRouter(prefix="/api/canonical", tags=["canonical"])

# ── region prefix patterns ────────────────────────────────────────────
# Matches "ES - ", "EN - ", "DE - ", "IN-EN - ", "PT/BR - ", "MX - ", "NF - ", "SC - " etc.
_REGION_PREFIX_RE = re.compile(
    r"^([A-Z]{2,3}(?:[/-][A-Z]{2,3})?)\s*[-–]\s*",
    re.IGNORECASE,
)
# Year suffix: "(2024)", "(2025)", trailing "2024"
_YEAR_SUFFIX_RE = re.compile(r"\s*\(?\b((?:19|20)\d{2})\b\)?\s*$")
# All non-alphanumeric (for normalized_key)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9 ]+")
_MULTI_SPACE_RE = re.compile(r"\s+")

# Category-based region extraction: "ESPAÑA NETFLIX" → "ES", "EN - SERIES NETFLIX" → "EN"
_CATEGORY_REGION_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^ESPAÑA\b", re.I), "ES"),
    (re.compile(r"^NORDIC\b", re.I), "NORDIC"),
]


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
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
            CREATE TABLE IF NOT EXISTS title_canonical_map (
                canonical_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_title TEXT NOT NULL,
                canonical_year  INTEGER,
                canonical_kind  TEXT,
                normalized_key  TEXT NOT NULL UNIQUE,
                created_at      INTEGER DEFAULT (unixepoch())
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS title_canonical_link (
                canonical_id  INTEGER NOT NULL REFERENCES title_canonical_map(canonical_id),
                source_table  TEXT NOT NULL,
                source_id     TEXT NOT NULL,
                region_label  TEXT,
                PRIMARY KEY (canonical_id, source_table, source_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tcl_source ON title_canonical_link(source_table, source_id)")
        conn.commit()
        conn.close()
        log.info("LT-17: title_canonical_map + title_canonical_link tables ready")
    except Exception:
        log.exception("LT-17: init_db failed")


def _extract_region(name: str, category: str) -> Optional[str]:
    """Extract 2-3 letter region code from name prefix or category."""
    m = _REGION_PREFIX_RE.match(name)
    if m:
        return m.group(1).upper()
    for pat, code in _CATEGORY_REGION_MAP:
        if pat.search(category or ""):
            return code
    cat_m = _REGION_PREFIX_RE.match(category or "")
    if cat_m:
        return cat_m.group(1).upper()
    return None


def _strip_title(name: str) -> str:
    """Remove region prefix from title for display."""
    return _REGION_PREFIX_RE.sub("", name).strip()


def _normalize_key(name: str) -> str:
    """Build a normalized key: strip prefix, year, punctuation, lowercase, collapse spaces."""
    s = _REGION_PREFIX_RE.sub("", name)
    s = _YEAR_SUFFIX_RE.sub("", s)
    s = unicodedata.normalize("NFKD", s)
    s = s.lower()
    s = _NON_ALNUM_RE.sub(" ", s)
    s = _MULTI_SPACE_RE.sub(" ", s).strip()
    return s


def _extract_year(name: str, db_year: Any) -> Optional[int]:
    """Get year from DB column or title suffix."""
    if db_year and int(db_year) > 1900:
        return int(db_year)
    m = _YEAR_SUFFIX_RE.search(name)
    if m:
        return int(m.group(1))
    return None


_rebuild_lock = threading.Lock()


def rebuild(conn: Optional[sqlite3.Connection] = None) -> dict[str, Any]:
    """Full rebuild of canonical tables from nigma_vod + nigma_series."""
    if not _rebuild_lock.acquire(timeout=0.1):
        return {"error": "rebuild already in progress"}
    try:
        return _rebuild_inner(conn)
    finally:
        _rebuild_lock.release()


def _rebuild_inner(conn: Optional[sqlite3.Connection] = None) -> dict[str, Any]:
    t0 = time.monotonic()
    own_conn = conn is None
    if own_conn:
        conn = _db()

    conn.execute("DELETE FROM title_canonical_link")
    conn.execute("DELETE FROM title_canonical_map")
    conn.commit()

    canonical_count = 0
    link_count = 0
    key_to_cid: dict[str, int] = {}

    sources = [
        ("nigma_vod", "movie"),
        ("nigma_series", "series"),
    ]

    for table, kind in sources:
        try:
            rows = conn.execute(
                f"SELECT id, name, year, category_name FROM {table} WHERE COALESCE(hidden,0)=0"
            ).fetchall()
        except sqlite3.OperationalError:
            log.warning("LT-17: table %s not found, skipping", table)
            continue

        for row in rows:
            rid = str(row["id"])
            raw_name = row["name"] or ""
            cat = row["category_name"] or ""
            db_year = row["year"]

            nkey = _normalize_key(raw_name)
            if not nkey:
                continue

            region = _extract_region(raw_name, cat)
            clean_title = _strip_title(raw_name)
            year = _extract_year(raw_name, db_year)

            cid = key_to_cid.get(nkey)
            if cid is None:
                conn.execute(
                    "INSERT OR IGNORE INTO title_canonical_map "
                    "(canonical_title, canonical_year, canonical_kind, normalized_key) "
                    "VALUES (?, ?, ?, ?)",
                    (clean_title, year, kind, nkey),
                )
                row_cid = conn.execute(
                    "SELECT canonical_id FROM title_canonical_map WHERE normalized_key=?", (nkey,)
                ).fetchone()
                if not row_cid:
                    continue
                cid = row_cid[0]
                key_to_cid[nkey] = cid
                canonical_count += 1

            try:
                conn.execute(
                    "INSERT OR IGNORE INTO title_canonical_link (canonical_id, source_table, source_id, region_label) "
                    "VALUES (?, ?, ?, ?)",
                    (cid, table, rid, region),
                )
                link_count += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("LT-17: rebuild done — %d canonical, %d links in %d ms", canonical_count, link_count, elapsed_ms)
    if own_conn:
        conn.close()
    return {"canonical_count": canonical_count, "link_count": link_count, "ms": elapsed_ms}


# ── endpoints ─────────────────────────────────────────────────────────

@router.post("/rebuild")
async def api_rebuild():
    return rebuild()


@router.get("/by-title")
async def api_by_title(q: str = Query(..., min_length=1)):
    """Fuzzy search canonical titles, return matches with linked regions."""
    conn = _db()
    try:
        search = "%" + q.strip().lower() + "%"
        rows = conn.execute(
            "SELECT canonical_id, canonical_title, canonical_year, canonical_kind, normalized_key "
            "  FROM title_canonical_map "
            " WHERE normalized_key LIKE ? OR LOWER(canonical_title) LIKE ? "
            " ORDER BY canonical_year DESC NULLS LAST "
            " LIMIT 50",
            (search, search),
        ).fetchall()

        results = []
        for r in rows:
            cid = r["canonical_id"]
            links = conn.execute(
                "SELECT source_table, source_id, region_label FROM title_canonical_link WHERE canonical_id=?",
                (cid,),
            ).fetchall()
            results.append({
                "canonical_id": cid,
                "canonical_title": r["canonical_title"],
                "year": r["canonical_year"],
                "kind": r["canonical_kind"],
                "normalized_key": r["normalized_key"],
                "region_count": len(links),
                "regions": [
                    {"source_table": lk["source_table"], "source_id": lk["source_id"], "region": lk["region_label"]}
                    for lk in links
                ],
            })
        return {"query": q, "count": len(results), "results": results}
    finally:
        conn.close()


@router.get("/{canonical_id}/regions")
async def api_regions(canonical_id: int):
    """All regional variants for a given canonical ID."""
    conn = _db()
    try:
        canon = conn.execute(
            "SELECT canonical_id, canonical_title, canonical_year, canonical_kind "
            "  FROM title_canonical_map WHERE canonical_id=?",
            (canonical_id,),
        ).fetchone()
        if not canon:
            return JSONResponse({"error": "not found", "canonical_id": canonical_id}, status_code=404)

        links = conn.execute(
            "SELECT source_table, source_id, region_label FROM title_canonical_link WHERE canonical_id=?",
            (canonical_id,),
        ).fetchall()

        variants = []
        for lk in links:
            src = lk["source_table"]
            sid = lk["source_id"]
            detail = conn.execute(
                f"SELECT name, category_name, poster_url FROM {src} WHERE id=?", (int(sid),)
            ).fetchone()
            variants.append({
                "source_table": src,
                "source_id": sid,
                "region": lk["region_label"],
                "original_name": detail["name"] if detail else None,
                "category": detail["category_name"] if detail else None,
                "poster_url": detail["poster_url"] if detail else None,
            })

        return {
            "canonical_id": canon["canonical_id"],
            "canonical_title": canon["canonical_title"],
            "year": canon["canonical_year"],
            "kind": canon["canonical_kind"],
            "variant_count": len(variants),
            "variants": variants,
        }
    finally:
        conn.close()


# ── background init on import ─────────────────────────────────────────

def _bg_init():
    try:
        init_db()
        rebuild()
    except Exception:
        log.exception("LT-17: background init failed")

threading.Thread(target=_bg_init, daemon=True, name="lt17-init").start()
