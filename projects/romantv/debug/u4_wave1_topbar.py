#!/usr/bin/env python3
"""u4 Wave 1 — unified top-bar across all 9 catalog tabs.

Strategy: write ONE CSS file `/root/mxstream-app/static/u4_unified.css` with
selectors covering all 9 bespoke top-bar/nav class names. Inject a single
<link> tag into each catalog page's <head>. Zero HTML rewrites.

Tab class selectors (from audit):
  Home    .v1a-topbar  .v1a-nav
  Movies  .rv-topbar   .rv-nav
  Series  .h1-topbar   .h1-mainnav
  Anime   .a1b-topbar  .a1b-nav
  Kids    .k4-topbar   .k4-nav
  Live TV .lt-top      .lt-nav
  Sports  .sp1-topbar  .sp1-nav
  Esports .es1-top     .es1-nav
  18+     .topbar      .nav-pills (these are generic — scope tighter)
"""
import re
from pathlib import Path

CATALOG = Path("/root/mxstream-app/static/mockups/CATALOG")
CSS_OUT = Path("/root/mxstream-app/static/u4_unified.css")

# Selector groups — every bespoke class targeted at once
TOPBAR_SELECTORS = ".v1a-topbar, .rv-topbar, .h1-topbar, .a1b-topbar, .k4-topbar, .lt-top, .sp1-topbar, .es1-top, .lang-wrap > .topbar"
NAV_SELECTORS    = ".v1a-nav, .rv-nav, .h1-mainnav, .a1b-nav, .k4-nav, .lt-nav, .sp1-nav, .es1-nav, .lang-wrap .nav-pills"
NAV_LINK_SELECTORS = (
    ".v1a-nav a, .rv-nav a, .h1-mainnav a, .a1b-nav a, .k4-nav a, .lt-nav a, "
    ".sp1-nav a, .es1-nav a, .lang-wrap .nav-pills a, "
    ".v1a-nav button, .rv-nav button, .h1-mainnav button, .a1b-nav button, .k4-nav button, "
    ".lt-nav button, .sp1-nav button, .es1-nav button, .lang-wrap .nav-pills button"
)

CSS = f"""/* ═══════════════════════════════════════════════════════════════════
   RomanTV u4 UNIFIED — applied across all 9 catalog tabs
   Wave 1: top bar + nav (consistent button/link/active-state across)
   3 device classes: laptop · mobile · TV box · D-pad focus
   ═══════════════════════════════════════════════════════════════════ */

:root {{
  --u4-red: #ff0a14;       /* saturated TV-friendly primary */
  --u4-tb-h: 72px;         /* top-bar height laptop */
  --u4-tb-h-mob: 56px;     /* mobile */
  --u4-tb-h-tv: 88px;      /* TV box */
}}

/* ─── TOP BAR container ─── */
{TOPBAR_SELECTORS} {{
  height: var(--u4-tb-h) !important;
  display: flex !important;
  align-items: center !important;
  gap: 16px !important;
  padding: 0 24px !important;
  background: var(--panel) !important;
  border-bottom: 1px solid var(--line) !important;
  position: relative !important;
  z-index: 100 !important;
}}

/* ─── Search input universal ─── */
{TOPBAR_SELECTORS.replace(", ", " input[type=search], ").replace("//", "")} input[type=search],
{TOPBAR_SELECTORS} input[type=text],
{TOPBAR_SELECTORS} input[placeholder] {{
  flex: 1 !important;
  max-width: 520px !important;
  height: 44px !important;
  padding: 0 18px 0 44px !important;
  border-radius: 22px !important;
  border: 1px solid var(--line) !important;
  background: var(--panel2) url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="%23a8a8b0" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>') no-repeat 14px center !important;
  color: var(--text) !important;
  font: 500 14px/1 -apple-system, sans-serif !important;
  outline: none !important;
  transition: border-color .15s, background-color .15s !important;
}}
{TOPBAR_SELECTORS} input[type=search]:focus,
{TOPBAR_SELECTORS} input[type=text]:focus {{
  border-color: var(--gold) !important;
  background-color: var(--panel) !important;
  box-shadow: 0 0 0 3px rgba(255, 214, 107, 0.18) !important;
}}

/* ─── NAV bar ─── */
{NAV_SELECTORS} {{
  display: flex !important;
  gap: 4px !important;
  align-items: center !important;
}}
{NAV_LINK_SELECTORS} {{
  display: inline-flex !important;
  align-items: center !important;
  height: 40px !important;
  padding: 0 14px !important;
  border-radius: 10px !important;
  font: 600 14px/1 -apple-system, sans-serif !important;
  color: var(--dim) !important;
  text-decoration: none !important;
  background: transparent !important;
  border: none !important;
  cursor: pointer !important;
  transition: color .15s, background .15s !important;
  position: relative !important;
}}
{NAV_LINK_SELECTORS.replace(", ", ":hover, ")}:hover {{
  color: var(--text) !important;
  background: rgba(255, 255, 255, 0.06) !important;
}}

/* Active tab indicator — gold underline, applies to .is-active / .active */
{NAV_LINK_SELECTORS.replace(", ", ".is-active, ")}.is-active,
{NAV_LINK_SELECTORS.replace(", ", ".active, ")}.active,
{NAV_LINK_SELECTORS.replace(", ", "[aria-current=page], ")}[aria-current=page] {{
  color: var(--text) !important;
  background: rgba(255, 214, 107, 0.10) !important;
}}
{NAV_LINK_SELECTORS.replace(", ", ".is-active::after, ")}.is-active::after,
{NAV_LINK_SELECTORS.replace(", ", ".active::after, ")}.active::after,
{NAV_LINK_SELECTORS.replace(", ", "[aria-current=page]::after, ")}[aria-current=page]::after {{
  content: '' !important;
  position: absolute !important;
  left: 12px !important;
  right: 12px !important;
  bottom: 6px !important;
  height: 2px !important;
  background: var(--gold) !important;
  border-radius: 2px !important;
}}

/* ─── D-pad focus rings (TV box keyboard nav) ─── */
body.input-dpad {NAV_LINK_SELECTORS.replace(", ", ":focus, ")}:focus,
body.input-dpad {TOPBAR_SELECTORS.replace(", ", " button:focus, ")} button:focus {{
  outline: 4px solid var(--gold) !important;
  outline-offset: 4px !important;
}}

/* ─── Mobile · 360-414px portrait ─── */
@media (max-width: 480px) {{
  {TOPBAR_SELECTORS} {{
    height: var(--u4-tb-h-mob) !important;
    padding: 0 12px !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
  }}
  {TOPBAR_SELECTORS} input[type=search],
  {TOPBAR_SELECTORS} input[type=text] {{
    height: 40px !important;
    flex-basis: 100% !important;
    order: 2 !important;
  }}
  {NAV_SELECTORS} {{
    gap: 2px !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    order: 3 !important;
    flex-basis: 100% !important;
    padding-bottom: 8px !important;
  }}
  {NAV_LINK_SELECTORS} {{
    height: 36px !important;
    padding: 0 10px !important;
    font-size: 13px !important;
    flex-shrink: 0 !important;
  }}
}}

/* ─── TV box · 1920px @ 10ft ─── */
@media (min-width: 1920px) {{
  {TOPBAR_SELECTORS} {{
    height: var(--u4-tb-h-tv) !important;
    padding: 0 32px !important;
    gap: 20px !important;
  }}
  {TOPBAR_SELECTORS} input[type=search],
  {TOPBAR_SELECTORS} input[type=text] {{
    height: 56px !important;
    max-width: 600px !important;
    border-radius: 28px !important;
    font-size: 16px !important;
  }}
  {NAV_LINK_SELECTORS} {{
    height: 56px !important;
    padding: 0 18px !important;
    font-size: 18px !important;
    border-radius: 12px !important;
  }}
  body.input-dpad {NAV_LINK_SELECTORS.replace(", ", ":focus, ")}:focus,
  body.input-dpad {TOPBAR_SELECTORS.replace(", ", " button:focus, ")} button:focus {{
    outline: 6px solid var(--gold) !important;
    outline-offset: 6px !important;
  }}
}}

/* ═══════════════════════════════════════════════════════════════════
   Wave 1 END — top bar + nav unified
   Wave 2 will add hero · Wave 3 tiles+chips · Wave 4 cards
   ═══════════════════════════════════════════════════════════════════ */
"""

CSS_OUT.write_text(CSS)
print(f"→ wrote {CSS_OUT}: {len(CSS):,} chars")

# Inject <link rel="stylesheet" href="/static/u4_unified.css"> into each catalog page
LINK_TAG = '<link rel="stylesheet" href="/static/u4_unified.css?v=1">'

CATALOG_PAGES = [
    "home_APPROVED_v1a.html", "movies_APPROVED_v1.html", "series_APPROVED_h1.html",
    "anime_APPROVED_a1b.html", "kids_APPROVED_k4.html", "livetv_APPROVED_lt1.html",
    "sports_APPROVED_sp1.html", "esports_APPROVED_es1.html", "adult_APPROVED_eg1v2.html",
]

print()
print("Injecting <link> into each catalog page:")
for name in CATALOG_PAGES:
    p = CATALOG / name
    if not p.exists():
        print(f"  {name}: MISSING")
        continue
    src = p.read_text()
    if LINK_TAG in src:
        print(f"  {name}: already injected — skipping")
        continue
    # Inject right after </title> in <head>
    new = src.replace("</title>", "</title>\n  " + LINK_TAG, 1)
    if new == src:
        # fallback: inject right before </head>
        new = src.replace("</head>", LINK_TAG + "\n</head>", 1)
    if new == src:
        print(f"  {name}: COULD NOT INJECT")
        continue
    p.write_text(new)
    print(f"  {name}: ✓ injected")

print("\nWave 1 DONE. Reload any catalog page to see unified top-bar.")
