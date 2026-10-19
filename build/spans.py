import json, os, re, collections
OUT='/home/claude/isaac-bible/app'
P=json.load(open(f'{OUT}/data/geo/places.json'))['places']
MEN=json.load(open('/tmp/mentions.json'))
IDX=json.load(open(f'{OUT}/data/index.json'))
BOOKS=IDX['books']

pairs=sum(len(v) for v in MEN.values())
print('verse-place pairs:',pairs,'over',len(MEN),'verses')

# pre-compile per place: list of (regex, form)
RX={}
for pid,p in P.items():
    pats=[]
    for f in p['forms']:
        if len(f)<2: continue
        pats.append(re.escape(f))
    if not pats: continue
    RX[pid]=re.compile(r'(?<![A-Za-z’\'-])(' + '|'.join(pats) + r')(?![A-Za-z’\'-])')

PERSON_RX=re.compile(r'\b(son|daughter|father|mother|wife|descendant) of $')

def spans_for(text, pids):
    found=[]
    for pid in pids:
        rx=RX.get(pid)
        if not rx: continue
        for m in rx.finditer(text):
            if not m.group(1)[0].isupper(): continue
            # "Lot son of Haran" is a person, not the town. Singular kinship only:
            # plural forms ("the sons of Javan") are peoples/places and stay linked.
            before = text[max(0, m.start(1)-14):m.start(1)].lower()
            if PERSON_RX.search(before): continue
            found.append([m.start(1), m.end(1), pid])
    if not found: return []
    # longest-first, drop overlaps
    found.sort(key=lambda s:(-(s[1]-s[0]), s[0]))
    out=[]
    for s in found:
        if any(not (s[1]<=o[0] or s[0]>=o[1]) for o in out): continue
        out.append(s)
    out.sort(key=lambda s:s[0])
    return out

for tr in ('bsb','kjv'):
    tot=0; hit=0; miss=collections.Counter()
    for bi in range(66):
        T=json.load(open(f'{OUT}/data/{tr}/{bi}.json'))
        res={}
        for ci,ch in enumerate(T):
            for vi,txt in enumerate(ch):
                key=f'{bi}.{ci+1}.{vi+1}'
                lst=MEN.get(key)
                if not lst: continue
                pids=[x[0] for x in lst] if tr=='bsb' else [x[0] for x in lst if x[1]]
                if not pids: continue
                tot+=len(pids)
                sp=spans_for(txt, pids)
                got={s[2] for s in sp}
                hit+=len(got)
                for pid in pids:
                    if pid not in got: miss[P[pid]['n']]+=1
                if sp: res[f'{ci+1}.{vi+1}']=sp
        json.dump(res, open(f'{OUT}/data/geo/{tr}-{bi}.json','w'), separators=(',',':'))
    print(f'{tr}: matched {hit}/{tot} = {100*hit/max(tot,1):.1f}%  top misses:', miss.most_common(8))

sz=sum(os.path.getsize(f'{OUT}/data/geo/{t}-{b}.json') for t in ('bsb','kjv') for b in range(66))
print('span files total', round(sz/1e6,2),'MB')
