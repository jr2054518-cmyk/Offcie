#!/usr/bin/env python3
"""u4 search-icon audit — find duplicate magnifier glass icons.

For each catalog page, locate the topbar search input and inspect the
surrounding HTML for any of these patterns:
  • <svg> sibling rendering a magnifier inside the search wrapper
  • <span class*=icon> / <i class*=fa-search> / .icon-search rendering inside
  • CSS background-image url(svg ... search ...) on the input itself
  • An emoji magnifier 🔍/🔎 in the placeholder or as text

The unified u4 CSS adds its OWN magnifier as a background-image. If a tab also
has a sibling element doing the same thing, the user sees TWO magnifiers.

Strategy:
  • For each tab, walk back ~2000 chars from the search <input> tag
  • Find any svg/span/i icon element in that proximity
  • Print a per-tab verdict and the exact element to remove
"""
import re, urllib.request
from pathlib import Path

BASE = "https://romantv.net/static/mockups/CATALOG/"
TABS = [
    ("home",   "home_APPROVED_v1a.html"),
    ("movies", "movies_APPROVED_v1.html"),
    ("series", "series_APPROVED_h1.html"),
    ("anime",  "anime_APPROVED_a1b.html"),
    ("kids",   "kids_APPROVED_k4.html"),
    ("livetv", "livetv_APPROVED_lt1.html"),
    ("sports", "sports_APPROVED_sp1.html"),
    ("esports","esports_APPROVED_es1.html"),
    ("adult",  "adult_APPROVED_eg1v2.html"),
]

# Patterns that suggest a sibling magnifier icon
ICON_PATTERNS = [
    (r'<svg[^>]*>(?:(?!</svg>).)*?<circle[^>]+r=["\']?(?:7|8|9|10)["\']?[^>]*>', 'svg-circle (magnifier)'),
    (r'<svg[^>]*class=["\']?[^"\']*search[^"\']*["\']?', 'svg.search'),
    (r'<i\s+class=["\'][^"\']*(?:fa-search|fa-magnifying|search-icon|icon-search)[^"\']*["\']', 'icon-class'),
    (r'<span\s+class=["\'][^"\']*(?:search-ico|search-icon|icon-search)[^"\']*["\']', 'span-icon-class'),
    (r'background(?:-image)?\s*:\s*url\([^)]*svg[^)]*search[^)]*\)', 'css-bg-svg-search'),
    (r'background(?:-image)?\s*:\s*url\([^)]*search[^)]*svg[^)]*\)', 'css-bg-search-svg'),
    (r'placeholder=["\'][^"\']*[\U0001F50D\U0001F50E]', 'emoji-magnifier-in-placeholder'),
    # Inline svg with magnifier shape (path containing M21 21l-4-4 or similar)
    (r'<svg[^>]*>[^<]*<(?:circle[^>]*r=["\']?(?:7|8|9|10)|path[^>]*d=["\'][^"\']*M2[0-2]\s*2[0-2])', 'svg-magnifier-path'),
]

print("# u4 Search-Icon Audit\n")
print(f"Scanning {len(TABS)} catalog pages for duplicate magnifier icons.\n")
print(f"Unified CSS already adds a magnifier via `background: url(svg...)` on every search input.")
print(f"If the page ALSO has its own sibling magnifier, the user sees two icons.\n")

findings = {}
for slug, page in TABS:
    try:
        html = urllib.request.urlopen(BASE + page, timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"\n## ❌ {slug}: fetch failed: {e}")
        continue

    # Find each search input in the page (we have EN+ES wrappers but only one is visible)
    # Just look at first occurrence per page since both wrappers are usually identical structure
    m = re.search(r'<input[^>]*type=["\']?(?:search|text)["\']?[^>]*>|<input[^>]*placeholder=', html, re.I)
    if not m:
        print(f"\n## ⚠ {slug}: no search input found")
        continue

    # Walk back to find enclosing wrapper (form / div / header containing both icon + input)
    start = m.start()
    # Look 1500 chars BEFORE the input for sibling icons
    before_window = html[max(0, start-1500):start]
    # Look 200 chars AFTER too (some designs put icon AFTER input)
    after_window = html[m.end():m.end()+200]

    # Also pull the inline <style> block for the page to scan for CSS-bg patterns
    style_block = "\n".join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.I | re.S))

    issues = []
    # Check HTML windows
    for pat, label in ICON_PATTERNS:
        if 'css-bg' in label:
            # search the inline style block for a background-image rule scoped to a search input
            if re.search(pat, style_block, re.I):
                issues.append((label, 'inline-style'))
        else:
            for window, where in [(before_window, 'before-input'), (after_window, 'after-input')]:
                if re.search(pat, window, re.I | re.S):
                    issues.append((label, where))

    # Special check: any <svg> inside the topbar/search-wrapper area (any svg at all is suspicious)
    svg_in_window = re.findall(r'<svg[^>]*>', before_window)
    if svg_in_window and not any('svg' in label for label, _ in issues):
        issues.append((f'<svg> sibling found ({len(svg_in_window)})', 'before-input'))

    findings[slug] = issues
    if issues:
        print(f"\n## ⚠ {slug} · {page}")
        for label, where in issues:
            print(f"   - {label} ({where})")
        # Print the exact 200-char window before the input so we can see it
        snippet = before_window[-300:].replace("\n", " ")
        print(f"   context: ...{snippet}")
    else:
        print(f"\n## ✓ {slug}: no icon duplicate detected")

print("\n\n# Summary")
print(f"  {sum(1 for v in findings.values() if v)} of {len(findings)} tabs have a likely duplicate icon")
for slug, issues in findings.items():
    if issues:
        print(f"    - {slug}: {len(issues)} indicator(s)")
