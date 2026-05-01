LOCAL_CACHE_COLD_ROOT = "/mnt/hetzner-storage"
LOCAL_CACHE_ROOT = LOCAL_CACHE_HOT_ROOT  # back-compat alias
LOCAL_CACHE_TOKEN_SECRET = (os.environ.get("LOCAL_CACHE_TOKEN_SECRET") or "").encode("utf-8") or b"rotate-me-please"

def _local_cache_sign_token(file_id: int, ttl_s: int = 24*3600) -> str:
    exp = int(time.time()) + int(ttl_s)
    payload = f"{file_id}|{exp}".encode("utf-8")
    sig = _hmac.new(LOCAL_CACHE_TOKEN_SECRET, payload, _hashlib.sha256).digest()
    return _base64.urlsafe_b64encode(payload + b"." + sig).decode("ascii").rstrip("=")



    """Return /local-stream/<token> URL for of:<creator>:<post_id>, else None."""
    parts = (item_id or "").split(":")
    if len(parts) < 3 or parts[0] != "of":
        return None
    creator = re.sub(r"[^a-zA-Z0-9_.\-]", "", parts[1])[:60]
    pid = re.sub(r"[^a-zA-Z0-9_]", "", parts[2])[:8]
    cdir = f"/mnt/hetzner-storage/onlyfans/{creator}"
    if not os.path.isdir(cdir):
        return None
    # Find video file matching pid
    target = None
    for f in os.listdir(cdir):
        if f.endswith(".mp4") and pid in f:
            target = os.path.join(cdir, f); break
    if not target:
        return None
    # Insert/get a local_cache row for this OF video so /local-stream can serve
    rel_path = f"onlyfans/{creator}/{os.path.basename(target)}"
    try:
        size = os.path.getsize(target)
        with _db() as conn:
            row = conn.execute("SELECT id FROM local_cache WHERE file_path=? LIMIT 1", (rel_path,)).fetchone()
            if row:
                cid = row["id"]
            else:
                cur = conn.execute(
                    """INSERT INTO local_cache(tt_id,kind,season,episode,file_path,info_hash,status,added_at,file_size_bytes,notes)
                       VALUES(?,?,?,?,?,?,'ready',?,?,?)""",
                    (item_id, "of", None, None, rel_path, "", int(time.time()), size, f"creator={creator}|pid={pid}|tier=cold"),
                )
                cid = cur.lastrowid
        return f"/local-stream/{_local_cache_sign_token(int(cid))}"
    except Exception:
        return None


def _local_cache_verify_token(tok: str) -> Optional[int]:
    try:
        data = _base64.urlsafe_b64decode(tok + "=" * (-len(tok) % 4))
        payload, _, sig = data.partition(b".")
        expected = _hmac.new(LOCAL_CACHE_TOKEN_SECRET, payload, _hashlib.sha256).digest()
        if not _hmac.compare_digest(sig, expected):
            return None
        fid_s, exp_s = payload.decode("utf-8").split("|", 1)
        if int(exp_s) < int(time.time()):
            return None
        return int(fid_s)
    except Exception:
        return None


@app.get("/local-stream/{token}")
async def local_stream(token: str, request: Request):
    """LOCAL_STREAM_ENDPOINT_v1: stream a cached file with Range support."""
    fid = _local_cache_verify_token(token)
    if fid is None:
        return JSONResponse({"error": "invalid or expired token"}, status_code=403)
    user = _require_user(request)
    if not user:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)
    with _db() as conn:
        row = conn.execute(
            "SELECT id, file_path, file_size_bytes FROM local_cache WHERE id=? AND status='ready'",
            (fid,),
        ).fetchone()
        if not row:
            return JSONResponse({"error": "not ready"}, status_code=404)
        # LOCAL_STREAM_TIER_AWARE_v1: route by tier from notes.
        _tier = 'hot'
        try:
            _notes = row['notes'] if 'notes' in row.keys() else ''
        except Exception:
            _notes = ''
        if _notes and 'tier=cold' in _notes:
            _tier = 'cold'
        _root = LOCAL_CACHE_COLD_ROOT if _tier == 'cold' else LOCAL_CACHE_HOT_ROOT
        file_path = os.path.join(_root, row["file_path"])
        if not os.path.isfile(file_path):
            return JSONResponse({"error": "file missing on disk"}, status_code=410)
        # Update play stats async-ish (commit happens immediately, fast)
        conn.execute(
            "UPDATE local_cache SET last_played_at=?, play_count=play_count+1 WHERE id=?",
            (int(time.time()), fid),
        )
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range") or request.headers.get("Range")
    ext = (os.path.splitext(file_path)[1] or "").lower()
    ctype = {".mp4": "video/mp4", ".mkv": "video/x-matroska", ".webm": "video/webm",
             ".m4v": "video/mp4", ".avi": "video/x-msvideo"}.get(ext, "application/octet-stream")
    if range_header and range_header.startswith("bytes="):
        try:
            spec = range_header[6:].split(",")[0].strip()
            start_s, _, end_s = spec.partition("-")
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else file_size - 1
            end = min(end, file_size - 1)
            if start > end or start >= file_size:
                return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})
            length = end - start + 1
            def iter_range():
                with open(file_path, "rb") as fh:
                    fh.seek(start)
                    remaining = length
                    chunk = 64 * 1024
                    while remaining > 0:
                        buf = fh.read(min(chunk, remaining))
                        if not buf: break
                        remaining -= len(buf)
                        yield buf
