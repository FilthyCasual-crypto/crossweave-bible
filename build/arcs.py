import json, collections, os
import os
# Paths resolve from the repo, not from an author's machine.
# Override with CW_ROOT (repo root) or CW_SOURCES (upstream datasets).
_ROOT = os.environ.get('CW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.environ.get('CW_SOURCES') or os.path.join(_ROOT, 'sources')
_CACHE = os.path.join(_ROOT, '.build-cache')
os.makedirs(_CACHE, exist_ok=True)

OUT=os.path.join(_ROOT,'app')
idx=json.load(open(f'{OUT}/data/index.json'))
books=idx['books']

# flat chapter table
chaps=[]          # (bookIdx, chapNo, nVerses, globalStart)
cstart=[]         # global verse index where each chapter starts
for bi,b in enumerate(books):
    g=b['s']
    for ci,n in enumerate(b['c']):
        chaps.append([bi,ci+1,n,g]); cstart.append(g); g+=n
print('chapters:',len(chaps))

# global verse -> chapter index (binary-searchable array)
import bisect
def chOf(gv): return bisect.bisect_right(cstart,gv)-1

# aggregate verse edges to chapter pairs
agg=collections.Counter()
seen=0
for bi in range(66):
    x=json.load(open(f'{OUT}/data/x/{bi}.json'))
    base=books[bi]['s']
    for off,lst in x.items():
        src=chOf(base+int(off))
        for t,span,w in lst:
            dst=chOf(t)
            if dst==src: continue
            a,b=(src,dst) if src<dst else (dst,src)
            agg[(a,b)]+=w
            seen+=1
print('verse-level edge endpoints seen:',seen)
print('unique chapter pairs:',len(agg))

edges=sorted(agg.items(), key=lambda kv:-kv[1])
mx=edges[0][1]
print('max pair weight:',mx)

# keep pairs above a floor to stay drawable; report coverage
KEEP=len(edges)
A=[];B=[];W=[]
for (a,b),w in edges[:KEEP]:
    A.append(a);B.append(b);W.append(w)

json.dump({'chaps':chaps,'a':A,'b':B,'w':W,'max':mx,'totalVerses':idx['totalVerses']},
          open(f'{OUT}/data/arcs.json','w'), separators=(',',':'))
print('arcs.json', round(os.path.getsize(f'{OUT}/data/arcs.json')/1e6,2),'MB')

# cross-testament stat (Matthew = book 39)
nt0=39
otnt=sum(1 for (a,b) in agg if chaps[a][0]<nt0<=chaps[b][0] or chaps[b][0]<nt0<=chaps[a][0])
print('OT<->NT chapter pairs:',otnt, '=', round(100*otnt/len(agg),1),'%')
