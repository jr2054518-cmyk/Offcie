# RomanTV — Open Bugs (as of last sync)

## P0 — Functional / blocking

### 1. Nav tabs don't navigate
**Symptom:** clicking any nav tab (Home/Movies/Series/Anime/Live TV/Sports/Esports/18+) on any catalog page does nothing.
**Cause:** mockup HTML uses `<button onclick="toast('Movies')">` or `<a href="#">` placeholders instead of `<a href="/movies">`.
**Counts (from audit):**
- index.html: 19 toast-buttons
- livetv.html, sports.html: 1 toast-button each
- All 9 tabs: 0 real-nav anchors
**Fix needed:** convert nav `<button>` / `<a href="#">` to `<a href="/<route>">` in all 9 production HTML files.
**Status:** identified, not yet fixed.

---

## P1 — Visual

### 2. Series hero scattered into wrong columns
**Symptom:** "PICK UP WHERE YOU LEFT OFF" kicker, "Breaking Bad" title, description, and 3 CTAs (Resume/From Start/Episode Guide) appear scattered across columns instead of left-stacked like Movies.
**Cause:** likely leftover bespoke `#h1.design` 3-column grid surviving the unified hero rule.
**Status:** identified, not yet fixed.

### 3. Anime hero split wrong (kicker+desc left, title+CTAs right)
**Symptom:** "FULL LATIN-AM DUB" kicker + description in left column, "One Piece · Latin-Am dub · Saga 4" title + Play/Episode list in right column.
**Cause:** similar to Series — bespoke `.a1b-` 2-col grid not stripped.
**Status:** identified, not yet fixed.

### 4. Home — UP NEXT row tile heights inconsistent
**Symptom:** in the rotating spotlight's UP NEXT row, some tiles render different heights (one was visibly empty/dark).
**Cause:** TBD — possibly missing poster URLs for some slides.
**Status:** identified, not yet diagnosed.

### 5. Home — "View queue" button floats orphaned
**Symptom:** the "View queue" pill renders below the hero, left-aligned, outside any clear container — looks accidentally placed.
**Cause:** missing wrapper or spacing rule.
**Status:** identified, not yet fixed.

### 6. Home — secondary spotlight poster peeks from right edge during transition
**Symptom:** during slide rotation, a 2nd poster (e.g. Crime 101 cast collage) is partially visible cut off on the right edge.
**Cause:** rotation slides are absolute-positioned and one may have z-index conflict during fade.
**Status:** identified, not yet fixed.

---

## P2 — Coverage gaps

### 7. Mobile (414×896) verification not done
**Status:** unified CSS has `@media (max-width: 480px)` block — not visually verified on any tab.
**Action needed:** open each catalog page in browser at 414×896, screenshot, document issues.

### 8. TV box (1920×1080+) verification not done
**Status:** unified CSS has `@media (min-width: 1920px)` block — not visually verified.
**Action needed:** same as above at 1920×1080.

### 9. Continue Watching tile heights on Home inconsistent
**Symptom:** the CW row shows landscape-aspect tiles (16:9) but heights vary slightly.
**Cause:** TBD.
**Status:** identified, not yet diagnosed.

### 10. Live TV "Also live now" sub-row card title bleed (POSSIBLY FIXED)
**Symptom (was):** TOP NEWS / TOP SPORTS / TOP NOVELA cards showed oversized truncated titles ("Noticier", "TUDN ·", "Las") because `.hero-title` font sizing bled into the sub-row cards.
**Fix attempted:** Wave 3 changed those card headlines from `.hero-title` to `.tile-title`.
**Status:** unverified post-fix.

---

## What I'd do next session

1. Fix #1 (nav navigation) — surgical replace of toast-buttons with `<a href>` anchors
2. Fix #2/#3 (Series + Anime hero columns) — strip remaining bespoke grid rules
3. Resume verification sweep — check every tab top-to-bottom on laptop/mobile/TV
4. Then move to ROUND 2 (detail pages: F-1 to F-7) per master task list
