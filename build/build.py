import json, os, io, re, collections

DATA='/home/claude/isaac-bible/data'
OUT='/home/claude/isaac-bible/app'

OSIS = "Gen Exod Lev Num Deut Josh Judg Ruth 1Sam 2Sam 1Kgs 2Kgs 1Chr 2Chr Ezra Neh Esth Job Ps Prov Eccl Song Isa Jer Lam Ezek Dan Hos Joel Amos Obad Jonah Mic Nah Hab Zeph Hag Zech Mal Matt Mark Luke John Acts Rom 1Cor 2Cor Gal Eph Phil Col 1Thess 2Thess 1Tim 2Tim Titus Phlm Heb Jas 1Pet 2Pet 1John 2John 3John Jude Rev".split()
NAMES = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth","1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra","Nehemiah","Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon","Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah","Malachi","Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians","2 Corinthians","Galatians","Ephesians","Philippians","Colossians","1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","Titus","Philemon","Hebrews","James","1 Peter","2 Peter","1 John","2 John","3 John","Jude","Revelation"]

# ---------- KJV (canonical versification skeleton) ----------
kjv = json.load(open(f'{DATA}/kjv.json'))
KJV = [b['chapters'] for b in kjv]

# ---------- BSB ----------
rows = []
with io.open(f'{DATA}/bsb_bsb.txt', encoding='utf-8-sig') as f:
    for line in f:
        line = line.rstrip('\r\n')
        if '\t' not in line: continue
        ref, txt = line.split('\t', 1)
        m = re.match(r'^(.+?)\s+(\d+):(\d+)$', ref.strip())
        if not m: continue
        rows.append((m.group(2), m.group(3), txt.strip()))
BSB = [[[ '' for _ in ch ] for ch in bk ] for bk in KJV]
i = 0
for bi, bk in enumerate(KJV):
    for ci, ch in enumerate(bk):
        for vi in range(len(ch)):
            BSB[bi][ci][vi] = rows[i][2]; i += 1
assert i == len(rows) == 31102, (i, len(rows))
OMIT = '[Omitted — not found in the earliest manuscripts.]'
for bi in range(66):
    for ci in range(len(BSB[bi])):
        for vi in range(len(BSB[bi][ci])):
            if not BSB[bi][ci][vi]: BSB[bi][ci][vi] = OMIT

TRANS = [
  {'id':'bsb','name':'Berean Standard Bible','short':'BSB','note':'Public domain — dedicated 30 April 2023','data':BSB},
  {'id':'kjv','name':'King James Version','short':'KJV','note':'Public domain','data':KJV},
]

# ---------- index ----------
idx = {}; books = []; g = 0
for bi in range(66):
    books.append({'o':OSIS[bi],'n':NAMES[bi],'c':[len(c) for c in KJV[bi]],'s':g})
    for ci, ch in enumerate(KJV[bi]):
        for vi in range(len(ch)):
            idx[f'{OSIS[bi]}.{ci+1}.{vi+1}'] = g; g += 1

# ---------- cross references ----------
raw = collections.defaultdict(list)
with open(f'{DATA}/cross_references.txt') as f:
    next(f)
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) < 3: continue
        src, dst = p[0], p[1]
        try: votes = int(p[2])
        except: continue
        if votes < 1 or src not in idx: continue
        a, b_ = dst.split('-', 1) if '-' in dst else (dst, dst)
        if a not in idx or b_ not in idx: continue
        s, e = idx[a], idx[b_]
        raw[idx[src]].append((s, min(max(e - s, 0), 30), votes))

sym = collections.defaultdict(dict)
for s, lst in raw.items():
    for (t, span, v) in lst:
        sym[s][(t, span)] = max(sym[s].get((t, span), 0), v)
        sym[t][(s, 0)]    = max(sym[t].get((s, 0), 0), v)

MAXPER = 24
xref = {}; total = 0
for s, d in sym.items():
    kept = []
    for (t, span), v in sorted(d.items(), key=lambda kv: -kv[1]):
        a2, b2 = t, t + span
        if any(not (b2 < a3 or a3b < a2) for (a3, a3b) in [(k[0], k[0]+k[1]) for k in kept]): continue
        kept.append((t, span, v))
        if len(kept) >= MAXPER: break
    xref[s] = [[t, span, v] for (t, span, v) in kept]; total += len(kept)

# ---------- emit ----------
os.makedirs(f'{OUT}/data/x', exist_ok=True)
for tr in TRANS: os.makedirs(f"{OUT}/data/{tr['id']}", exist_ok=True)
for bi, bk in enumerate(books):
    start = bk['s']; n = sum(bk['c'])
    refs = {str(i-start): xref[i] for i in range(start, start+n) if i in xref}
    json.dump(refs, open(f'{OUT}/data/x/{bi}.json','w'), separators=(',',':'))
    for tr in TRANS:
        json.dump(tr['data'][bi], open(f"{OUT}/data/{tr['id']}/{bi}.json",'w'),
                  separators=(',',':'), ensure_ascii=False)

linked = [sum(1 for i in range(b['s'], b['s']+sum(b['c'])) if i in xref) for b in books]
json.dump({'books':books, 'linked':linked, 'totalVerses':g, 'totalEdges':total,
           'trans':[{'id':t['id'],'name':t['name'],'short':t['short'],'note':t['note']} for t in TRANS]},
          open(f'{OUT}/data/index.json','w'), separators=(',',':'))
print('verses',g,'linked',sum(linked),'edges',total)
