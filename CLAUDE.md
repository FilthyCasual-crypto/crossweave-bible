# Crossweave — working notes for Claude Code

A static, hyperlinked Bible reader. No backend, no build step for the app itself, no runtime
dependencies. `app/index.html` is the entire application; `app/data/` is 17 MB of generated
JSON; `build/` regenerates that JSON from public datasets.

Read `README.md` for what the product is. This file is about how to work on it safely.

---

## Commands

```bash
make serve     # static server on :8000 (the app CANNOT run from file://)
make verify    # data integrity + the ASCII rule - run before every commit
make check     # render all five views headless, fail on any console/page error
make shots     # write screenshots of every view to .shots/ for eyeballing
make sources   # fetch the five upstream datasets into sources/, fail if they drifted
make data      # full data rebuild, in dependency order (refuses to run on drifted sources)
```

`make verify` is cheap and catches the mistakes that have actually shipped. Run it. It is the
same thing as `python3 scripts/verify.py` — use whichever.

`make check` runs 26 assertions across all five views and fails on any console or page
error. Two env overrides: `CW_CHROMIUM=/path/to/chromium` to use a browser Playwright did
not install, `CW_BASE=https://host/index.html` to check a deployed build instead of
localhost.

---

## Hard invariants

Breaking any of these produces damage that is silent at build time and wrong in the product.
They are listed in order of how badly they bite.

### 1. Versification is locked at 31,102 verses

Every cross-reference is stored as an **integer index into the canon**, not as a reference
string. `build.py` asserts that the BSB parses to exactly 31,102 verses in the same
versification as the KJV.

**If that assertion fails, do not relax it.** A versification mismatch of even one verse
silently repoints every downstream reference past that point at the wrong verse. There is no
test that will catch it afterwards, because every file will still be well-formed.

The sixteen verses absent from the critical text (Matthew 17:21, 18:11, 23:14; Mark 7:16 and
others) are present in the BSB data as a bracketed note, specifically so the count holds.
Do not "clean them up".

### 2. `app/index.html` must stay pure ASCII

HTML entities in markup (`&mdash;`, `&middot;`, `&ldquo;`), `\uXXXX` escapes inside
`<script>`. `make verify` enforces this and CI fails on it.

A raw curly quote in the source renders as `â€œAnd God said` whenever the page is served
without a charset header. Verse text from the JSON is unaffected, because JSON is UTF-8 by
spec — so this bug only ever appears in strings that live in the HTML, which makes it easy
to reintroduce and easy to miss.

### 3. The cross-reference graph is translation-independent

```
app/data/x/<book>.json        the graph - never per-translation
app/data/<trans>/<book>.json  the text - one directory per translation
```

Adding a translation = 66 JSON files in a new directory + one entry in the `trans` array of
`index.json`. Nothing else. Do not fold text and references back into one file; that was the
original layout and it made the KJV addition a rewrite instead of a drop-in.

### 4. Sourced and approximate map boundaries must stay visually distinct

openBible supplies boundaries for 19 regions. `build/kingdoms.py` contains **13 hand-drawn
approximate extents** because the gazetteer has no "Israel" and no "Judah" at all.

Sourced boundaries render **solid**. Hand-drawn extents render **dashed**, carry a period
label, and the legend says they are schematic.

**Preserve that distinction through any redesign.** A schematic border presented as a
surveyed one is the most misleading thing a Bible atlas can do. If a redesign makes them look
alike, the redesign is wrong, not the rule.

### 5. Place links are matched at build time, never guessed at runtime

`spans.py` asks the gazetteer which places a verse mentions, finds the longest matching
surface form in that verse's actual text, and emits character offsets. The renderer only
wraps spans it was handed.

Current match rate: **89.2% BSB / 94.4% KJV**. Do not chase a higher number with runtime
regex — the misses are places referred to by pronoun, and a wrong link costs more trust than
a missing one. The kinship guard in `spans.py` (suppressing a match after "son of",
"daughter of", etc.) exists because "Lot son of Haran" was linking the person to the town;
it cost 0.6pp of recall and was worth it.

---

## Architecture

```
app/index.html     one file: ~1803 lines, five views, five drawing engines
app/data/          generated, committed, served as static files
build/*.py         regeneration, must run in order (see below)
```

**Five views**, routed by `setView()` over `#v-home|read|web|atlas|places`:
home, read, web (arc diagram), atlas (map), places (gazetteer).

**Verse addressing.** A verse is a global integer 0..31,101. `locate(g)` turns an integer
into `{book, chapter, verse}` by binary search over book start offsets; `gidx(b,c,v)` goes
the other way. Cross-references are `[targetIndex, span, weight]`.

**Everything visual is canvas.** Well over 100,000 arcs and a full vector map are far past the DOM.
The arc view draws once into an offscreen canvas in 9,000-arc chunks across animation frames,
then composites that buffer plus the hovered subset. The map redraws wholesale on pan/zoom,
which is fine at this geometry count.

**Label collision.** Both the map and the arc view place labels through `lblFree()`, which
keeps a list of occupied rectangles and refuses overlaps. Priority order on the map: the
headline place, then kingdoms, then nearby places ranked by scripture frequency. Labels that
would collide are dropped, never stacked.

**Theme.** Everything is CSS custom properties on `:root`, redefined under
`@media (prefers-color-scheme: dark)` guarded with `:root:not([data-theme="light"])` and
again under `:root[data-theme="dark"]`. Canvas code reads the tokens via
`getComputedStyle()` at draw time, so maps and arcs follow the theme. If you add a colour,
add it as a token in all three places or dark mode breaks silently.

**Persistence** is `localStorage` only, wrapped in the `LS` helper, all reads defaulted. Keys:
`cw.pos` (reading position), `cw.view`, `cw.tr` (translation), `cw.th`, `cw.fs`, `cw.lw`,
`cw.dens`, `cw.seen`. Nothing survives a device change — see the roadmap on accounts.

### Build order

```
build.py  ->  arcs.py
          ->  geo.py  ->  spans.py  ->  journeys.py
              kingdoms.py (independent)
```

`geo.py` writes `.build-cache/mentions.json`, which `spans.py` consumes. `journeys.py` reads the span
files `spans.py` writes. Run them out of order and you get stale or empty output with no error.

### Totals and source checksums live in `data-baseline.json`

The sources are fetched from upstream, not vendored, and upstream republishes: openBible
replaced `cross_references.txt` on 2026-10-26, and the file the original data was built
from no longer exists anywhere. So the expected totals (edges, chapter links, linked verses,
places, journeys, kingdoms) and the sha256 of every source file are checked in at the repo
root. `verify.py` and `check.mjs` assert against that file, never against `index.json`,
which the build writes itself. The verse count stays invariant 1; the edge count is **not**
an invariant and is deliberately not written anywhere in this file.

`make sources` fails when a download no longer matches its checksum, and `make data` refuses
to run on drifted sources. That failure is not a build error, it is a decision:

- **Re-baseline** (the default): `python3 scripts/check_sources.py --rebaseline` records the
  new checksums and date, `make data` rebuilds, and `verify.py` then reports each total that
  moved. In **one commit**, update the totals in `data-baseline.json`, the figures in
  `README.md`, and the few literal counts in `app/index.html` (the home card meta and the
  palette entry for The Web). Say in the commit message what upstream changed and by how
  much.
- **Never** edit a number in `data-baseline.json` just to make `verify.py` pass, and never
  rebuild on drifted sources without re-baselining. Both hide the change instead of
  recording it.

---

## Conventions

- **Vanilla ES5-flavoured JS.** No framework, no bundler, no npm dependency in the app. The
  only dev dependency is Playwright, for `make check`, and it is not shipped.
- **No external requests for data.** No map tiles, no CDN data. Natural Earth vectors are
  vendored as JSON so the geography works offline and inside sandboxed embeds. The one
  exception is **webfonts**: the page loads EB Garamond and IBM Plex Sans from Google Fonts,
  so offline or in a locked-down embed the type falls back to the declared stacks
  (Georgia / system sans). Vendoring them is roadmap item 9 if true offline matters.
- Build scripts are plain Python 3 stdlib. Keep it that way — no pandas, no shapely. The RDP
  simplifier in `geo.py` is 15 lines for that reason.
- Numbers that line up in columns get `font-variant-numeric: tabular-nums`.
- Copy is written plainly. No "unlock", no "seamless", no exclamation marks.

---

## Gotchas that have cost time

- **`file://` does not work.** The app fetches its data; browsers block that on file URLs.
  Always `make serve`.
- **Sizing canvas before its container is visible** gives a zero-width canvas. `setView()`
  shows the view first, then calls `sizeMap()` / `resizeArc()` on a timeout.
- **`[hidden]` loses to `display:grid`.** The stylesheet declares
  `[hidden]{display:none!important}` explicitly; don't remove it.
- **Writing `\uXXXX` through a JSON tool parameter** produces a literal character in the
  file, not an escape. If you generate HTML from a script, post-process to ASCII and let
  `make verify` confirm.
- **openBible has duplicate place names with different referents.** "Moab 1" is the kingdom
  (162 verses); "Moab 2" is the plains of Moab (12 verses) and is the one carrying a
  boundary polygon. Do not merge them to borrow geometry. The UI shows the gazetteer id as a
  disambiguator wherever a display name is shared.
- **Never patch generated JSON by hand.** Two fields were once added to `places.json` and
  `kingdoms.json` directly instead of in the build scripts; the next `make data` silently
  dropped the verse counts and the whole Moab extent. `verify.py` now asserts both, but the
  rule is: change the script, then rebuild.
- **The build must stay deterministic.** `geo.py` once sorted surface forms by `-len` alone,
  which left ties to set iteration order and produced a different file on every run. Sort keys
  must be total orders.

---

## Where to pick up

`docs/ROADMAP.md` has the prioritised list with acceptance criteria. The top item is
**full-text search of scripture**, which is the conspicuous gap in a Bible app and needs a
built inverted index shipped as static shards, not a runtime scan.

Before any commit: `make verify && make check`.
