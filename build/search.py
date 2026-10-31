#!/usr/bin/env python3
"""Full-text search index: verse text -> data/s/<trans>/<shard>.json + data/s/meta.json.

Reads the per-book text that build.py writes (app/data/<trans>/<book>.json), so it must run
after build.py. One inverted index per translation: the BSB and KJV share versification,
not vocabulary.

Tokens: NFKD, combining marks dropped, lowercased, split on anything that is not a-z or 0-9.
Tokens shorter than two characters and the stoplist below are not indexed. The browser
tokenises queries with the same rule (index.html, `stoks`) and reads the stoplist from
meta.json, so the two cannot drift apart.

Shards are keyed by a token's first two characters, so a query term loads one small file.
Each shard maps token -> postings, the ascending global verse indices delta-encoded and
written as a base-36 string joined with '.', which is about half the size of a JSON int list.

The sixteen BSB verses that are only a bracketed omission note are not indexed: they hold
no scripture text, and a search for "omitted" or "manuscripts" should not return them.
"""
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "app", "data")
OUT = os.path.join(DATA, "s")

# Function words only. Anything a reader might plausibly look up stays indexed, even when
# common ("lord", "god", "said"): ranking by rarity handles those, dropping them would not.
STOP = sorted(set("""
a an and are as at be but by for from had has have he her him his i in is it its me my
of on or our she so that the their them then there they this to was we were which who
will with you your ye thee thou thy unto shall upon not
""".split()))

TOKEN = re.compile(r"[a-z0-9]+")
NOTE = re.compile(r"^\s*\[[^\]]*\]\s*$")


def tokens(text):
    t = unicodedata.normalize("NFKD", text)
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
    return [w for w in TOKEN.findall(t) if len(w) >= 2]


def b36(n):
    if n == 0:
        return "0"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = "0123456789abcdefghijklmnopqrstuvwxyz"[r] + s
    return s


def encode(post):
    out, prev = [], 0
    for g in post:
        out.append(b36(g - prev))
        prev = g
    return ".".join(out)


def index(trans, stop=frozenset(STOP)):
    """token -> ascending global verse indices, and the number of note verses skipped.
    scripts/verify.py calls this too, to prove the committed shards are not stale."""
    post = {}
    g = 0
    skipped = 0
    for b in range(66):
        with open(os.path.join(DATA, trans, f"{b}.json"), encoding="utf-8") as f:
            book = json.load(f)
        for chapter in book:
            for verse in chapter:
                if NOTE.match(verse):
                    skipped += 1
                else:
                    for w in set(tokens(verse)):
                        if w not in stop:
                            post.setdefault(w, []).append(g)
                g += 1
    assert g == 31102, f"{trans}: {g} verses, expected 31,102 (CLAUDE.md invariant 1)"
    return post, skipped


def shards_of(post):
    shards = {}
    for w in sorted(post):
        shards.setdefault(w[:2], {})[w] = encode(post[w])
    return shards


def body(shard):
    return json.dumps(shard, separators=(",", ":"), sort_keys=True)


def build(trans):
    post, skipped = index(trans)
    shards = shards_of(post)
    d = os.path.join(OUT, trans)
    os.makedirs(d, exist_ok=True)
    for name in os.listdir(d):
        if name.endswith(".json"):
            os.remove(os.path.join(d, name))
    sizes = {}
    for key in sorted(shards):
        text = body(shards[key])
        with open(os.path.join(d, f"{key}.json"), "w", encoding="ascii") as f:
            f.write(text)
        sizes[key] = len(text)
    big = max(sizes, key=sizes.get)
    print(f"  {trans}: {len(post):,} tokens  {len(shards)} shards  "
          f"{sum(sizes.values()) / 1e6:.1f} MB  largest {big!r} {sizes[big] / 1e3:.0f} KB  "
          f"{skipped} note verses skipped")
    return sorted(shards), len(post)


def main():
    with open(os.path.join(DATA, "index.json"), encoding="utf-8") as f:
        trans = [t["id"] for t in json.load(f)["trans"]]
    meta = {"stop": STOP, "shards": {}, "tokens": {}}
    for t in trans:
        meta["shards"][t], meta["tokens"][t] = build(t)
    with open(os.path.join(OUT, "meta.json"), "w", encoding="ascii") as f:
        json.dump(meta, f, separators=(",", ":"), sort_keys=True)


if __name__ == "__main__":
    main()
