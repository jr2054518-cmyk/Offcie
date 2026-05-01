#!/usr/bin/env python3
"""u4 Wave 2.2 — fix Live TV hero dimming.

The Live TV hero renders with `Liga MX build-up` title in dim gray, and
the `▶ Watch Now` + `Browse all channels` CTAs as ghosted outline-only
buttons. Other 8 tabs render fine — Sports, with the same hero classes,
renders bright.

Compare:
- Sports hero: bright white "América vs Pumas", solid red "▶ Watch Live" CTA
- Live TV hero: dim gray "Liga MX build-up", red-outline-only "▶ Watch Now"

Hypothesis: a leftover Live TV bespoke CSS rule is winning over the unified
.hero-title / .btn-primary rules. Could be:
  • #lt1 .X-hero-title { color: var(--dim) }   (specificity 1 ID + 1 class = 110)
  • #lt1 .btn-primary { background: transparent; border: 1px solid var(--accent) }
  • OR the hero-bg / overlay is dimming things
  • OR there's a parent element with opacity < 1

Cursor's job:
  1. Inspect /root/mxstream-app/static/mockups/CATALOG/livetv_APPROVED_lt1.html
     inline <style> block for any rule matching .hero-* / .btn-* / hero-content /
     hero-section / lt-* that sets color, background, opacity, filter.
  2. Identify the rule that's making the title dim and the CTAs ghosted.
  3. Strip the offending rule (or add a more specific override in the unified
     u4_unified.css if needed). Prefer stripping bespoke over adding overrides
     (per Juan's fresh-start rule).
  4. Bump cache-bust on livetv from `?v=12` to `?v=13`.
  5. Verify: chrome --headless screenshot, save to /tmp/w2_2_livetv.png.
     Also re-screenshot Sports for control: /tmp/w2_2_sports.png.
  6. Confirm: title is bright white, primary CTA is solid red filled, secondary
     CTA is gold-outline. Same as Sports.
"""
import subprocess
from pathlib import Path

CURSOR = "/root/.local/bin/cursor-agent"
MODEL = "auto"

CTX = """RomanTV catalog Wave 2.2 fix — Live TV hero is dimming.

PROBLEM:
The Live TV catalog page hero renders with the title text dim/grayed and the
CTAs as outline-only (no fill on Watch Now, gold-outline-only on Browse all
channels). Compare to Sports which renders bright white title + solid red
primary CTA using the SAME .hero-title / .btn-primary classes.

Both pages use the unified hero CSS at /root/mxstream-app/static/u4_unified.css?v=12.
Sports renders correctly. Live TV does NOT.

FILES:
  /root/mxstream-app/static/mockups/CATALOG/livetv_APPROVED_lt1.html
  /root/mxstream-app/static/mockups/CATALOG/sports_APPROVED_sp1.html (control)
  /root/mxstream-app/static/u4_unified.css

EVIDENCE (visual):
  Live TV hero:
    - "Liga MX build-up" title appears in light gray instead of bright white
    - "▶ Watch Now" button has red BORDER but transparent background and
      grayed-out text (should be: solid red bg, white text, gold left-edge)
    - "Browse all channels" button has gold border but grayed-out gold text
      (should be: bright gold border + bright gold text)

ROOT CAUSE HYPOTHESIS (verify before fixing):
  1. The page's bespoke `<style>` block has a rule like:
       #lt1 .lt-hero-head h1 { color: var(--dim) }   or
       #lt1 .lt-section .btn-primary { background: transparent }
     that wins via specificity (1 ID + 1+ class = 110+ vs unified's 10-30).
  2. OR a parent like `.lt-hero-section` has `opacity: 0.7` set somewhere.
  3. OR there's a leftover `.btn-primary { background: transparent !important }`
     in the inline style block (from a previous "outline-style buttons" treatment).

YOUR JOB:
  1. Inspect the inline <style> block in livetv_APPROVED_lt1.html for ANY
     rule matching:
       - hero-* (kicker, title, desc, ctas)
       - btn-primary, btn-secondary
       - lt-hero, lt-spot, lt-section
       - opacity, filter
     and identify which rule is dimming the hero text + ghosting the CTAs.
  2. Confirm by comparing with sports_APPROVED_sp1.html — the same rules
     in Sports do NOT have this issue, so the difference is the bespoke
     Live TV inline CSS.
  3. STRIP the offending rule(s) from livetv_APPROVED_lt1.html. Apply the
     strip to BOTH lang-en and lang-es copies of the design.
  4. Backup before editing: livetv_APPROVED_lt1.html.bak_w2_dim_fix
  5. Bump cache-bust on livetv from `?v=12` to `?v=13`.

VERIFY:
  • Screenshot Live TV at 1440x900:
      google-chrome --headless --no-sandbox --disable-gpu \\
        --window-size=1440,900 \\
        --screenshot=/tmp/w2_2_livetv.png \\
        'https://romantv.net/static/mockups/CATALOG/livetv_APPROVED_lt1.html'
  • Screenshot Sports as control (should be unchanged):
      google-chrome --headless --no-sandbox --disable-gpu \\
        --window-size=1440,900 \\
        --screenshot=/tmp/w2_2_sports.png \\
        'https://romantv.net/static/mockups/CATALOG/sports_APPROVED_sp1.html'
  • Visually confirm Live TV now has: bright white title, solid red filled
    Watch Now CTA with gold left-edge, bright gold-outline + gold-text Browse
    all channels CTA.

REPORT:
  • Which rule(s) caused the dimming
  • What you stripped and from which line(s)
  • Bytes changed
  • PASS / FAIL verdict
"""

prompt_file = "/tmp/cursor_w2_2.txt"
out_file = "/tmp/cursor_w2_2.out"
Path(prompt_file).write_text(CTX)

print(f"Dispatching Cursor with {MODEL} for Live TV dim fix...")
cmd = f'{CURSOR} --model {MODEL} --print --force --yolo "$(cat {prompt_file})" > {out_file} 2>&1'
try:
    subprocess.run(["bash", "-c", cmd], timeout=900)
    print("→ Cursor finished")
except subprocess.TimeoutExpired:
    print("⚠ Cursor timed out — check /tmp/cursor_w2_2.out")

out = Path(out_file).read_text() if Path(out_file).exists() else "(no output)"
print("\n=== CURSOR OUTPUT (last 80 lines) ===")
print("\n".join(out.split("\n")[-80:]))
