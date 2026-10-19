# Attribution and data licences

Crossweave redistributes several third-party datasets. Two of them are CC BY 4.0 and
**require attribution to be preserved**. The application carries that attribution on its
home screen and in the map legend. Do not remove it.

## Scripture text

**Berean Standard Bible (BSB)** — the default reading text.
Dedicated to the public domain on 30 April 2023. The publisher states that "licensing is
not required for any use."
<https://berean.bible/licensing.htm>

**King James Version (KJV)** — public domain.

Sixteen verses absent from the critical text (Matthew 17:21, 18:11, 23:14; Mark 7:16 and
others) are present in the BSB files as a bracketed note rather than omitted, so verse
numbering stays aligned between translations and cross-references pointing at them still
resolve.

### On the NASB

The New American Standard Bible is **not** included and cannot be without a licence. The
Lockman Foundation permits up to 1,000 verses without written permission, capped at 50% of
a work, and never a complete book. This app needs all 31,102 verses and all 66 books —
about 31x the free ceiling. A written licence from Lockman is the only path.
<https://www.lockman.org/digital/>

## Cross-references

**openBible.info cross-reference dataset** — CC BY 4.0.
344,799 community-voted references. Crossweave filters to positive votes, makes every edge
bidirectional, deduplicates overlapping ranges and caps at 24 per verse, yielding 455,806
edges across 30,288 verses.
<https://www.openbible.info/labs/cross-references/>

## Places

**openBible Bible-Geocoding-Data** — CC BY 4.0.
Ancient places, modern location identifications, coordinates, per-verse mentions and
per-translation surface forms. Crossweave uses 1,335 places that carry coordinates, and the
19 region boundaries the dataset publishes inline.
<https://github.com/openbibleinfo/Bible-Geocoding-Data>

That dataset in turn incorporates OpenStreetMap data, licensed ODbL 1.0.

## Modern geography

**Natural Earth** — public domain.
1:50m admin-0 country boundaries, clipped to the biblical world and simplified with
Ramer-Douglas-Peucker to 154 rings / 120 KB.
<https://www.naturalearthdata.com/>

## Kingdom extents

**Hand-drawn for this project.** Not sourced from any dataset. Drawn coarsely from standard
historical atlases, labelled "approximate extent", and rendered dashed to distinguish them
from sourced boundaries. See the warning in `README.md`.

## Journey routes

**Curated for this project**, from the narrative of each passage. The stop names are
editorial; the verse reference attached to each stop is resolved against the openBible
per-verse place data, so every stop is checkable against the text.

---

## Required notice

If you redistribute this application or its data, carry forward at minimum:

> Cross-reference and place data from openBible.info, licensed CC BY 4.0.
> Modern geography from Natural Earth (public domain).
> Scripture text: Berean Standard Bible (public domain) and King James Version (public domain).
