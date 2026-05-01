#!/usr/bin/env python3
"""u4 Wave 2 fix — Sports + Live TV heroes feel small relative to others.

Sports today: kicker + title + 2 CTAs all crammed into a small green-bordered
panel on the LEFT (50% width). The scoreboard graphic dominates. Other tabs
(Home, Movies, Series, Anime, Kids, 18+) have a full-width hero with a big
title taking visual center stage.

Live TV today: "What's on now · American TV" is a small subtitle, then 3
program cards (Top News / Top Sports / Top Novela) below. No singular hero
moment.

GOAL: bring Sports + Live TV to parity with the other 7 tabs.
  • Sports: full-width hero. Title "América vs Pumas" big and bold. Kicker
    "LIVE NOW · LIGA MX". 2 CTAs (Watch Live + Open Scoreboard). Move the
    green-bordered scoreboard graphic to the RIGHT side of the hero (like
    Home's "Project Hail Mary" poster). Keep the existing multiplex picker
    (TUDN / ESPN Deportes / Fox Sports MX) UNDER the hero.
  • Live TV: full-width hero. Title "Watching now · Liga MX build-up" (or
    similar — pick the most "tonight's anchor" feed). Kicker "WHAT'S ON
    AMERICAN TV · LIVE". Description "{country} mainstream lineup · {N}
    channels showing now". 2 CTAs (Watch Now + Browse all 7,355 channels).
    Move the 3 program cards underneath to a sub-row labelled "Also live now".
"""
import subprocess
from pathlib import Path

CURSOR = "/root/.local/bin/cursor-agent"
MODEL = "auto"

CTX = """RomanTV Wave 2 fix — Sports + Live TV heroes feel small relative to other tabs.

Both pages already have hero content (kicker + title + CTAs) but it's crammed
into a smaller left-side panel rather than taking the full hero treatment that
Home / Movies / Series / Anime / Kids / 18+ / Esports use.

Files to edit:
  /root/mxstream-app/static/mockups/CATALOG/sports_APPROVED_sp1.html
  /root/mxstream-app/static/mockups/CATALOG/livetv_APPROVED_lt1.html

Each page has TWO copies of the design (lang-en + lang-es wrappers). Apply changes to BOTH.

Reference structures (compare to these — they're the unified pattern):
  /root/mxstream-app/static/mockups/CATALOG/movies_APPROVED_v1.html
  /root/mxstream-app/static/mockups/CATALOG/series_APPROVED_h1.html
  /root/mxstream-app/static/mockups/CATALOG/kids_APPROVED_k4.html

Unified hero anatomy:
  <section class="X-hero" or .hero or .cinematic>
    <div class="hero-bg">  <!-- background image / video -->
    <div class="hero-content">  <!-- left 60% or full width -->
      <p class="hero-kicker">ITALIC GOLD UPPERCASE TAG</p>
      <h1 class="hero-title">Big Sans Bold Title</h1>
      <p class="hero-desc">One line description in dim color</p>
      <div class="hero-ctas">
        <button class="btn-primary">Primary CTA</button>
        <button class="btn-secondary">Secondary CTA</button>
      </div>
    </div>
    <div class="hero-poster">  <!-- right 40% -->
      <!-- visual feature: poster image, scoreboard graphic, character collage -->
    </div>
  </section>

Hero CSS (already in /static/u4_unified.css?v=11):
  min-height: 60vh laptop · 50vh mobile · 85vh TV
  linear-gradient overlay
  italic gold kicker (uppercase, 1px letter-spacing)
  sans bold title (64-84px laptop)
  dim description (16-18px)
  64px primary + secondary CTA pair

═══════════════════════════════════════════════════════════════════
SPORTS sp1 — current state
═══════════════════════════════════════════════════════════════════
The "LIVE NOW WALL" kicker + "América vs Pumas" title + 2 CTAs are inside a
green-bordered panel taking only ~50% of the screen width. The scoreboard
graphic (AME 2-1 PUM) sits inside the same panel. Looks small/crammed.

Fix:
  1. Promote the existing kicker to <p class="hero-kicker">LIVE NOW · LIGA MX</p>
  2. Promote the title "América vs Pumas" to <h1 class="hero-title">.
  3. Add description: <p class="hero-desc">Multiplex live matchup with instant
     channel switching and commentary options · 47.3k watching now</p>
  4. CTAs: <button class="btn-primary">▶ Watch Live</button>
           <button class="btn-secondary">Open Scoreboard</button>
  5. Move the green-bordered AME 2-1 PUM graphic to the RIGHT side of the
     hero (similar to how Home shows the Project Hail Mary poster on the
     right). Strip the green border (it was a bespoke Sports-only treatment
     — let the hero overlay do the visual treatment instead).
  6. Move the multiplex picker (TUDN / ESPN Deportes / Fox Sports MX) and
     the "47.3k watching live · simulcasts across 4 channels" caption into
     a sub-row LABELLED "Multiplex picks" UNDER the hero.
  7. Move the "También en vivo" / "Also live" lateral list (ESP vs ARG,
     LAG vs SJ, etc.) to its own row UNDER the multiplex sub-row, full-width.

═══════════════════════════════════════════════════════════════════
LIVE TV lt1 — current state
═══════════════════════════════════════════════════════════════════
"What's on now · American TV" is a small subtitle. Then 3 program cards
(Top News, Top Sports, Top Novela). No singular hero moment.

Fix:
  1. Pick ONE program as the hero (the one Juan/family is most likely watching
     right now — make it Liga MX build-up since Mexico is the family's primary
     market). Use it as the hero subject.
  2. <p class="hero-kicker">LIVE NOW · LIGA MX</p>
     <h1 class="hero-title">Liga MX build-up</h1>
     <p class="hero-desc">7,355 American channels · 164 Mexican channels ·
     1,360 LATAM-native streams · live now</p>
  3. CTAs: <button class="btn-primary">▶ Watch Now</button>
           <button class="btn-secondary">Browse all channels</button>
  4. Move the 3 existing program cards (Noticiero Univisión / TUDN / Las
     Estrellas) to a sub-row UNDER the hero, with row header "Also live
     right now · top picks".
  5. Add a hero-poster on the RIGHT showing the channel logo collage
     (TUDN logo + ESPN Deportes logo + ABC News + a few channel thumbnails).

═══════════════════════════════════════════════════════════════════
APPROACH
═══════════════════════════════════════════════════════════════════
1. Backup each file as `*.bak_w2_fix_2`
2. Edit HTML — add canonical .hero-kicker / .hero-title / .hero-desc / .hero-ctas
   classes. Move existing scoreboard / multiplex / program-card content INTO
   sub-rows below the hero.
3. NO new CSS rules needed — the unified u4_unified.css already styles the
   canonical hero classes via Wave 2 selectors. Just add the matching class
   names to the Sports + Live TV HTML.
4. Bump cache-bust on both pages from `?v=11` to `?v=12`.
5. Verify with chrome --headless:
     google-chrome --headless --no-sandbox --disable-gpu \\
       --window-size=1440,900 \\
       --screenshot=/tmp/w2fix_sports.png \\
       'https://romantv.net/static/mockups/CATALOG/sports_APPROVED_sp1.html'
     google-chrome --headless --no-sandbox --disable-gpu \\
       --window-size=1440,900 \\
       --screenshot=/tmp/w2fix_livetv.png \\
       'https://romantv.net/static/mockups/CATALOG/livetv_APPROVED_lt1.html'
6. Visually confirm: kicker + title + desc + CTA all readable at full width,
   right-side has a poster/visual, sub-rows below.
7. Report: bytes-changed, new screenshots saved.
"""

prompt_file = "/tmp/cursor_w2fix.txt"
out_file = "/tmp/cursor_w2fix.out"
Path(prompt_file).write_text(CTX)

print(f"Dispatching Cursor with {MODEL} for Sports + Live TV hero fix...")
cmd = f'{CURSOR} --model {MODEL} --print --force --yolo "$(cat {prompt_file})" > {out_file} 2>&1'
try:
    subprocess.run(["bash", "-c", cmd], timeout=900)
    print("→ Cursor finished")
except subprocess.TimeoutExpired:
    print("⚠ Cursor timed out — check /tmp/cursor_w2fix.out")

out = Path(out_file).read_text() if Path(out_file).exists() else "(no output)"
print("\n=== CURSOR OUTPUT (last 80 lines) ===")
print("\n".join(out.split("\n")[-80:]))
