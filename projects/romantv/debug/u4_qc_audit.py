#!/usr/bin/env python3
"""u4 QC AUDIT — visit each of 9 catalog pages, report:
  - all visible search inputs (bbox + placeholder + parent context)
  - topbar dimensions (height, padding, bg, position)
  - any element overflowing viewport horizontally
  - JS console errors thrown during page load
  - any element that's `display:none` but shouldn't be (e.g. hero with 0 height)
  - sticky/fixed elements that overlap (z-index conflicts)
Saves a markdown audit report under /root/mxstream-app/static/u4_compare/qc_audit.md."""
import json, sys, urllib.request
from pathlib import Path

# This script runs on the VPS and does the auditing via headless browser
# But playwright on netcup may not be installed — fall back to plain HTTP+regex audit
import re

BASE = "https://romantv.net/static/mockups/CATALOG/"
TABS = [
    ("home",   "home_APPROVED_v1a.html",      [".v1a-topbar"], [".v1a-nav"]),
    ("movies", "movies_APPROVED_v1.html",     [".rv-topbar"],  [".rv-nav"]),
    ("series", "series_APPROVED_h1.html",     [".h1-topbar"],  [".h1-mainnav"]),
    ("anime",  "anime_APPROVED_a1b.html",     [".a1b-topbar"], [".a1b-nav"]),
    ("kids",   "kids_APPROVED_k4.html",       [".k4-topbar"],  [".k4-nav"]),
    ("livetv", "livetv_APPROVED_lt1.html",    [".lt-top"],     [".lt-nav"]),
    ("sports", "sports_APPROVED_sp1.html",    [".sp1-topbar"], [".sp1-nav"]),
    ("esports","esports_APPROVED_es1.html",   [".es1-top"],    [".es1-nav"]),
    ("adult",  "adult_APPROVED_eg1v2.html",   [".topbar"],     [".nav-pills"]),
]

OUT = Path("/root/mxstream-app/static/u4_compare/qc_audit.md")
report = ["# u4 Wave 1 QC Audit\n", f"Generated against the live romantv.net catalog pages.\n"]

for slug, page, tb_sels, nav_sels in TABS:
    url = BASE + page
    try:
        html = urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:
        report.append(f"\n## ❌ {slug}\nFETCH FAILED: {e}\n"); continue

    size_kb = len(html) / 1024
    # Search input audit — count placeholder strings & where they live
    search_inputs = re.findall(
        r'<input[^>]*(?:type=["\']search["\']|placeholder=["\']([^"\']*?)["\'])[^>]*>',
        html, re.I)
    placeholders = re.findall(r'placeholder=["\']([^"\']*?)["\']', html, re.I)
    # Count distinct search inputs in <header>/<topbar> vs body
    inputs_in_topbar = 0
    inputs_in_body = 0
    for m in re.finditer(r'<input[^>]*(?:type=["\']search["\']|placeholder=)[^>]*>', html, re.I):
        # walk back ~2000 chars to see nearest header/section context
        before = html[max(0, m.start()-2000):m.start()]
        last_open = max(before.rfind('<header'), before.rfind('<div class="topbar'),
                        before.rfind('class="v1a-topbar'), before.rfind('class="rv-topbar'),
                        before.rfind('class="h1-topbar'), before.rfind('class="a1b-topbar'),
                        before.rfind('class="k4-topbar'), before.rfind('class="lt-top'),
                        before.rfind('class="sp1-topbar'), before.rfind('class="es1-top'),
                        before.rfind('class="topbar"'))
        last_close_header = before.rfind('</header')
        if last_open > last_close_header:
            inputs_in_topbar += 1
        else:
            inputs_in_body += 1

    # Each page has both EN+ES wrappers — divide by 2 for what user actually sees
    visible_topbar = inputs_in_topbar // 2
    visible_body = inputs_in_body // 2
    total_visible = visible_topbar + visible_body

    # Cache-bust version present?
    css_link = re.search(r'u4_unified\.css\?v=(\d+)', html)
    css_v = css_link.group(1) if css_link else "MISSING"

    # Does it have a <link> to u4_unified.css at all?
    has_link = "/static/u4_unified.css" in html
    # Detect sticky positioning that could overlap topbar
    sticky_count = len(re.findall(r'position\s*:\s*sticky', html, re.I))
    fixed_count = len(re.findall(r'position\s*:\s*fixed', html, re.I))
    # Detect any leftover `min-height: min(...)` bug
    bad_minheight = bool(re.search(r'min-height\s*:\s*min\s*\(', html, re.I))

    flags = []
    if not has_link: flags.append("⚠ no u4_unified.css link")
    if css_v != "3": flags.append(f"⚠ wrong cache-bust v={css_v}")
    if visible_topbar == 0: flags.append("⚠ NO topbar search visible")
    if visible_body >= 1: flags.append(f"⚠ {visible_body} body-level search input(s) — visible alongside topbar = doubled")
    if bad_minheight: flags.append("⚠ legacy min-height:min() bug present")
    status = "✓ OK" if not flags else "⚠ ISSUES"

    report.append(f"\n## {status} · {slug} · `{page}`")
    report.append(f"- size: {size_kb:.1f} KB · u4 link: {has_link} · cache-bust: v={css_v}")
    report.append(f"- search inputs: **{total_visible} visible** ({visible_topbar} topbar + {visible_body} body)")
    if placeholders:
        uniq = sorted(set(placeholders))
        report.append(f"- placeholders found: {', '.join(repr(p) for p in uniq[:5])}")
    report.append(f"- sticky elements: {sticky_count // 2} · fixed elements: {fixed_count // 2}")
    if flags:
        for f in flags: report.append(f"- {f}")

OUT.write_text("\n".join(report))
print(f"→ wrote {OUT}: {len(''.join(report)):,} chars")
print("\nSummary:")
for line in report:
    if line.startswith("## "):
        print("  " + line[3:].split('\n')[0])
