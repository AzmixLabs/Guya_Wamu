# PATH 2 step 1 spot-check: for >=20 re-scanned tiles spread across all 14 hybrid survey
# groups, confirm the audit's 3 stored example coordinates (audit_results.json) fall inside
# the re-scan's flagged-cell set for that tile. Example lat/lon are cell centres; inverse
# transform to the tile's native CRS and floor(/25) must land exactly on a flagged (cx,cy).
import json
import numpy as np
from pyproj import Transformer

BASE = 'D:/Claude Code/data/raw/_inventory/'
scan = {r['name']: r for r in json.load(open(BASE + 'hybrid_mask_cells.json'))}
res = json.load(open(BASE + 'audit_results.json'))

t_to = {e: Transformer.from_crs('EPSG:4326', f'EPSG:{e}', always_xy=True) for e in (28356, 7856)}

by_survey = {}
for r in res:
    if r['status'] == 'HIT' and r['name'] in scan and r.get('examples'):
        by_survey.setdefault(r['survey'], []).append(r)

checked = passed = 0
tile_pass = tile_total = 0
for survey, rows in sorted(by_survey.items()):
    rows = sorted(rows, key=lambda r: -r['sus_cells'])
    picks = rows[:2] if len(rows) >= 2 else rows[:1]  # 2 per survey x 14 surveys = 28 tiles
    for r in picks:
        s = scan[r['name']]
        cellset = {(cx, cy) for cx, cy in s['cells']}
        ok = 0
        for ex in r['examples']:
            x, y = t_to[s['epsg']].transform(ex['lon'], ex['lat'])
            key = (int(np.floor(x / 25)), int(np.floor(y / 25)))
            if key in cellset:
                ok += 1
        checked += len(r['examples']); passed += ok
        tile_total += 1
        tile_pass += (ok == len(r['examples']))
        flag = 'PASS' if ok == len(r['examples']) else f'FAIL ({ok}/{len(r["examples"])})'
        print(f"{flag}  {survey:26s} {r['name'][:52]:52s} examples={ok}/{len(r['examples'])}")
print(f"\nSPOT-CHECK: {tile_pass}/{tile_total} tiles fully matched; "
      f"{passed}/{checked} example coordinates found in re-scan cell sets")
