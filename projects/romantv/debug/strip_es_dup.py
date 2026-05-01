#!/usr/bin/env python3
"""Strip leftover Spanish duplicate content from each production HTML.

The lang-es wrapper was removed, but the chip-row + rv-row + provider-row
INSIDE it survived. They render after the EN content as duplicates.

Strategy: find the SECOND occurrence of the chip-row/header marker per file
and delete from there to just before </body>.
"""
import re
from pathlib import Path

PROD = Path("/root/mxstream-app/static")

# Each tab uses different chip-row/header class names — find the SECOND occurrence
# of any "filter chip row" pattern that signals start of duplicate ES content.
TABS = {
    "index.html":      [r'<div[^>]*class="rv-chip-row"', r'<div[^>]*class="v1a-chip-row"', r'<div[^>]*class="cat-bar"'],
    "movies.html":     [r'<div[^>]*class="rv-chip-row"'],
    "series.html":     [r'<div[^>]*class="h1-(chip|navtab)-row"', r'<div[^>]*class="h1-chip-row"'],
    "anime.html":      [r'<div[^>]*class="a1b-chip-row"', r'<div[^>]*class="a1b-audio-chips"'],
    "kids.html":       [r'<div[^>]*class="k4-(chip|age|filter)"'],
    "livetv.html":     [r'<div[^>]*class="lt-(chip|filter)-row"'],
    "sports.html":     [r'<div[^>]*class="sp1-(chip|view)"'],
    "esports.html":    [r'<div[^>]*class="es1-(chip|region)"'],
    "premium-tv.html": [r'<div[^>]*class="bucket-strip"'],
}

for fname, patterns in TABS.items():
    p = PROD / fname
    if not p.exists():
        print(f"  {fname}: missing"); continue
    src = p.read_text()
    # Count chip-rows total (should be 1 after fix)
    total_chip_rows = sum(len(re.findall(pat, src)) for pat in patterns)
    if total_chip_rows < 2:
        print(f"  {fname}: only {total_chip_rows} chip-row(s) — already clean")
        continue
    # Find the SECOND occurrence
    second_pos = -1
    for pat in patterns:
        matches = list(re.finditer(pat, src))
        if len(matches) >= 2:
            second_pos = matches[1].start()
            break
    if second_pos < 0:
        print(f"  {fname}: couldn't locate 2nd chip-row")
        continue
    # Find the END marker: look for </body> or last </section> before script block
    body_close = src.rfind("</body>")
    script_block_start = src.rfind("<script>")
    end_pos = body_close if body_close > 0 else len(src)
    # Don't strip past script blocks — keep them
    if script_block_start > second_pos and script_block_start < end_pos:
        end_pos = script_block_start
    # Backup
    bak = p.with_suffix(p.suffix + ".bak_es_strip")
    if not bak.exists():
        bak.write_text(src)
    # Strip
    new = src[:second_pos] + src[end_pos:]
    p.write_text(new)
    print(f"  {fname}: stripped {end_pos - second_pos} bytes ({len(src):,} → {len(new):,}) — chip-rows now {sum(len(re.findall(pat, new)) for pat in patterns)}")

print("\ndone")
