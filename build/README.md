# Regenerating the data

The build scripts read source datasets this repo does not vendor (they are large, and two
are CC BY — better fetched from the publisher than mirrored here). Put them in `sources/`
and adjust the paths at the top of each script.

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
python3 build/geo.py         # base map + gazetteer (writes /tmp/mentions.json for spans.py)
python3 build/spans.py       # place-name offsets per translation (needs geo.py)
python3 build/kingdoms.py    # hand-drawn kingdom extents
python3 build/journeys.py    # curated routes (needs spans.py)
```

`geo.py` must run before `spans.py`, and `spans.py` before `journeys.py`.

## What each script asserts

`build.py` checks the BSB parses to exactly 31,102 verses in the same versification as the
KJV. If that assertion ever fails, do not relax it — the cross-reference graph is keyed to
verse position, and a versification mismatch silently points every reference at the wrong
verse.
