# Offcie — Claude Memory & Setup

## Who I Am
- **User:** Juan (GitHub: jr2054518-cmyk, JRoma)
- **Repo:** jr2054518-cmyk/Offcie
- **Purpose:** Personal AI secretary — work tasks, projects, automation

## Environment
- **Cloud env (primary):** `/home/user/Offcie` on Linux (this is the JRoma tab in Claude Code desktop)
- **Laptop:** Windows, Claude Code desktop app installed
- **Rule:** Always work in the **JRoma (cloud) tab**, never Local — so work is accessible from any device
- **Phone access:** Chrome Remote Desktop (setup pending) → control laptop → use JRoma tab

## Git Setup
- **Main branch:** `main`
- **Dev branch:** `claude/general-session-7ZnlD`
- **Remote:** `origin` → github.com/jr2054518-cmyk/Offcie
- **Auto-sync hooks (settings.local.json):**
  - SessionStart: `git pull --rebase --autostash` — pulls latest on every session start
  - Stop: `git add -A && git commit && git push` — auto-commits and pushes on session end

## Active Projects (from laptop sessions)
- **Kalshi Crypto** — crypto trading / Kalshi prediction market work (pinned)
- **Oanda Bot** — forex trading bot
- **ESports Kalshi** — esports prediction markets
- **RomanTV** — streaming/TV app (had bugs, ongoing)
- **VPS-Netcup** — VPS server setup
- **To-Do List** — personal task tracking

## Key Decisions Made
- Use cloud (JRoma) tab as primary workspace across all devices
- Chrome Remote Desktop for phone → laptop access
- Git hooks handle cross-session continuity (no manual commits needed)
- Auto-created PRs from hooks should be closed, not merged

## Permissions Allowed (settings.local.json)
`git pull, push, add, commit, diff, status, log`

## How to Start a New Task
1. Open Claude Code desktop → JRoma tab → New session
2. Session auto-pulls latest from GitHub
3. Work here — changes auto-push when session ends
