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


idx = json.load(open(os.path.join(APP, 'data/index.json')))
books = idx['books']

check(len(books) == 66, f"expected 66 books, found {len(books)}")
check(idx['totalVerses'] == 31102, f"versification changed: {idx['totalVerses']} != 31102")

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
check(edges == idx['totalEdges'], f"counted {edges} edges, index.json claims {idx['totalEdges']}")

# geo layer
for f in ('arcs.json', 'geo/base.json', 'geo/places.json', 'geo/kingdoms.json', 'geo/journeys.json'):
    check(os.path.exists(os.path.join(APP, 'data', f)), f"missing data/{f}")

places = json.load(open(os.path.join(APP, 'data/geo/places.json')))['places']
for pid, pl in places.items():
    check(isinstance(pl.get('c'), list) and len(pl['c']) == 2, f"place {pid} has no coordinate pair")

# journey stops must point at real places
jr = json.load(open(os.path.join(APP, 'data/geo/journeys.json')))
for j in jr:
    for w in j['w']:
        check(w['p'] in places, f"journey {j['id']}: stop {w['p']} not in gazetteer")

# span files cover every translation and book
for tr in idx['trans']:
    for bi in range(66):
        check(os.path.exists(os.path.join(APP, 'data/geo', f"{tr['id']}-{bi}.json")),
              f"missing place spans for {tr['id']} book {bi}")

# the ASCII rule - see CLAUDE.md invariant 2
html = open(os.path.join(APP, 'index.html'), encoding='utf-8').read()
bad = sorted({c for c in html if ord(c) > 127})
check(not bad, f"index.html must stay pure ASCII; found {bad!r} "
               "(use HTML entities in markup, \\uXXXX escapes in script)")

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

print(f"ok  66 books  {idx['totalVerses']:,} verses  {edges:,} cross-references  "
      f"{len(places):,} places  {len(jr)} journeys  {len(idx['trans'])} translations  ASCII clean")
