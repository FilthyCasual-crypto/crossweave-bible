import json, os, re, math, collections
import os
# Paths resolve from the repo, not from an author's machine.
# Override with CW_ROOT (repo root) or CW_SOURCES (upstream datasets).
_ROOT = os.environ.get('CW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.environ.get('CW_SOURCES') or os.path.join(_ROOT, 'sources')
_CACHE = os.path.join(_ROOT, '.build-cache')
os.makedirs(_CACHE, exist_ok=True)


GEO=_SRC
OUT=os.path.join(_ROOT,'app')
os.makedirs(f'{OUT}/data/geo', exist_ok=True)

BBOX=(9.0,10.0,64.0,48.5)   # lon0,lat0,lon1,lat1 — Rome to Persia, Nubia to the Black Sea

# ---------------- base map: Natural Earth 50m countries ----------------
def rdp(pts, eps):
    if len(pts) < 3: return pts
    def d(p,a,b):
        if a==b: return math.hypot(p[0]-a[0],p[1]-a[1])
        t=((p[0]-a[0])*(b[0]-a[0])+(p[1]-a[1])*(b[1]-a[1]))/((b[0]-a[0])**2+(b[1]-a[1])**2)
        t=max(0,min(1,t)); return math.hypot(p[0]-a[0]-t*(b[0]-a[0]), p[1]-a[1]-t*(b[1]-a[1]))
    keep=[0,len(pts)-1]; stack=[(0,len(pts)-1)]
    while stack:
        i,j=stack.pop()
        if j-i<2: continue
        mx=-1;mi=i
        for k in range(i+1,j):
            dd=d(pts[k],pts[i],pts[j])
            if dd>mx: mx=dd;mi=k
        if mx>eps: keep.append(mi); stack.append((i,mi)); stack.append((mi,j))
    keep=sorted(set(keep)); return [pts[k] for k in keep]

def ring_bbox(r):
    xs=[p[0] for p in r]; ys=[p[1] for p in r]
    return min(xs),min(ys),max(xs),max(ys)
def hits(bb):
    return not (bb[2]<BBOX[0] or bb[0]>BBOX[2] or bb[3]<BBOX[1] or bb[1]>BBOX[3])

ne=json.load(open(f'{GEO}/ne_countries.geojson'))
countries=[]
for f in ne['features']:
    p=f['properties']; g=f['geometry']
    polys = g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    outs=[]
    for poly in polys:
        outer=[(round(x,3),round(y,3)) for x,y in poly[0]]
        bb=ring_bbox(outer)
        if not hits(bb): continue
        s=rdp(outer, 0.035)
        if len(s)>=4: outs.append(s)
    if outs:
        countries.append({'n':p.get('NAME') or p.get('name'), 'r':outs})
json.dump(countries, open(f'{OUT}/data/geo/base.json','w'), separators=(',',':'))
print('base countries:',len(countries),'rings',sum(len(c['r']) for c in countries),
      round(os.path.getsize(f'{OUT}/data/geo/base.json')/1e6,2),'MB')

# ---------------- gazetteer ----------------
A=[json.loads(l) for l in open(f'{GEO}/ancient.jsonl')]
M={}
for l in open(f'{GEO}/modern.jsonl'):
    d=json.loads(l); M[d['id']]=d
GM={}
for l in open(f'{GEO}/geometry.jsonl'):
    d=json.loads(l); GM[d['id']]=d

def ll(s):
    try:
        a,b=s.split(','); return [round(float(a),4), round(float(b),4)]
    except Exception: return None

STOP={'lower','upper','the','city','valley','brook','river','sea','mount','mountain','land',
      'great','east','west','north','south','daughter','jews','way','gate','desert','wilderness',
      'spring','well','tower','house','field','rock','hill','pool','garden','plain','coast','king',
      'lord','god','men','people','son','sons','tribe','high','new','old','red','salt','water','waters'}

places={}
for a in A:
    pid=a['id']
    fid=a.get('friendly_id') or ''
    disp=re.sub(r'\s+\d+$','',fid).strip() or fid
    types=a.get('types') or []
    # pick best resolution by score
    best=None; cands=[]
    for ident in (a.get('identifications') or []):
        for r in (ident.get('resolutions') or []):
            c=ll(r.get('lonlat') or '')
            if not c: continue
            sc=(r.get('best_path_score') or 0)+(r.get('best_time_score') or 0)
            cands.append({'c':c,'s':sc,'g':r.get('ancient_geometry'),'gid':r.get('geometry_id'),
                          'mb':r.get('modern_basis_id')})
            if best is None or sc>best['s']: best=cands[-1]
    if not best: continue
    # modern name/country from the modern basis
    mname=None
    mb=best.get('mb')
    if mb and mb in M:
        nm=(M[mb].get('names') or [])
        mname=(nm[0]['name'] if nm else M[mb].get('friendly_id'))
    # region boundary if the publisher supplies one inline
    poly=None
    gid=best.get('gid')
    if gid and gid in GM:
        rb=(GM[gid].get('suggested') or {}).get('rough_boundary')
        if rb and len(rb)>3:
            poly=[ll(s) for s in rb]; poly=[p for p in poly if p]
            if len(poly)<4: poly=None
    # surface forms
    forms=[]
    for k,v in (a.get('translation_name_counts') or {}).items():
        if not k or len(k)<2: continue
        if ' ' not in k and k.lower() in STOP: continue
        forms.append(k)
    if disp not in forms: forms.append(disp)
    # total order: -len alone leaves ties to set iteration, which makes the build non-deterministic
    forms=sorted(set(forms), key=lambda s:(-len(s), s))
    # verse count drives the gazetteer sort, palette ranking and the map's dot thinning
    vc=sum(1 for v in (a.get('verses') or [])
           if set((v.get('instance_types') or {}).keys()) & {'name','combined','partial','people_group'})
    places[pid]={'id':pid,'n':disp,'fid':fid,'t':(types[0] if types else 'place'),
                 'c':best['c'],'mn':mname,'nc':len(cands),'poly':poly,'v':vc,
                 'art':a.get('preceding_article') or '','slug':a.get('url_slug'),'forms':forms}

print('places with coords:',len(places),'| with inline boundary:',sum(1 for p in places.values() if p['poly']))

# ---------------- verse -> place index ----------------
WANT={'name','combined','partial','people_group'}
mentions=collections.defaultdict(list)   # (book,chap,verse) -> [pid]
for a in A:
    pid=a['id']
    if pid not in places: continue
    for v in a.get('verses') or []:
        it=set((v.get('instance_types') or {}).keys())
        if not (it & WANT): continue
        s=v.get('sort') or ''
        if len(s)!=8 or not s.isdigit(): continue
        b=int(s[0:2])-1; c=int(s[2:5]); vv=int(s[5:8])
        if b<0 or b>65: continue
        tr=v.get('translations') or []
        mentions[(b,c,vv)].append((pid, 'kjv' in tr))
print('verses with at least one place:',len(mentions))
json.dump({'places':places}, open(f'{OUT}/data/geo/places.json','w'), separators=(',',':'), ensure_ascii=False)
print('places.json', round(os.path.getsize(f'{OUT}/data/geo/places.json')/1e6,2),'MB')
with open(os.path.join(_CACHE,'mentions.json'),'w') as f:
    json.dump({f'{k[0]}.{k[1]}.{k[2]}':v for k,v in mentions.items()}, f)
