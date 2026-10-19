import json, os
OUT='/home/claude/isaac-bible/app'
# Approximate territorial extents, hand-drawn from standard historical atlases.
# Marked "approximate" in the UI and visually distinct from openBible's sourced boundaries.
K=[
 {"id":"k_united","n":"Kingdom of Israel (United Monarchy)","p":"c. 1000–930 BC","note":"Dan to Beersheba under David and Solomon.",
  "poly":[[34.60,31.00],[35.40,30.85],[35.80,31.45],[35.95,32.30],[35.90,33.30],[35.30,33.40],[34.90,32.95],[34.58,32.05],[34.50,31.45]]},
 {"id":"k_israel","n":"Kingdom of Israel (Northern)","p":"c. 930–722 BC","note":"The ten northern tribes; capital at Samaria. Fell to Assyria in 722 BC.",
  "poly":[[34.92,32.02],[35.50,31.92],[35.92,32.28],[35.98,32.92],[35.78,33.28],[35.28,33.34],[34.95,32.92],[34.84,32.42]]},
 {"id":"k_judah","n":"Kingdom of Judah","p":"c. 930–586 BC","note":"The southern kingdom; capital at Jerusalem. Fell to Babylon in 586 BC.",
  "poly":[[34.95,31.96],[35.26,31.96],[35.47,31.74],[35.52,31.34],[35.34,30.94],[34.94,30.88],[34.58,31.14],[34.64,31.52],[34.80,31.78]]},
 {"id":"k_edom","n":"Edom","p":"c. 1200–550 BC","note":"South and east of the Dead Sea, astride the King's Highway.",
  "poly":[[35.20,30.90],[35.70,30.95],[36.00,30.55],[35.95,29.85],[35.50,29.55],[35.10,29.90],[35.02,30.45]]},
 {"id":"k_phoen","n":"Phoenicia","p":"c. 1200–300 BC","note":"The coastal city-states of Tyre, Sidon and Byblos.",
  "poly":[[35.10,33.05],[35.45,33.20],[35.75,34.10],[36.00,34.70],[35.72,34.85],[35.30,34.20],[35.08,33.50]]},
 {"id":"k_egypt","n":"Egypt (New Kingdom core)","p":"c. 1550–1070 BC","note":"The Nile valley and delta — the heartland, not the full imperial reach.",
  "poly":[[29.75,31.45],[32.35,31.30],[32.60,30.55],[31.35,29.95],[31.05,28.95],[32.05,27.45],[32.90,25.45],[33.05,23.95],[32.90,22.00],[32.15,22.00],[31.55,24.20],[30.65,26.30],[30.25,28.30],[29.55,30.30]]},
 {"id":"k_assyria","n":"Neo-Assyrian Empire","p":"at its height, c. 660 BC","note":"From the Nile delta to the Zagros — the power that took the northern kingdom.",
  "poly":[[30.90,31.30],[34.40,30.95],[36.20,30.40],[38.60,32.60],[41.00,33.20],[45.20,34.60],[47.20,36.30],[46.20,37.90],[42.00,38.10],[38.20,37.40],[36.10,36.70],[34.95,35.40],[34.10,33.00],[32.40,31.50]]},
 {"id":"k_babylon","n":"Neo-Babylonian Empire","p":"c. 570 BC","note":"Nebuchadnezzar's empire — the power of the exile.",
  "poly":[[34.20,31.10],[36.30,30.30],[39.00,31.00],[42.50,32.40],[47.00,30.10],[48.60,30.30],[47.80,33.60],[45.60,36.00],[42.20,37.00],[38.60,36.90],[36.00,36.40],[34.90,35.30],[34.30,33.20]]},
 {"id":"k_persia","n":"Achaemenid Persian Empire","p":"c. 500 BC","note":"The empire of Cyrus, Darius and Esther — extending east beyond this map.",
  "poly":[[25.50,31.60],[30.00,31.60],[34.00,36.20],[38.00,40.50],[45.00,41.50],[53.00,40.00],[60.00,38.50],[64.00,36.00],[64.00,24.50],[57.00,25.00],[50.00,27.50],[44.00,29.50],[39.00,27.00],[34.00,27.50],[30.00,24.00],[25.50,26.00]]},
 {"id":"k_rome","n":"Roman Empire (eastern provinces)","p":"c. AD 30","note":"The world of Acts and the epistles.",
  "poly":[[9.00,45.00],[14.00,46.00],[19.00,45.50],[23.00,44.00],[28.50,44.00],[32.00,42.00],[36.00,41.50],[39.50,38.50],[37.50,36.00],[36.50,33.00],[35.00,31.00],[33.50,30.00],[30.00,31.30],[25.00,32.00],[20.00,32.50],[15.00,33.50],[10.50,36.50],[9.00,40.00]]},
 {"id":"k_judea","n":"Roman Judea","p":"c. AD 30","note":"The province of Pilate's prefecture.",
  "poly":[[34.90,31.95],[35.30,31.95],[35.52,31.70],[35.56,31.30],[35.30,30.95],[34.90,30.88],[34.62,31.20],[34.70,31.60]]},
 {"id":"k_galilee","n":"Galilee","p":"c. AD 30","note":"Herod Antipas' tetrarchy — the setting of most of Jesus' ministry.",
  "poly":[[35.05,32.70],[35.58,32.62],[35.72,32.90],[35.65,33.22],[35.25,33.28],[35.00,33.05]]},
]
json.dump(K, open(f'{OUT}/data/geo/kingdoms.json','w'), separators=(',',':'), ensure_ascii=False)
print('kingdoms:',len(K), round(os.path.getsize(f'{OUT}/data/geo/kingdoms.json')/1024,1),'KB')
