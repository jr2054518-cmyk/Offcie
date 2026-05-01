#!/usr/bin/env python3
"""Hunt for leftover bespoke nav active-state rules across all 9 catalog pages.
The unified CSS expects gold underline + gold-tinted background on
.X-nav a.is-active / .X-nav a.active / [aria-current=page]. Any
additional inline rule painting border/box-shadow/background on the
active link competes with the unified rendering.
"""
import re, urllib.request

PAGES = [
    "home_APPROVED_v1a.html","movies_APPROVED_v1.html","series_APPROVED_h1.html",
    "anime_APPROVED_a1b.html","kids_APPROVED_k4.html","livetv_APPROVED_lt1.html",
    "sports_APPROVED_sp1.html","esports_APPROVED_es1.html","adult_APPROVED_eg1v2.html",
]

# Regex: any CSS rule whose selector mentions "active" or "is-active" or aria-current
#   and whose body sets visual properties (background, box-shadow, border, color).
# This catches rules like `.h1-navtab.is-active {...}` or `.k4-navlink.active {...}`.
RULE = re.compile(
    r'(?:^|[\s,{])([^{}]*?(?:\.is-active|\.active|\[aria-current[^\]]*\])[^{}]*)\s*\{([^}]*?)\}',
    re.M
)

print("# Leftover active-state CSS hunt\n")
total_flags = 0
for page in PAGES:
    url = f"https://romantv.net/static/mockups/CATALOG/{page}"
    try:
        html = urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"  {page}: fetch failed: {e}")
        continue
    style = "\n".join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.I | re.S))

    flagged = []
    for m in RULE.finditer(style):
        sel = m.group(1).strip()
        body = m.group(2).strip()
        # Skip rules that are ours (the unified ones inject inside <link>, not <style>)
        # Skip generic .picker etc.
        if 'picker' in sel.lower() or 'lang-' in sel.lower(): continue
        # Skip rules that ONLY set visual neutrals (e.g. only `display:flex`)
        if not re.search(r'(background|box-shadow|border\s*:|outline|color\s*:)', body, re.I): continue
        # Skip rules in lang-en/es language toggle which are page UI not topbar nav
        if 'lang' in sel and ('btn' in sel or 'cat-bar' in sel): continue
        # If selector references known bespoke nav classes, flag it as a duplicate
        if re.search(r'\.(v1a|rv|h1|a1b|k4|lt|sp1|es1|nav-pills|navtab|nav)', sel):
            flagged.append((sel[:80], body[:100]))

    # Dedup (same rule appears once per language wrapper)
    flagged = list({(s, b): None for s, b in flagged}.keys())
    if flagged:
        total_flags += len(flagged)
        print(f"\n## ⚠ {page} — {len(flagged)} leftover rule(s)")
        for sel, body in flagged[:5]:
            print(f"   {sel}")
            print(f"     → {body}")
    else:
        print(f"  ✓ {page}")

print(f"\nTOTAL flagged: {total_flags}")
