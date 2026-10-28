import json, os
# Paths resolve from the repo, not from an author's machine.
# Override with CW_ROOT (repo root) or CW_SOURCES (upstream datasets).
_ROOT = os.environ.get('CW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.environ.get('CW_SOURCES') or os.path.join(_ROOT, 'sources')
_CACHE = os.path.join(_ROOT, '.build-cache')
os.makedirs(_CACHE, exist_ok=True)

OUT=os.path.join(_ROOT,'app')
IDX=json.load(open(f'{OUT}/data/index.json')); B=IDX['books']
P=json.load(open(f'{OUT}/data/geo/places.json'))['places']

# Itineraries are the stops the narrative actually makes, in order.
# Pure mention-order draws lines through places only *named* (the ship from
# Alexandria, Aristarchus of Thessalonica), which asserts travel that never happened.
# Each name below is resolved against the places the text links inside that passage,
# walking forward through the passage, so every stop carries the verse where the narrative
# reaches it - a return visit gets the return verse, and "Antioch" resolves to whichever
# Antioch the text links at that point. A stop may pin its verse as "Name@ch:v" where the
# forward walk alone would land too early (the return leg of Paul's first journey).
J=[
 {"id":"j_abram","n":"Abram leaves Ur","s":"Genesis 11:31 – 13:18",
  "note":"Ur to Haran to Canaan — the migration the whole story hangs on.",
  "r":[[0,11,31,32],[0,12,1,20],[0,13,1,18]],
  "stops":["Ur","Haran","Shechem","Bethel","Ai","Negeb","Egypt","Bethel","Hebron"]},
 {"id":"j_exodus","n":"Out of Egypt","s":"Exodus 12:37 – 19:2",
  "note":"Rameses to Sinai, as Exodus names the camps.",
  "r":[[1,12,37,51],[1,13,1,22],[1,14,1,31],[1,15,1,27],[1,16,1,36],[1,17,1,16],[1,18,1,27],[1,19,1,2]],
  "stops":["Rameses","Succoth","Etham","Pi-hahiroth","Marah","Elim","Rephidim","Wilderness of Sinai"]},
 {"id":"j_stations","n":"The wilderness stations","s":"Numbers 33:1–49",
  "note":"The explicit itinerary — forty years of camps, listed in order by the text itself.",
  "r":[[3,33,1,49]], "stops":None},
 {"id":"j_paul1","n":"Paul's first journey","s":"Acts 13–14",
  "note":"Antioch to Cyprus and the Galatian cities, and back the way he came.",
  "r":[[43,13,1,52],[43,14,1,28]],
  "stops":["Antioch","Seleucia","Salamis","Paphos","Perga","Antioch","Iconium","Lystra","Derbe",
           "Lystra@14:21","Iconium@14:21","Antioch@14:21","Perga@14:25","Attalia","Antioch@14:26"]},
 {"id":"j_paul2","n":"Paul's second journey","s":"Acts 15:36 – 18:22",
  "note":"Into Macedonia and Achaia — Philippi, Thessalonica, Athens, Corinth.",
  "r":[[43,15,36,41],[43,16,1,40],[43,17,1,34],[43,18,1,22]],
  "stops":["Derbe","Lystra","Troas","Samothrace","Neapolis","Philippi","Amphipolis","Apollonia",
           "Thessalonica","Berea","Athens","Corinth","Cenchreae","Ephesus","Caesarea","Antioch"]},
 {"id":"j_paul3","n":"Paul's third journey","s":"Acts 18:23 – 21:17",
  "note":"The long stay at Ephesus, then the slow return toward Jerusalem.",
  "r":[[43,18,23,28],[43,19,1,41],[43,20,1,38],[43,21,1,17]],
  "stops":["Antioch","Ephesus","Philippi","Troas","Assos","Mitylene","Chios","Samos","Miletus",
           "Cos","Rhodes","Patara","Tyre","Ptolemais","Caesarea","Jerusalem@21:17"]},
 {"id":"j_rome","n":"The voyage to Rome","s":"Acts 27:1 – 28:16",
  "note":"Caesarea to Rome, by way of the shipwreck at Malta.",
  "r":[[43,25,13,27],[43,27,1,44],[43,28,1,16]],
  "stops":["Caesarea","Sidon","Myra","Cnidus","Fair Havens","Malta","Syracuse","Rhegium",
           "Puteoli","Forum of Appius","Three Taverns","Rome"]},
]

SPN={}
def spans(bi):
    if bi not in SPN: SPN[bi]=json.load(open(f'{OUT}/data/geo/bsb-{bi}.json'))
    return SPN[bi]

def derived(j):
    """Every place the passage links, in order, with its verse."""
    seq=[]
    for (bi,ch,v0,v1) in j['r']:
        sp=spans(bi)
        for v in range(v0,v1+1):
            lst=sp.get(f'{ch}.{v}')
            if not lst: continue
            for s in sorted(lst,key=lambda z:z[0]):
                if s[2] in P: seq.append((s[2], f'{B[bi]["n"]} {ch}:{v}', f'{ch}:{v}'))
    return seq


out=[]
for j in J:
    seq=derived(j)
    if j['stops'] is None:
        # Numbers 33 is itself an ordered itinerary — derivation is the right answer there
        clean=[]
        for pid,ref,_ in seq:
            if clean and clean[-1][0]==pid: continue
            clean.append((pid,ref))
        unresolved=[]
    else:
        # walk forward through the places this passage links; never back
        clean=[]; unresolved=[]; pos=0
        for stop in j['stops']:
            name, _, pin = stop.partition('@')
            hit=next((i for i in range(pos, len(seq))
                      if P[seq[i][0]]['n']==name and (not pin or seq[i][2]==pin)), None)
            if hit is None: unresolved.append(stop); continue
            clean.append(seq[hit][:2]); pos=hit+1
    j2={'id':j['id'],'n':j['n'],'s':j['s'],'note':j['note'],
        'w':[{'p':p,'r':r,'c':P[p]['c'],'n':P[p]['n']} for p,r in clean]}
    out.append(j2)
    print(f"{j['n']:<28} {len(clean):>3} stops   {clean[0][1] if clean else '-'} {P[clean[0][0]]['n'] if clean else ''}")
    if unresolved:
        # a dropped stop draws a confident line that skips part of the journey
        raise SystemExit(f"{j['n']}: stops not found in passage order: {unresolved}")

json.dump(out, open(f'{OUT}/data/geo/journeys.json','w'), separators=(',',':'), ensure_ascii=False)
print('\njourneys.json', round(os.path.getsize(f'{OUT}/data/geo/journeys.json')/1024,1),'KB')
