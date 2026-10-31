#!/usr/bin/env python3
"""Data-integrity and source-hygiene checks. Cheap; run before every commit."""
import json, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'app')
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond


# Expectations live in data-baseline.json, NOT in index.json: the build writes index.json
# itself, so checking the data against it can never catch upstream drift.
BASE = json.load(open(os.path.join(ROOT, 'data-baseline.json')))
T = BASE['totals']
REBASE = "If upstream changed, re-baseline deliberately (see CLAUDE.md), do not edit this number to match."

idx = json.load(open(os.path.join(APP, 'data/index.json')))
books = idx['books']

check(len(books) == T['books'], f"expected {T['books']} books, found {len(books)}")
check(idx['totalVerses'] == T['verses'], f"versification changed: {idx['totalVerses']} != {T['verses']}")
check(len(idx['trans']) == T['translations'],
      f"{len(idx['trans'])} translations, baseline expects {T['translations']}")
check(sum(idx['linked']) == T['linked_verses'],
      f"{sum(idx['linked'])} verses carry cross-references, baseline expects {T['linked_verses']}. " + REBASE)

# book offsets must be contiguous and sum to the total
run = 0
for i, b in enumerate(books):
    check(b['s'] == run, f"book {i} ({b['n']}) start offset {b['s']} != {run}")
    run += sum(b['c'])
check(run == idx['totalVerses'], f"chapter lengths sum to {run}, not {idx['totalVerses']}")

# every translation complete, and every book the right shape
for tr in idx['trans']:
    for bi, b in enumerate(books):
        p = os.path.join(APP, 'data', tr['id'], f'{bi}.json')
        if not check(os.path.exists(p), f"{tr['id']}: missing book {bi}"):
            continue
        t = json.load(open(p))
        if not check(len(t) == len(b['c']), f"{tr['id']} {b['n']}: {len(t)} chapters, expected {len(b['c'])}"):
            continue
        for ci, n in enumerate(b['c']):
            check(len(t[ci]) == n, f"{tr['id']} {b['n']} {ci+1}: {len(t[ci])} verses, expected {n}")

# cross-reference graph: present, in range, well-formed
edges = 0
for bi, b in enumerate(books):
    p = os.path.join(APP, 'data/x', f'{bi}.json')
    if not check(os.path.exists(p), f"missing cross-references for book {bi}"):
        continue
    x = json.load(open(p))
    n = sum(b['c'])
    for off, lst in x.items():
        check(0 <= int(off) < n, f"book {bi}: offset {off} outside book")
        for e in lst:
            check(len(e) == 3, f"book {bi} offset {off}: malformed edge {e}")
            check(0 <= e[0] < idx['totalVerses'], f"book {bi} offset {off}: target {e[0]} out of range")
            edges += 1
check(edges == T['edges'],
      f"counted {edges} cross-references, baseline expects {T['edges']}. " + REBASE)
# a different failure from drift: a partial build leaves index.json describing other data
check(edges == idx['totalEdges'], f"index.json disagrees with the data it describes: "
                                  f"counted {edges} edges, index.json claims {idx['totalEdges']}")

arcs = json.load(open(os.path.join(APP, 'data/arcs.json')))
check(len(arcs['a']) == T['chapter_links'],
      f"{len(arcs['a'])} chapter links, baseline expects {T['chapter_links']}. " + REBASE)

# geo layer
for f in ('arcs.json', 'geo/base.json', 'geo/places.json', 'geo/kingdoms.json', 'geo/journeys.json'):
    check(os.path.exists(os.path.join(APP, 'data', f)), f"missing data/{f}")

places = json.load(open(os.path.join(APP, 'data/geo/places.json')))['places']
check(len(places) == T['places'], f"{len(places)} places, baseline expects {T['places']}. " + REBASE)
for pid, pl in places.items():
    check(isinstance(pl.get('c'), list) and len(pl['c']) == 2, f"place {pid} has no coordinate pair")
    # these were once patched into the JSON instead of emitted by geo.py, so a rebuild
    # silently dropped them and took the gazetteer sort and map thinning with them
    check(isinstance(pl.get('v'), int), f"place {pid} ({pl.get('n')}) has no verse count")
    check(pl.get('id') == pid, f"place {pid} id field does not match its key")
    check(pl.get('forms'), f"place {pid} ({pl.get('n')}) has no surface forms")

kings = json.load(open(os.path.join(APP, 'data/geo/kingdoms.json')))
check(len(kings) == T['kingdoms'],
      f"{len(kings)} kingdom extents, baseline expects {T['kingdoms']}; Moab was once lost this way")
for k in kings:
    check(k.get('n') and k.get('p'), f"kingdom {k.get('id')} missing name or period")
    check(len(k.get('poly') or []) >= 4, f"kingdom {k.get('id')} polygon too small")

# journey stops must point at real places
jr = json.load(open(os.path.join(APP, 'data/geo/journeys.json')))
check(len(jr) == T['journeys'], f"{len(jr)} journeys, baseline expects {T['journeys']}")
_bk = {b['n']: i for i, b in enumerate(books)}
def _ref_key(r):
    name, cv = r.rsplit(' ', 1); ch, v = cv.split(':')
    return (_bk[name], int(ch), int(v))
for j in jr:
    for w in j['w']:
        check(w['p'] in places, f"journey {j['id']}: stop {w['p']} not in gazetteer")
    # stops resolve by walking forward through the passage; a verse that goes backwards means
    # a return visit got its first-mention verse (or the wrong same-named place) again
    keys = [_ref_key(w['r']) for w in j['w']]
    for k in range(1, len(keys)):
        check(keys[k] >= keys[k-1], f"journey {j['id']}: stop {k+1} {j['w'][k]['n']} "
                                    f"({j['w'][k]['r']}) comes before stop {k} ({j['w'][k-1]['r']})")

# span files cover every translation and book
for tr in idx['trans']:
    for bi in range(66):
        check(os.path.exists(os.path.join(APP, 'data/geo', f"{tr['id']}-{bi}.json")),
              f"missing place spans for {tr['id']} book {bi}")

# full-text search index: present for every translation, and not stale. Rebuilding it in
# memory and comparing is the only check that catches "text rebuilt, search.py not re-run",
# which would otherwise ship results that point at the wrong verses with no error anywhere.
sys.path.insert(0, os.path.join(os.path.dirname(APP), 'build'))
import search as _search
_mp = os.path.join(APP, 'data/s/meta.json')
if check(os.path.exists(_mp), "missing data/s/meta.json - run build/search.py"):
    _meta = json.load(open(_mp))
    check(_meta['stop'] == _search.STOP, "data/s/meta.json stoplist differs from build/search.py - rebuild")
    for tr in idx['trans']:
        t = tr['id']
        _d = os.path.join(APP, 'data/s', t)
        if not check(os.path.isdir(_d) and t in _meta['shards'], f"search: no index for {t} - run build/search.py"):
            continue
        _want = _search.shards_of(_search.index(t)[0])
        _have = sorted(f[:-5] for f in os.listdir(_d) if f.endswith('.json'))
        check(_have == sorted(_want) == _meta['shards'][t],
              f"search {t}: shard files, meta.json and a fresh build disagree on the shard list - rebuild")
        _stale = [k for k in _want if k in _have and
                  open(os.path.join(_d, k + '.json'), encoding='ascii').read() != _search.body(_want[k])]
        check(not _stale, f"search {t}: {len(_stale)} shards are stale against the text "
                          f"(e.g. {_stale[:3]}) - run build/search.py")

# the ASCII rule - see CLAUDE.md invariant 2
html = open(os.path.join(APP, 'index.html'), encoding='utf-8').read()
bad = sorted({c for c in html if ord(c) > 127})
check(not bad, f"index.html must stay pure ASCII; found {bad!r} "
               "(use HTML entities in markup, \\uXXXX escapes in script)")

# INVARIANT 4 (CLAUDE.md): a hand-drawn kingdom extent must never render solid. An empty
# dash array on the "containing polity" branch is exactly how that regressed once
# (setLineDash(here?[]:[4,5])). This is a tripwire for a careless edit, not a proof: it flags
# any ternary that yields an empty array, in either branch, whether passed to setLineDash
# directly or through a variable. A determined rewrite gets past any grep; the real guard is
# the comment at the call site plus review. The file has no legitimate `cond ? [] : x`, so a
# hit here means look, not necessarily wrong - if it is legitimate, say why in a comment and
# narrow this pattern rather than deleting it.
_dense = re.sub(r'\s+', '', html)
_solid = re.findall(r'.{0,40}(?:\?\[\]:|\?[^;:?]*:\[\][);,])', _dense)
check(not _solid,
      f"invariant 4: a ternary yields an empty dash array, which draws an approximate kingdom "
      f"solid - solid is reserved for openBible sourced boundaries: {_solid}")

# a literal \uXXXX escape inside markup renders as text, not a character
head = html.split('<script>')[0]
stray = re.findall(r'\\u[0-9A-Fa-f]{4}', head)
check(not stray, f"literal {stray} in markup - use an HTML entity there, not a JS escape")

if fails:
    print(f"FAIL ({len(fails)})")
    for f in fails[:40]:
        print('  -', f)
    if len(fails) > 40:
        print(f'  ... and {len(fails)-40} more')
    sys.exit(1)

print(f"ok  {len(books)} books  {idx['totalVerses']:,} verses  {edges:,} cross-references  "
      f"{len(places):,} places  {len(jr)} journeys  {len(idx['trans'])} translations  ASCII clean")
