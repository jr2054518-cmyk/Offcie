# Offcie — Current State Across All Projects

**Last synced:** May 1 2026 (auto-updated on every Stop hook commit)

This file is the cross-device snapshot. Open this on any device (laptop, phone via Chrome Remote Desktop) to see what's in flight.

---

## Active Projects

### 1. RomanTV (streaming app — primary work)
- **Status:** Catalog deployed, data piping live, ~17 bugs fixed this session, ~10 open
- **URL:** https://romantv.net
- **VPS:** netcup (`/root/mxstream-app`, port 7006, FastAPI)
- **Repo state mirror:** `projects/romantv/` (this repo)
- **Open bugs:** see `projects/romantv/BUGS_OPEN.md`
- **Session log:** `projects/romantv/SESSION_LOG.md`

### 2. Kalshi Crypto (trading) — pinned, no work this session
- **Status:** SPEC 142 deep-context AI ensemble live (verify per CLAUDE.md memory)
- **VPS:** netcup (`/root/kalshi/`)

### 3. Oanda Bot (forex) — no work this session
### 4. ESports Kalshi — covered by SPEC 142
### 5. VPS-Netcup setup — stable
### 6. To-Do List — managed via this repo's `.claude/` settings

---

## Cross-Device Sync Setup

### Auto-pull on session start
`.claude/settings.local.json` SessionStart hook runs:
```
git pull --rebase --autostash
```
on every new Claude Code session.

### Auto-push on session end
Stop hook runs:
```
git add -A && git commit -m 'auto: claude session sync' && git push -u origin HEAD
```
on every session close.

### Branch hygiene
- `main` — clean snapshot, this is what auto-syncs
- `claude/general-session-7ZnlD` — older dev branch (don't merge per rule)
- Feature work on `main` directly (this single-user repo doesn't need PRs)

---

## How to resume on a different device

1. Open Claude Code → JRoma (cloud) tab → New session
2. SessionStart hook auto-pulls — STATE.md + projects/ now reflect last machine's work
3. Read this STATE.md first to see what was in flight
4. Read the project's SESSION_LOG.md for detailed history
5. Read the project's BUGS_OPEN.md for known issues
6. Continue from where the previous session ended

---

## Memory anchors

- **CLAUDE.md** at repo root — consolidated who/what/setup memory
- **memory/MEMORY.md** at `~/.claude/projects/...` — the per-machine memory file (NOT in repo, machine-local)

The repo + CLAUDE.md is the cross-device memory. The local memory file is the per-machine cache that gets refreshed by reading the repo's CLAUDE.md.
