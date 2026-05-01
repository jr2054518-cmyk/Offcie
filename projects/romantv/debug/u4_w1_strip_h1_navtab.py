#!/usr/bin/env python3
"""Strip leftover .h1-navtab CSS rules from series_APPROVED_h1.html.
Cursor's strip pass missed these because they target the child class
.h1-navtab rather than the parent .h1-mainnav. The unified CSS already
styles them via the parent selector, so these are redundant + cause
a red active-pill that fights the unified gold underline."""
import re
from pathlib import Path

P = Path("/root/mxstream-app/static/mockups/CATALOG/series_APPROVED_h1.html")
src = P.read_text()

# Strip these 3 rules wherever they appear
PATTERNS = [
    r'\.romantv-series-h1\s+\.h1-navtab\s*\{[^}]*\}\s*',
    r'\.romantv-series-h1\s+\.h1-navtab:hover\s*\{[^}]*\}\s*',
    r'\.romantv-series-h1\s+\.h1-navtab\.is-active\s*\{[^}]*\}\s*',
]
total_removed = 0
new = src
for pat in PATTERNS:
    matches = re.findall(pat, new)
    new = re.sub(pat, "", new)
    total_removed += len(matches)
    print(f"  stripped {len(matches)} rules matching: {pat[:60]}")

if new != src:
    P.write_text(new)
    print(f"\n✓ stripped {total_removed} CSS rules from {P.name} ({len(src):,} → {len(new):,} chars)")
else:
    print("  no rules matched — already clean")

# Bump cache-bust v=5 → v=6 just for this page
old_link = '/static/u4_unified.css?v=5'
new_link = '/static/u4_unified.css?v=6'
src2 = P.read_text()
if old_link in src2:
    P.write_text(src2.replace(old_link, new_link))
    print(f"  bumped cache-bust v=5 → v=6")
