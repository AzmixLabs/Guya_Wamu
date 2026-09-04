# Moreton Bay / Redcliffe flats-layer build (v16.51).
# Extract -> mask -> band -> MERGE CSV, in one pass.
#
# Faithful to the proven BR/SC pipeline:
#   - class-2 ground only, elevation clipped to ELEV_MIN/MAX (-3.0..+5.0 AHD)
#   - 25 m cell aggregation, key = round(coord/25) in native CRS (process_tiles.py convention)
#   - rank priority: lower rank wins outright; equal rank pools z, median per cell
# Two approved deviations from the shared scripts, both because those were written for SC/Noosa:
#   1. outer zip resolved from tile['src'], not a hardcoded SUNSHINE_DIR (Moreton spans two bundles)
#   2. AHD->LAT offset from the manifest's per-tile 'offset' (1.26 Beachmere / 1.32 Brisbane Bar),
#      not export_csv.py's latitude-bucket function, which buckets every Moreton tile to 1.26
# Flagged-cell drop uses floor(coord/25) in the tile's NATIVE CRS - the same anchoring the audit and
# mask re-scan used - computed straight from native x/y, so there is no transform round-trip.
# Points in flagged cells are DROPPED, never reclassified.
import json, os, sys, tempfile, shutil, zipfile, time
from collections import defaultdict
import numpy as np
import laspy
from pyproj import Transformer

BASE = 'D:/Claude Code/data/raw/_inventory/'
OUT = BASE + 'moreton_full/'
MANIFEST = json.load(open(BASE + 'moreton_manifest.json'))
MASKROWS = json.load(open(OUT + 'mask_mask_cells.json'))

GRID = 25
ELEV_MIN, ELEV_MAX = -3.0, 5.0
EVERY = 10
CKPT = OUT + 'build_checkpoint.json'
SCRATCH = OUT + 'build_work'
os.makedirs(SCRATCH, exist_ok=True)

transformers = {28356: Transformer.from_crs('EPSG:28356', 'EPSG:4326', always_xy=True),
                7856:  Transformer.from_crs('EPSG:7856',  'EPSG:4326', always_xy=True)}

# flagged-cell key sets per EPSG, floor-anchored (audit / hybrid_mask convention)
MASK = defaultdict(set)
for r in MASKROWS:
    for cx, cy in r['cells']:
        MASK[r['epsg']].add((cx, cy))
print(f"mask cells loaded: {sum(len(v) for v in MASK.values()):,} across epsg {sorted(MASK)}", flush=True)

PORTS = [('Burnett Heads', -24.7607, 152.4063, 3.70, 1.407, 2.176),
         ('Brisbane Bar',  -27.3667, 153.1667, 2.81, 1.002, 1.653),
         ('Mooloolaba',    -26.6833, 153.1167, 2.24, 0.775, 1.234)]

def nearest_port(lat, lng):
    import math
    best, bd = PORTS[0], float('inf')
    for p in PORTS:
        dy, dx = math.radians(p[1] - lat), math.radians(p[2] - lng)
        s = math.sin(dy/2)**2 + math.cos(math.radians(lat))*math.cos(math.radians(p[1]))*math.sin(dx/2)**2
        d = 2*6371*math.asin(min(1, math.sqrt(s)))
        if d < bd: bd, best = d, p
    return best

cells = {}            # (cx,cy) -> [rank, [z...], x, y, epsg, offset]
start_idx = 0

def save_ckpt(i):
    tmp = CKPT + '.tmp'
    json.dump({'next_idx': i,
               'cells': [[k[0], k[1], v[0], v[1], v[2], v[3], v[4], v[5]] for k, v in cells.items()]},
              open(tmp, 'w'))
    os.replace(tmp, CKPT)

def load_ckpt():
    global cells, start_idx
    if not os.path.exists(CKPT): return
    d = json.load(open(CKPT))
    start_idx = d['next_idx']
    for cx, cy, rank, zl, x, y, epsg, off in d['cells']:
        cells[(cx, cy)] = [rank, zl, x, y, epsg, off]
    print(f"RESUMED: next_idx={start_idx}, cells={len(cells):,}", flush=True)

def process_one(t):
    tmpdir = tempfile.mkdtemp(dir=SCRATCH)
    try:
        with zipfile.ZipFile(os.path.join(t['src'], t['outer'])) as z:
            z.extract(t['path'], tmpdir)
        with zipfile.ZipFile(os.path.join(tmpdir, t['path'])) as z:
            names = [n for n in z.namelist() if n.lower().endswith(('.las', '.laz'))]
            if not names: return 0, 0
            z.extract(names[0], tmpdir)
        las = laspy.read(os.path.join(tmpdir, names[0]))
        cls = np.asarray(las.classification)
        g = cls == 2
        n_raw = int(g.sum())
        if not n_raw: return 0, 0
        x, y, zz = np.asarray(las.x)[g], np.asarray(las.y)[g], np.asarray(las.z)[g]
        m = (zz >= ELEV_MIN) & (zz <= ELEV_MAX)
        n_clip = int(m.sum())
        if not n_clip: return n_raw, 0
        x, y, zz = x[m], y[m], zz[m]
        ex = np.round(x / GRID).astype(np.int64)
        ny = np.round(y / GRID).astype(np.int64)
        rank, epsg, off = t['rank'], t['epsg'], t['offset']
        for i in range(len(zz)):
            k = (int(ex[i]), int(ny[i]))
            cur = cells.get(k)
            if cur is None or rank < cur[0]:
                cells[k] = [rank, [float(zz[i])], float(x[i]), float(y[i]), epsg, off]
            elif rank == cur[0]:
                cur[1].append(float(zz[i]))
        return n_raw, n_clip
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

load_ckpt()
total = len(MANIFEST)
t0 = time.time()
for idx in range(start_idx, total):
    t = MANIFEST[idx]
    try:
        process_one(t)
    except Exception as e:
        print(f"[{idx+1}/{total}] ERROR {t['name']}: {str(e)[:160]}", flush=True)
    if (idx + 1) % EVERY == 0 or idx == total - 1:
        print(f"{idx+1}/{total} tiles processed | cells={len(cells):,} | {int(time.time()-t0)}s", flush=True)
        save_ckpt(idx + 1)

print(f"EXTRACT DONE. cells={len(cells):,} wall={int(time.time()-t0)}s", flush=True)

# ---- collapse, mask, convert, band ----
kept, dropped_mask, above_hat, below_lat = [], 0, 0, 0
bands = [0, 0, 0, 0]
portc = defaultdict(int)
for (cx, cy), (rank, zl, x, y, epsg, off) in cells.items():
    fx, fy = int(np.floor(x / GRID)), int(np.floor(y / GRID))
    if (fx, fy) in MASK[epsg]:
        dropped_mask += 1
        continue
    z = float(np.median(zl))
    lon, lat = transformers[epsg].transform(x, y)
    depth = -z - off              # metres below LAT, negative = dries
    p = nearest_port(lat, lon)
    e = -depth                    # elevation above LAT
    if e > p[3]:
        above_hat += 1
        continue
    portc[p[0]] += 1
    if   e < 0:      bands[3] += 1; below_lat += 1
    elif e <= p[4]:  bands[2] += 1
    elif e <= p[5]:  bands[1] += 1
    else:            bands[0] += 1
    kept.append((round(lat, 6), round(lon, 6), round(depth, 2)))

dst = 'D:/Claude Code/data/moreton_bay_flats_v1.csv'
with open(dst, 'w', newline='') as f:
    f.write('lat,lng,depth\n')
    for la, lo, d in kept:
        f.write(f'{la:.6f},{lo:.6f},{d:.2f}\n')

pre = len(cells) - dropped_mask
print()
print(f"cells extracted        : {len(cells):,}")
print(f"dropped by mask        : {dropped_mask:,} ({100*dropped_mask/len(cells):.2f}%)")
print(f"post-mask points       : {pre:,}")
print(f"dropped above HAT      : {above_hat:,} ({100*above_hat/pre:.1f}% of post-mask)")
print(f"written                : {len(kept):,}  {os.path.getsize(dst)/1e6:.2f} MB -> {dst}")
print(f"below LAT              : {below_lat:,}")
print(f"port split             : {dict(portc)}")
print(f"gold {bands[0]:,} | amber {bands[1]:,} | teal {bands[2]:,} | blue {bands[3]:,}")
json.dump({'cells': len(cells), 'mask_dropped': dropped_mask, 'post_mask': pre,
           'above_hat': above_hat, 'written': len(kept), 'below_lat': below_lat,
           'bands': bands, 'ports': dict(portc)}, open(OUT + 'build_summary.json', 'w'), indent=1)
