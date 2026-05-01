#!/usr/bin/env python3
"""u4 Wave 1 fix — search bar QC.

Findings from /root/mxstream-app/static/u4_compare/qc_audit.md:
  • 18+ (eg1v2): topbar search + body-level .search-wide form = 2 visible searches
  • esports (es1): .es1-search is a <div>, not an <input> — no real search at all

Fix:
  • 18+: remove the .search-wide block in BOTH lang-en and lang-es (4 occurrences total).
    The topbar search already exists with the same placeholder.
  • esports: replace `<div class="es1-search" role="search">…</div>` with a real
    <form><input type="search">. Also keep the EN+ES variant intact.

Idempotent — safe to re-run.
"""
import re
from pathlib import Path

CATALOG = Path("/root/mxstream-app/static/mockups/CATALOG")
ADULT = CATALOG / "adult_APPROVED_eg1v2.html"
ESPORTS = CATALOG / "esports_APPROVED_es1.html"

# ─── 18+ fix: remove duplicate .search-wide blocks ─────────────────────────
src = ADULT.read_text()
PATTERN = re.compile(
    r'<div class="search-wide">\s*<form[^>]*>\s*<label[^>]*>[^<]*</label>\s*'
    r'<input[^>]*id="eg1-main-q"[^>]*/>\s*</form>\s*</div>\s*',
    re.S
)
matches = PATTERN.findall(src)
new = PATTERN.sub("", src)
removed = len(matches)
if new != src:
    ADULT.write_text(new)
    print(f"✓ 18+: removed {removed} .search-wide block(s) ({len(src):,} → {len(new):,} chars)")
else:
    print(f"  18+: no .search-wide blocks found (already clean)")

# ─── esports fix: turn the <div> into a real <input> form ──────────────────
src = ESPORTS.read_text()

# EN search
EN_DIV = re.compile(
    r'<div class="es1-search" role="search" aria-label="Search teams, players, tournaments">[^<]*</div>',
    re.S
)
EN_FORM = (
    '<form class="es1-search" role="search" aria-label="Search teams, players, tournaments" '
    'onsubmit="event.preventDefault(); openSearch(this.q.value);">'
    '<input id="es1-q-en" name="q" type="search" autocomplete="off" '
    'placeholder="Search teams, players, tournaments…" enterkeyhint="search" />'
    '</form>'
)
ES_DIV = re.compile(
    r'<div class="es1-search" role="search" aria-label="Buscar equipos, jugadores, torneos">[^<]*</div>',
    re.S
)
ES_FORM = (
    '<form class="es1-search" role="search" aria-label="Buscar equipos, jugadores, torneos" '
    'onsubmit="event.preventDefault(); openSearch(this.q.value);">'
    '<input id="es1-q-es" name="q" type="search" autocomplete="off" '
    'placeholder="Buscar equipos, jugadores, torneos…" enterkeyhint="search" />'
    '</form>'
)

en_count = len(EN_DIV.findall(src))
new = EN_DIV.sub(EN_FORM, src, count=1)  # only the first one (lang-en wrapper)
es_count = len(ES_DIV.findall(new))
if es_count > 0:
    new = ES_DIV.sub(ES_FORM, new, count=1)
else:
    # EN block may exist twice (once in lang-en, once in lang-es) if Cursor never
    # produced a Spanish variant. Replace the SECOND EN block with ES form.
    if en_count >= 2:
        # find second occurrence
        m_iter = list(EN_DIV.finditer(src))
        if len(m_iter) >= 2:
            second = m_iter[1]
            new = src[:second.start()] + ES_FORM + src[second.end():]
            # plus apply the first-block EN replacement on top
            new = EN_DIV.sub(EN_FORM, new, count=1)

if new != src:
    # backup once
    bak = ESPORTS.with_suffix(".html.bak_w1search")
    if not bak.exists(): bak.write_text(src)
    # also need to update the inline CSS so .es1-search input renders correctly
    # Grep showed the rule already targets `#es1 .es1-search { ... }` styling for div.
    # We need to make sure inputs inside that class also pick up the unified styling
    # which they will via my u4_unified.css selector `.es1-top input[type=search]`.
    # No CSS change needed — just fix HTML structure.
    ESPORTS.write_text(new)
    print(f"✓ esports: converted {en_count} EN + {es_count} ES <div class=es1-search> to real <form><input> ({len(src):,} → {len(new):,} chars)")
else:
    print(f"  esports: no .es1-search divs found to convert (already fixed)")

print("\nQC fix complete. Re-run /root/mxstream_debug/u4_qc_audit.py to confirm.")
