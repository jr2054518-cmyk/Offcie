#!/usr/bin/env python3
"""u4 Wave 2 HARDENING PASS — fix all undersized hero titles + Anime content.

After Wave 2 ships, 6 of 9 tabs still have broken heroes:
  Movies   — title 32px (spec 64-84) · poster crammed on LEFT (should be right)
  Series   — title 32-40px · hero only ~30% viewport
  Anime    — "title" is marketing copy ("FULL LATIN-AM DUB · +1080 EPISODES
              DUBBED") — should be a real anime name
  Kids     — title 32-40px
  Esports  — title 24px · CTAs tiny · layout collapsed
  18+      — title ~28px

Hypothesis: per-tab `#XXX .hero-title { font: ... }` rules win over unified
`.hero-title` because of ID specificity (110 vs 10).
"""
import subprocess, sys
from pathlib import Path

CURSOR = "/root/.local/bin/cursor-agent"
MODEL = "auto"

CTX = """RomanTV catalog Wave 2 HARDENING PASS — 6 of 9 tabs have broken heroes.

CONTEXT:
Wave 2 attempted to unify the hero across 9 catalog pages by applying canonical
.hero-kicker / .hero-title / .hero-desc / .hero-ctas classes and styling them in
/root/mxstream-app/static/u4_unified.css.

Problem: 6 of 9 tabs still render the hero too small or with wrong content,
because per-tab inline <style> rules (with ID-level specificity like
`#v1 .hero-title`) WIN over the unified `.hero-title` rule.

═══════════════════════════════════════════════════════════════════
TARGETS — fix each of these 6 tabs:
═══════════════════════════════════════════════════════════════════

1) movies_APPROVED_v1.html
   PROBLEM: title is rendered ~32px (spec 64-84px). Hero poster is on the LEFT;
            should be on the RIGHT (like Home).
   FIX:
     • Find any `#v1 .hero-title` / `.rv-hero-title` / `.movie-title` inline
       <style> rule that constrains font-size below 60px and either:
         (a) STRIP it (preferred — fresh start)
         (b) OR raise the unified rule's specificity to win
     • Move the poster from left of hero-content to RIGHT (use .hero-poster
       class on the wrapping div). Hero-content takes left 60%, poster takes
       right 40%.
     • Both lang-en + lang-es copies.

2) series_APPROVED_h1.html
   PROBLEM: title (Breaking Bad) is ~32-40px (spec 64-84px). Hero is only
            ~30% of viewport height (spec min-height 60vh).
   FIX:
     • Strip any `#h1 .hero-title` / `.h1-hero-title` rule constraining font.
     • Strip any `#h1 .hero` / `.h1-hero` height rule constraining < 60vh.
     • Both lang copies.

3) anime_APPROVED_a1b.html
   PROBLEM: the <h1 class="hero-title"> currently contains
            "FULL LATIN-AM DUB · +1080 EPISODES DUBBED" — that's MARKETING COPY,
            not an anime title. The kicker already says "FULL LATIN-AM DUB · DUB-FIRST SHOWCASE",
            so the title is redundant and weird.
   FIX:
     • Replace the hero-title content with a REAL anime title — pick the
       featured anime: "One Piece · Latin-Am dub · Saga 4". The kicker stays
       "FULL LATIN-AM DUB · DUB-FIRST SHOWCASE".
     • Add hero-desc: "1080+ episodes dubbed in Latin-American Spanish · live
       co-watch with thousands of fans" (or similar — the count claim 1080+
       matches reality).
     • Update both lang copies. ES title: "One Piece · doblaje Latino · Saga 4"
     • Strip any `#a1b .hero-title` font-size rule constraining < 60px.

4) kids_APPROVED_k4.html
   PROBLEM: title (Coco · Watch Together Tonight) is ~32-40px (spec 64-84px).
            Parental Controls panel on the right is eating hero space.
   FIX:
     • Strip any `#k4 .hero-title` font rule.
     • Make the Parental Controls panel collapse to a small "Parental controls"
       icon button in the top-right of the hero (clickable to expand). When
       collapsed, hero gets the full width like other tabs. When expanded
       (click), the panel slides down/over.
     • Both lang copies.

5) esports_APPROVED_es1.html
   PROBLEM: title (Worlds 2026) is ~24px (spec 64-84px). CTAs are small
            (Watch on Twitch / YouTube mirror / Bracket open all undersized).
            Hero layout is collapsed.
   FIX:
     • Strip any `#es1 .hero-title` / `.es1-hero-title` font rule (specificity
       fight with unified).
     • Strip any `#es1 .hero` / `.es1-hero` width/height constraints below
       100% / 60vh.
     • Strip any `#es1 .btn-primary` / `.es1-btn` etc. that constrains CTA
       size below the unified .btn-primary 64px height.
     • Both lang copies.

6) adult_APPROVED_eg1v2.html
   PROBLEM: title ("Premium private library") is ~28px (spec 64-84px).
   FIX:
     • Strip any `#eg1` / `#eg1v2` / `.eg-hero-title` rule constraining the
       title font-size.
     • The CTAs that look like settings toggles ("Hide previews (safe tiles)"
       + "EN · Global catalog defaults" + "Quick exit") should NOT be the
       hero CTAs. Move them BELOW the hero as a "controls" sub-row. The hero
       CTAs should be: Primary "▶ Browse Library" + Secondary "Quick exit"
       (red emergency exit button).
     • Both lang copies.

═══════════════════════════════════════════════════════════════════
VERIFY GATES (must PASS for each fixed tab — report computed values):
═══════════════════════════════════════════════════════════════════
For each of the 6 tabs, after editing, run a programmatic check:

    google-chrome --headless --no-sandbox --disable-gpu \\
      --window-size=1440,900 --virtual-time-budget=2000 \\
      --dump-dom 'https://romantv.net/static/mockups/CATALOG/<page>?cb=fix' \\
      > /tmp/wv2h_<slug>.html

    cat > /tmp/check_<slug>.js << 'EOF'
    // load the page, query computed hero-title font-size
    const puppeteer = require('puppeteer');
    (async () => {
      const browser = await puppeteer.launch({args:['--no-sandbox']});
      const page = await browser.newPage();
      await page.setViewport({width: 1440, height: 900});
      await page.goto('https://romantv.net/static/mockups/CATALOG/<page>?cb=verify', {waitUntil: 'networkidle0'});
      const result = await page.evaluate(() => {
        const t = document.querySelector('.lang-wrap.active .hero-title');
        const k = document.querySelector('.lang-wrap.active .hero-kicker');
        const p = document.querySelector('.lang-wrap.active .btn-primary');
        return {
          title_font_px: t ? parseFloat(getComputedStyle(t).fontSize) : null,
          title_text: t ? t.textContent.trim().slice(0,60) : null,
          kicker_color: k ? getComputedStyle(k).color : null,
          primary_btn_h: p ? parseFloat(getComputedStyle(p).height) : null,
          primary_btn_bg: p ? getComputedStyle(p).backgroundColor : null,
        };
      });
      console.log(JSON.stringify(result));
      await browser.close();
    })();
    EOF

If puppeteer not available, just do an inline script via google-chrome
--headless --dump-dom and grep computed-style markers. EITHER WAY:

  • title_font_px MUST be >= 56 (unified spec is 64-84). FAIL if < 56.
  • primary_btn_h MUST be >= 56. FAIL if < 56.
  • primary_btn_bg MUST contain `rgb(255, 10, 20)` (--u4-red) or close.
  • For Anime: title_text MUST include "One Piece" (or whatever you chose).
  • Take a screenshot at /tmp/wv2h_<slug>.png so the user can verify visually.

Cache-bust: bump u4_unified.css from `?v=13` to `?v=14` on each page changed.

═══════════════════════════════════════════════════════════════════
DELIVERABLE
═══════════════════════════════════════════════════════════════════
A markdown report at /tmp/wv2h_report.md containing, FOR EACH of the 6 tabs:

  ## <tab>
  - title computed font-size: NN px (spec >= 56) — PASS/FAIL
  - title text: "..."
  - primary CTA computed height: NN px (spec >= 56) — PASS/FAIL
  - primary CTA computed bg: rgb(...) — PASS/FAIL
  - bytes-stripped: NN
  - rules-stripped: list of selectors stripped
  - screenshot: /tmp/wv2h_<slug>.png

Final line: "Wave 2 hardening: <X> of 6 tabs PASS"

If any tab FAILS the gates, KEEP iterating on it until it passes — don't
ship a "PASS" while any tab is < spec.

═══════════════════════════════════════════════════════════════════
CONSTRAINTS
═══════════════════════════════════════════════════════════════════
- Don't break the topbar (Wave 1 already shipped + locked)
- Don't break per-tab unique features (live scoreboard in Sports, parental
  controls in Kids, region tabs in Esports — those stay, just reflow them
  so they don't fight the hero)
- Backups: each file as `*.bak_w2_harden`
- Idempotent — running twice = no-op
"""

prompt_file = "/tmp/cursor_w2h.txt"
out_file = "/tmp/cursor_w2h.out"
Path(prompt_file).write_text(CTX)

print(f"Dispatching Cursor with {MODEL} for Wave 2 hardening pass (will take 8-15 min)...")
cmd = f'{CURSOR} --model {MODEL} --print --force --yolo "$(cat {prompt_file})" > {out_file} 2>&1'
try:
    subprocess.run(["bash", "-c", cmd], timeout=1500)
    print("→ Cursor finished")
except subprocess.TimeoutExpired:
    print("⚠ Cursor timed out — check /tmp/cursor_w2h.out")

out = Path(out_file).read_text() if Path(out_file).exists() else "(no output)"
print("\n=== CURSOR OUTPUT (last 100 lines) ===")
print("\n".join(out.split("\n")[-100:]))
