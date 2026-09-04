# PATH 2 step 2: apply the hybrid flagged-cell mask to the v1 CSVs -> v2 CSVs.
# Grid: 25 m cells anchored at the projection origin in each mask cell's NATIVE CRS
# (EPSG:28356 for pre-2022 surveys, EPSG:7856 for 2022/2023) — a CSV point is dropped
# iff floor(easting/25), floor(northing/25) computed IN THAT CRS matches a mask key of
# that CRS. Never mixes grids across CRSs (GDA94/GDA2020 ~1.8 m shift). v1 files are
# read-only; v2 written alongside. 2009-vintage points are naturally untouched — the
# mask was built only from post-2009 hybrid-scope tiles.
import json
import numpy as np
from pyproj import Transformer

BASE = 'D:/Claude Code/data/raw/_inventory/'
DATA = 'D:/Claude Code/data/'

scan = json.load(open(BASE + 'hybrid_mask_cells.json'))
mism = [r for r in scan if not r['match']]
print(f"mask tiles: {len(scan)} | count mismatches: {len(mism)}")
assert not mism, "cross-validation mismatches present — resolve before applying mask"

# per-EPSG mask key sets, key = cx*10_000_000 + cy
keys = {28356: set(), 7856: set()}
for r in scan:
    s = keys[r['epsg']]
    for cx, cy in r['cells']:
        s.add(cx * 10_000_000 + cy)
mask_arr = {e: np.fromiter(s, dtype=np.int64) for e, s in keys.items()}
print({e: len(s) for e, s in keys.items()}, '| total mask cells:', sum(len(s) for s in keys.values()))

t_to = {e: Transformer.from_crs('EPSG:4326', f'EPSG:{e}', always_xy=True) for e in (28356, 7856)}

def mask_csv(name):
    src = DATA + name + '_v1.csv'
    dst = DATA + name + '_v2.csv'
    rows = np.genfromtxt(src, delimiter=',', skip_header=1)
    lat, lon = rows[:, 0], rows[:, 1]
    drop = np.zeros(len(rows), dtype=bool)
    for e in (28356, 7856):
        x, y = t_to[e].transform(lon, lat)
        k = (np.floor(x / 25).astype(np.int64) * 10_000_000
             + np.floor(y / 25).astype(np.int64))
        drop |= np.isin(k, mask_arr[e])
    keep = rows[~drop]
    with open(dst, 'w', newline='') as f:
        f.write('lat,lng,depth\n')
        for la, lo, d in keep:
            f.write(f'{la:.6f},{lo:.6f},{d:.2f}\n')
    print(f"{name}: v1={len(rows)} dropped={int(drop.sum())} v2={len(keep)} -> {dst}")
    return len(rows), int(drop.sum()), len(keep)

b = mask_csv('brisbane_river_intertidal_ground')
s = mask_csv('sunshine_coast_intertidal_ground')
print(f"TOTAL dropped: {b[1] + s[1]} points (mask holds {sum(len(v) for v in keys.values())} cells)")
