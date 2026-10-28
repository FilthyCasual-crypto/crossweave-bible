# Roadmap

Prioritised. Each item states what "done" means, so a session can pick one up and know when
to stop. Items are sized to be finishable in one sitting unless marked otherwise.

---

## 1. Full-text search of scripture — **the conspicuous gap**

Search currently finds references, place names and journeys. It does not find *words*. In a
Bible app that is the first thing a reader reaches for.

**Approach.** Build an inverted index at build time; ship it as static shards. Do not scan
31,102 verses in the browser on every keystroke.

- Tokenise lowercase, strip punctuation, drop a small stoplist (the, and, of, to, …).
- Map token to a list of global verse indices. Roughly 12–14k distinct tokens after
  stemming-free normalisation.
- Shard by first two characters of the token so a query loads one small file, not the index.
- Index the BSB and the KJV separately — they share versification, not vocabulary.

**Done when:** typing three or more characters in the command palette returns matching verses
with the matched term highlighted, ranked by how rare the term is, and selecting one opens
that verse in the reader with its cross-references loaded. Phrase search in quotes works.
Index payload for a typical query is under 150 KB.

**Watch for:** the palette currently assumes a small synchronous result set. Verse results
need to be async and debounced, and must not block the existing reference/place matching.

---

## 2. Confidence rendering on uncertain map stops

The wilderness itinerary (Numbers 33, 66 camps) zigzags across the map. That is not a
rendering bug — the geography is genuinely unresolved and openBible places several camps at
best-guess coordinates far from their neighbours in sequence. Right now the map draws a
confident line through real uncertainty.

`places.json` already carries `nc` — the number of proposed sites for that place. Use it.

**Done when:** a stop whose place has more than one proposed site draws as a hollow ring
rather than a filled dot, the route segments touching it draw dashed, and the legend explains
it in one line. The Numbers 33 route reads as "we are not sure where these were" rather than
"this is the path".

---

## 3. Shareable verse links

Nothing in the app can be linked to. A reader who finds something cannot send it to anyone.

GitHub Pages has no constraint here, but the artifact build only receives a bare `#anchor`
(letters, digits, `.`, `_`, `~`, `-`) — no query string, no `#key=value`. So encode state as
a single token the page decodes itself, e.g. `#v-43-3-16` for John 3:16, `#p-a1b2c3d` for a
place, `#j-2` for a journey.

**Done when:** the reader has a copy-link control, opening such a URL restores that exact
view and selection, and the token survives both GitHub Pages and the artifact sandbox.

---

## 4. Sea legs versus land legs on journeys

Acts distinguishes sailing from walking, and the voyage to Rome is almost entirely sea. One
undifferentiated line makes the route read wrongly.

**Done when:** each journey waypoint carries a mode, sea legs draw as a different stroke
(dashed or lighter) from land legs, and the legend names both. Modes are editorial, set in
`build/journeys.py` alongside the stop list — do not try to infer them.

---

## 5. Bookmarks and notes

Readers want to keep what they find. Browser storage is per-device and per-origin, so this
splits into two very different jobs:

- **Local-only (small):** bookmark a verse, add a note, list them, export as JSON. Works
  today with `localStorage`, no infrastructure, no cost. Do this first.
- **Synced (large, and a business decision):** anything surviving a device change needs
  accounts, which means a server, which means recurring cost. The app is meant to be free.
  Do not start this without an explicit decision about who pays.

**Done when (local):** a bookmark control in the reader, a bookmarks list reachable from the
nav, notes attached to verse references, and an export that round-trips.

---

## 6. Route from the reading pane

Journeys are reachable only from the Atlas. When the open chapter sits inside a journey's
passage, the reader should offer it.

**Done when:** opening Acts 27 shows an unobtrusive "This chapter is part of: The voyage to
Rome" affordance that opens the atlas on that route, and the back button returns to the
chapter.

---

## 7. Book-level banding on the arc view

Orientation currently depends on five landmark labels. A thin band of alternating tone under
the bars, one segment per book, would make the whole axis readable.

**Done when:** book boundaries are visible along the axis at any width, hovering a band names
the book, and it still reads at 400 px wide.

---

## 8. Two-hop reference view

Pick a verse, see what it reaches and what those reach. This is the study move the arc
picture cannot express and the reference list cannot either.

**Done when:** a verse can be expanded to show its references' references, deduplicated,
with the path back to the origin verse visible, capped at a sensible node count.

---

## 9. Vendor the webfonts

`CLAUDE.md` claims no external runtime requests, and that is true of data but not of type: the
page pulls EB Garamond and IBM Plex Sans from Google Fonts. Offline, or inside a locked-down
embed, the type silently falls back to Georgia and the system sans. The layout survives it,
but the identity does not.

**Done when:** both families are subset to the Latin glyphs the app uses, inlined as
`@font-face` data URIs, and the page makes no network request to any host but its own. Keep
the fallback stacks regardless. Budget: under ~250 KB for all weights after subsetting.

---

## Decided against, with reasons

**NASB text.** Requires a written licence from the Lockman Foundation: free use caps at
1,000 verses, 50% of a work, never a complete book; the app needs all 31,102 and all 66
books. See `ATTRIBUTION.md`. The data model makes it a drop-in if a licence is ever
obtained — 66 files plus one `index.json` entry — so nothing is blocked by its absence.

**Mention-order journey routes.** The first implementation derived waypoints from the order
the text names places. It produced plausible garbage: the voyage to Rome ran
Italy → Adramyttium → Asia → Thessalonica before reaching Sidon, because Acts 27:1–2 names
the destination, the ship's home port, the province and a companion's home town before the
ship sails. A line between two points is a claim; mention order does not support it. Routes
are curated and resolved against the text instead.

**Runtime place-name matching.** See invariant 5 in `CLAUDE.md`.

**A backend.** The static design is what makes "free" structurally true. Any proposal that
adds a server should state who pays for it and why the feature cannot be done statically.
