#!/usr/bin/env python3
"""Compare the downloaded upstream datasets against data-baseline.json. Run by `make sources`
and before `make data`: a mismatch means upstream moved, and the build must not run on top
of it until someone decides to re-baseline (see CLAUDE.md).

  python3 scripts/check_sources.py               # compare; exit 1 on any drift
  python3 scripts/check_sources.py --rebaseline  # accept sources/ as the new baseline:
                                                 # rewrite the checksums and the date only
"""
import datetime, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get('CW_SOURCES') or os.path.join(ROOT, 'sources')
BASE_PATH = os.path.join(ROOT, 'data-baseline.json')
BASE = json.load(open(BASE_PATH))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


if '--rebaseline' in sys.argv:
    missing = [n for n in BASE['sources'] if not os.path.exists(os.path.join(SRC, n))]
    if missing:
        sys.exit(f"cannot re-baseline, missing from {SRC}: {', '.join(missing)}")
    for name in BASE['sources']:
        BASE['sources'][name] = sha256(os.path.join(SRC, name))
    BASE['rebaselined'] = datetime.date.today().isoformat()
    with open(BASE_PATH, 'w') as f:
        json.dump(BASE, f, indent=2)
        f.write('\n')
    print("checksums re-baselined. Now `make data`, then set the totals in data-baseline.json "
          "from what verify.py reports, and commit it all together (see CLAUDE.md).")
    sys.exit(0)

bad = []
for name, want in BASE['sources'].items():
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        bad.append(f"  {name}: missing from {SRC}")
        continue
    got = sha256(p)
    if got != want:
        bad.append(f"  {name}:\n    baseline {want}\n    now      {got}")

if bad:
    print("SOURCE DRIFT - sources/ does not match data-baseline.json")
    print('\n'.join(bad))
    print("\nUpstream data has changed. This is not a build error. Decide whether to re-baseline "
          "(see CLAUDE.md) - do not silently rebuild on top of it.")
    sys.exit(1)

print(f"sources match baseline ({len(BASE['sources'])} files, rebaselined {BASE['rebaselined']})")
