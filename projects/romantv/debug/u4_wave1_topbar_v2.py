#!/usr/bin/env python3
"""u4 Wave 1 v2 — FIXED unified top-bar across all 9 catalog tabs.

v1 bug: `{SELECTORS} input[type=text]` syntax only adds suffix to LAST item in
list. CSS treated `.v1a-topbar`, `.rv-topbar` etc. as bare selectors and
applied input styles (44px height) directly to the topbars themselves.

v2 fix: helper `desc()` distributes a descendant suffix across every selector
in a comma-separated list, producing proper CSS.
"""
from pathlib import Path

CATALOG = Path("/root/mxstream-app/static/mockups/CATALOG")
CSS_OUT = Path("/root/mxstream-app/static/u4_unified.css")

TOPBAR = [
    ".v1a-topbar", ".rv-topbar", ".h1-topbar", ".a1b-topbar", ".k4-topbar",
    ".lt-top", ".sp1-topbar", ".es1-top",
    # 18+ tab uses generic .topbar inside .lang-wrap > .design — descendant match
    ".lang-wrap .design > .topbar"
]
NAV = [
    ".v1a-nav", ".rv-nav", ".h1-mainnav", ".a1b-nav", ".k4-nav",
    ".lt-nav", ".sp1-nav", ".es1-nav", ".lang-wrap .nav-pills"
]


def desc(selectors, suffix=""):
    """Distribute suffix across each selector. desc(['.a','.b'], ' input') -> '.a input, .b input'"""
    if suffix:
        return ", ".join(f"{s}{suffix}" for s in selectors)
    return ", ".join(selectors)


# Pre-compute common selector groups
TOPBAR_S = desc(TOPBAR)
NAV_S = desc(NAV)
NAV_LINKS = desc(NAV, " a") + ", " + desc(NAV, " button")
NAV_LINKS_HOVER = desc(NAV, " a:hover") + ", " + desc(NAV, " button:hover")
TOPBAR_INPUT_SEARCH = desc(TOPBAR, " input[type=search]")
TOPBAR_INPUT_TEXT = desc(TOPBAR, " input[type=text]")
TOPBAR_INPUT_PLACEHOLDER = desc(TOPBAR, " input[placeholder]")
TOPBAR_SEARCH_FOCUS = desc(TOPBAR, " input[type=search]:focus")
TOPBAR_TEXT_FOCUS = desc(TOPBAR, " input[type=text]:focus")

# Active-state aliases — every variant any tab uses. Tabs aren't required to
# converge on a single class name; the unified CSS accepts all of them so
# the gold underline always renders on the current tab.
ACTIVE_VARIANTS = [
    ".is-active", ".active", ".is-on", ".on",
    ".v1a-active", ".rv-active", ".h1-active", ".a1b-active",
    ".k4-active", ".lt-active", ".sp1-active", ".es1-active",
    ".nav-link--active", "[aria-current=page]",
]
def _active_selectors(suffix=""):
    parts = []
    for tag in (" a", " button"):
        for v in ACTIVE_VARIANTS:
            parts.append(desc(NAV, f"{tag}{v}{suffix}"))
    return ",\n  ".join(parts)
NAV_LINKS_ACTIVE = _active_selectors("")
NAV_LINKS_ACTIVE_AFTER = _active_selectors("::after")
DPAD_NAV_FOCUS = "body.input-dpad " + desc(NAV, " a:focus").replace(", ", ", body.input-dpad ") + ", body.input-dpad " + desc(NAV, " button:focus").replace(", ", ", body.input-dpad ")
DPAD_TOPBAR_BTN_FOCUS = "body.input-dpad " + desc(TOPBAR, " button:focus").replace(", ", ", body.input-dpad ")

CSS = f"""/* ═══════════════════════════════════════════════════════════════════
   RomanTV u4 UNIFIED — applied across all 9 catalog tabs
   Wave 1 v2 — top bar + nav, FIXED selector distribution
   3 device classes: laptop · mobile · TV box · D-pad focus
   ═══════════════════════════════════════════════════════════════════ */

:root {{
  --u4-red: #ff0a14;
  --u4-tb-h: 72px;
  --u4-tb-h-mob: 56px;
  --u4-tb-h-tv: 88px;
}}

/* ─── TOP BAR container ─── */
{TOPBAR_S} {{
  min-height: var(--u4-tb-h) !important;
  display: flex !important;
  align-items: center !important;
  gap: 16px !important;
  padding: 12px 24px !important;
  background: var(--panel) !important;
  border-bottom: 1px solid var(--line) !important;
  position: relative !important;
  z-index: 100 !important;
  flex-wrap: wrap !important;
}}

/* ─── Search input universal ─── */
{TOPBAR_INPUT_SEARCH},
{TOPBAR_INPUT_TEXT},
{TOPBAR_INPUT_PLACEHOLDER} {{
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
{TOPBAR_SEARCH_FOCUS},
{TOPBAR_TEXT_FOCUS} {{
  border-color: var(--gold) !important;
  background-color: var(--panel) !important;
  box-shadow: 0 0 0 3px rgba(255, 214, 107, 0.18) !important;
}}

/* ─── Suppress legacy sibling magnifier icons (movies + livetv shipped with their own) ─── */
.rv-topbar .rv-search-icon,
.lt-top .lt-search-icon,
.rv-search > .rv-search-icon,
.lt-search-wrap > .lt-search-icon {{
  display: none !important;
}}

/* ─── NAV bar ─── */
{NAV_S} {{
  display: flex !important;
  gap: 4px !important;
  align-items: center !important;
}}
{NAV_LINKS} {{
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
{NAV_LINKS_HOVER} {{
  color: var(--text) !important;
  background: rgba(255, 255, 255, 0.06) !important;
}}

/* Active tab indicator */
{NAV_LINKS_ACTIVE} {{
  color: var(--text) !important;
  background: rgba(255, 214, 107, 0.10) !important;
}}
{NAV_LINKS_ACTIVE_AFTER} {{
  content: '' !important;
  position: absolute !important;
  left: 12px !important;
  right: 12px !important;
  bottom: 6px !important;
  height: 2px !important;
  background: var(--gold) !important;
  border-radius: 2px !important;
}}

/* ─── D-pad focus rings ─── */
{DPAD_NAV_FOCUS},
{DPAD_TOPBAR_BTN_FOCUS} {{
  outline: 4px solid var(--gold) !important;
  outline-offset: 4px !important;
}}

/* ─── Mobile · 360-480px ─── */
@media (max-width: 480px) {{
  {TOPBAR_S} {{
    height: auto !important;
    min-height: var(--u4-tb-h-mob) !important;
    padding: 0 12px !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
    overflow-x: visible !important;
  }}
  {TOPBAR_INPUT_SEARCH},
  {TOPBAR_INPUT_TEXT} {{
    height: 40px !important;
    flex-basis: 100% !important;
    order: 2 !important;
  }}
  {NAV_S} {{
    gap: 2px !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    order: 3 !important;
    flex-basis: 100% !important;
    padding-bottom: 8px !important;
  }}
  {NAV_LINKS} {{
    height: 36px !important;
    padding: 0 10px !important;
    font-size: 13px !important;
    flex-shrink: 0 !important;
  }}
}}

/* ─── TV box · 1920px+ @ 10ft ─── */
@media (min-width: 1920px) {{
  {TOPBAR_S} {{
    height: var(--u4-tb-h-tv) !important;
    padding: 0 32px !important;
    gap: 20px !important;
  }}
  {TOPBAR_INPUT_SEARCH},
  {TOPBAR_INPUT_TEXT} {{
    height: 56px !important;
    max-width: 600px !important;
    border-radius: 28px !important;
    font-size: 16px !important;
  }}
  {NAV_LINKS} {{
    height: 56px !important;
    padding: 0 18px !important;
    font-size: 18px !important;
    border-radius: 12px !important;
  }}
  {DPAD_NAV_FOCUS},
  {DPAD_TOPBAR_BTN_FOCUS} {{
    outline: 6px solid var(--gold) !important;
    outline-offset: 6px !important;
  }}
}}

/* ═══════════════════════════════════════════════════════════════════
   Wave 1 v2 END — Wave 2: hero · Wave 3: tiles+chips · Wave 4: cards
   ═══════════════════════════════════════════════════════════════════ */
"""

CSS_OUT.write_text(CSS)
print(f"→ wrote {CSS_OUT}: {len(CSS):,} chars")

# Sanity check — ensure NO bare topbar selector appears in input rules
bad = [line for line in CSS.split("\n")
       if " input[" in line and ".v1a-topbar," in line.split(" input[")[0]]
if bad:
    print("WARN: possible bare-selector bug:")
    for b in bad[:3]: print(f"  {b[:200]}")
else:
    print("✓ selector distribution sanity check passed")

# Bump cache-bust version (?v=2) so browsers refetch
LINK_TAG_OLD = '<link rel="stylesheet" href="/static/u4_unified.css?v=9">'
LINK_TAG_NEW = '<link rel="stylesheet" href="/static/u4_unified.css?v=10">'

CATALOG_PAGES = [
    "home_APPROVED_v1a.html", "movies_APPROVED_v1.html", "series_APPROVED_h1.html",
    "anime_APPROVED_a1b.html", "kids_APPROVED_k4.html", "livetv_APPROVED_lt1.html",
    "sports_APPROVED_sp1.html", "esports_APPROVED_es1.html", "adult_APPROVED_eg1v2.html",
]
print()
print("Bumping cache-bust v=1 → v=2 in each catalog page:")
for name in CATALOG_PAGES:
    p = CATALOG / name
    if not p.exists():
        print(f"  {name}: MISSING"); continue
    src = p.read_text()
    if LINK_TAG_OLD in src:
        p.write_text(src.replace(LINK_TAG_OLD, LINK_TAG_NEW))
        print(f"  {name}: ✓ bumped to v=2")
    elif LINK_TAG_NEW in src:
        print(f"  {name}: already v=2")
    elif "/static/u4_unified.css" in src:
        # any other version present, leave alone
        print(f"  {name}: link present (different ver) — skipping")
    else:
        # not injected at all; inject fresh
        new = src.replace("</title>", "</title>\n  " + LINK_TAG_NEW, 1)
        if new == src: new = src.replace("</head>", LINK_TAG_NEW + "\n</head>", 1)
        p.write_text(new)
        print(f"  {name}: ✓ injected v=2 fresh")

print("\nWave 1 v2 DONE.")
