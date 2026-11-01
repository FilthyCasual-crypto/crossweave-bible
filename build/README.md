# Regenerating the data

The build scripts read source datasets this repo does not vendor (they are large, and two
are CC BY — better fetched from the publisher than mirrored here). `make sources` puts them in
`sources/` and checks each against the sha256 in `data-baseline.json`. The scripts resolve
paths from the repo root; set `CW_SOURCES` to read the datasets from somewhere else.

## Fetch the sources

```bash
mkdir -p sources && cd sources

# cross-references (openBible, CC BY) - 8.3 MB
curl -LO https://a.openbible.info/data/cross-references.zip
unzip cross-references.zip          # -> cross_references.txt

# King James Version text - 4.2 MB
curl -L -o kjv.json \
  https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json

# Berean Standard Bible text (public domain) - 4.3 MB
curl -L -o bsb_bsb.txt https://bereanbible.com/bsb.txt

# ASV, YLT, Darby, Webster, BBE (public domain) - 8.4 MB each, pinned to one commit
for t in ASV YLT Darby Webster BBE; do
  curl -L -o $t.json \
    https://raw.githubusercontent.com/scrollmapper/bible_databases/59b18c5af5845728c275d5b7178ad0d024172b1f/formats/json/$t.json
done

# gazetteer (openBible, CC BY) - 15 MB
for f in ancient modern geometry; do
  curl -L -o $f.jsonl \
    https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/main/data/$f.jsonl
done

# modern geography (Natural Earth, public domain) - 3 MB
curl -L -o ne_countries.geojson \
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
```

## Run the build, in order

```bash
python3 build/build.py       # verse text + cross-reference graph
python3 build/arcs.py        # chapter-level arc aggregate (needs build.py output)
python3 build/geo.py         # base map + gazetteer (writes .build-cache/mentions.json for spans.py)
python3 build/spans.py       # place-name offsets per translation (needs geo.py)
python3 build/kingdoms.py    # hand-drawn kingdom extents
python3 build/journeys.py    # curated routes (needs spans.py)
python3 build/search.py      # full-text index per translation (needs build.py)
```

`geo.py` must run before `spans.py`, and `spans.py` before `journeys.py`. `search.py` reads the
text `build.py` writes, so it runs after it; `verify.py` rebuilds the index in memory and fails
if the committed shards are stale against the text.

## What each script asserts

`build.py` checks the BSB parses to exactly 31,102 verses in the same versification as the
KJV. If that assertion ever fails, do not relax it — the cross-reference graph is keyed to
verse position, and a versification mismatch silently points every reference at the wrong
verse.
