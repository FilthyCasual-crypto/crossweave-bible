# Crossweave

A hyperlinked Bible reader. Every verse opens the passages that cross-reference it, every
place name opens a map, and the whole canon can be seen as one picture of its own
cross-references.

**30,288 of 31,102 verses are linked — 97.4%.** That figure is the reason the app exists.

| | |
|---|---|
| Cross-references | 455,832 weighted verse-level links |
| Chapter-to-chapter links | 133,679, of which 29.6% cross between the Testaments |
| Places mapped | 1,335, with modern site names and coordinates |
| Journey routes | 7, each stop keyed to the verse that names it |
| Translations | Berean Standard Bible, King James Version |
| Search | Every word of both translations, phrases in quotes, ranked rarest first |

Everything is static. No backend, no accounts, no database, nothing to pay for — which is
what makes "free" structurally true rather than aspirational.

---

## Use it

- **Online:** <https://filthycasual-crypto.github.io/crossweave-bible/> - nothing to install, works on phones.
- **Offline download:** grab the latest `crossweave-vX.Y.Z.zip` from
  [Releases](https://github.com/FilthyCasual-crypto/crossweave-bible/releases/latest), unzip it, then
  double-click `start.bat` (Windows) or run `sh start.sh` (macOS/Linux). Needs Python 3.

## Running it

The app is plain HTML plus JSON. Any static server works:

```bash
cd app
python3 -m http.server 8000
# open http://localhost:8000
```

Opening `app/index.html` straight off the filesystem will **not** work — the app fetches its
data files, and browsers block `fetch` on `file://`. Use a server.

## Deploying

A GitHub Actions workflow is included at `.github/workflows/pages.yml`. Enable Pages in
**Settings -> Pages -> Source: GitHub Actions** and every push to `main` publishes `app/`.

It is a static directory, so Netlify, Cloudflare Pages, S3, or any web host serves it
equally well. Point the host at `app/`.

---

## How it is built

```
app/
  index.html            the entire application - one file, no build step, no dependencies
  data/
    index.json          book names, chapter lengths, verse offsets, translation list
    bsb/<0-65>.json     Berean Standard Bible, one file per book
    kjv/<0-65>.json     King James Version, one file per book
    x/<0-65>.json       cross-reference graph, keyed by verse offset within the book
    arcs.json           chapter-level aggregate for the whole-canon arc view
    geo/
      base.json         Natural Earth coastlines and national borders, simplified
      places.json       the gazetteer: 1,335 places with coordinates and modern names
      kingdoms.json     13 approximate kingdom extents (see the warning below)
      journeys.json     7 routes, each stop carrying its verse reference
      bsb-<0-65>.json   character offsets of every place name in the BSB text
      kjv-<0-65>.json   the same for the KJV
    s/
      meta.json         stoplist and shard list for full-text search
      bsb/<xx>.json     inverted index, one shard per two-letter token prefix
      kjv/<xx>.json     the same for the KJV
build/
  build.py              verse text + cross-reference graph -> data/index.json, bsb/, kjv/, x/
  arcs.py               verse-level graph -> chapter-level arcs.json
  geo.py                gazetteer + Natural Earth -> geo/base.json, geo/places.json
  spans.py              place-name matching -> geo/<trans>-<book>.json
  kingdoms.py           the hand-drawn approximate kingdom extents
  journeys.py           curated itineraries -> geo/journeys.json
  search.py             verse text -> s/ (full-text index, both translations)
```

### Design decisions worth knowing before you change anything

**Verse positions are global integers.** A verse is identified by its index in the canon
(0 to 31,101). The cross-reference graph stores `[target, span, weight]` triples of
integers, which is what keeps a 455,832-edge graph down to 5.6 MB. A book/chapter offset
table on the client turns any integer back into "John 3:16".

**Text and references are separate layers.** `data/x/` is translation-independent. Adding a
translation is: drop 66 JSON files into `data/<id>/`, add one entry to the `trans` array in
`index.json`. The graph is untouched. This is how KJV was added after BSB, and how NASB
would be added if it were ever licensed.

**Place names are matched at build time, not guessed at runtime.** `spans.py` asks the
gazetteer which places each verse mentions, finds the longest matching surface form in the
actual text, and records character offsets. The renderer only wraps spans it was handed.
Match rate: 89.2% BSB, 94.4% KJV. The gap is places referred to by pronoun, which correctly
produce no link rather than a wrong one.

**Everything is drawn on canvas.** 133,679 arcs and a full vector map are far past what the
DOM handles. The arc view draws once into an offscreen buffer in 9,000-arc chunks across
animation frames, then composites; hover redraws only the highlighted subset.

**The page is pure ASCII.** HTML entities in markup, `\uXXXX` escapes in script. This makes
the file immune to being served without a charset header. Keep it that way — a build script
writing a raw curly quote into the source is how the verse quote once rendered as
`â€œAnd God said`.

### Regenerating the data

The build scripts expect source files the repo does not vendor. See `build/README.md`.

---

## A warning about the kingdom boundaries

openBible's gazetteer has no "Israel" and no "Judah" — it classes them as peoples rather
than mapped places — and publishes boundary polygons for only 19 of its 168 regions.

So `build/kingdoms.py` contains **13 hand-drawn approximate extents**: the United Monarchy,
northern Israel, Judah, Moab, Edom, Phoenicia, New Kingdom Egypt, the Neo-Assyrian,
Neo-Babylonian, Achaemenid Persian and Roman empires, Roman Judea, and Galilee.

These are drawn as **dashed** outlines and labelled "approximate extent" in the map legend,
visually separate from openBible's **solid** sourced boundaries. The legend states that
ancient boundaries were never fixed lines and that each extent is one moment in a kingdom's
history.

**Keep that distinction through any redesign.** A schematic border presented as a surveyed
one is the single most misleading thing a Bible atlas can do, and it is the kind of error
that costs a reader's trust in everything else on the page.

---

## Licence

Application code: MIT, see `LICENSE`.

Scripture text and data: see `ATTRIBUTION.md`. The cross-reference and gazetteer data are
CC BY 4.0 and **require attribution** — the app carries it on the home screen and in the map
legend. Do not remove it.
