# Brisbane River / Bremer / Redland / Pine River — intertidal/exposed-GROUND elevation
# extraction (NOT depth, NOT bathymetry — topographic NIR LiDAR cannot see through water).
import json, os, random, tempfile, shutil, zipfile
from collections import defaultdict
import numpy as np
import laspy
from pyproj import Transformer

BASE = 'D:/Claude Code/data/raw/_inventory/brisbane/'
MANIFEST_PATH = os.environ.get('MANIFEST_PATH', BASE + 'manifest.json')
OUT_PREFIX = os.environ.get('OUT_PREFIX', BASE)
CHECKPOINT_EVERY = int(os.environ.get('CHECKPOINT_EVERY', '50'))
SRC_DIR = 'D:/Claude Code/data/raw/Brisbane-River'

MANIFEST = json.load(open(MANIFEST_PATH))
SCRATCH = OUT_PREFIX + 'work'
os.makedirs(SCRATCH, exist_ok=True)

GRID = 25  # metres
# Floor tightened vs the Sunshine Coast run: genuine intertidal ground cannot sit below
# LAT (Brisbane Bar LAT = -1.32 m AHD; Bremer -1.21). Class-2 below -1.6 m AHD is fused
# hydro-survey insert or artifact (e.g. the CBD 180x175 m patch at -15..-2) — excluded.
ELEV_MIN, ELEV_MAX = -1.6, 5.0
ZK = 15  # reservoir sample size per cell

transformers = {
    28356: Transformer.from_crs('EPSG:28356', 'EPSG:4326', always_xy=True),
    7856:  Transformer.from_crs('EPSG:7856', 'EPSG:4326', always_xy=True),
}

CHECKPOINT_PATH = OUT_PREFIX + 'checkpoint.json'

# cell key -> [rank, count, zsample(<=ZK), x, y, epsg, offset]
cells = {}
tile_stats = []
group_cells = defaultdict(set)
start_idx = 0
rng = random.Random(42)

def save_checkpoint(next_idx):
    ser = [[k[0], k[1]] + v for k, v in cells.items()]
    tmp = CHECKPOINT_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump({'next_idx': next_idx, 'cells': ser,
                   'group_cells': {k: list(v) for k, v in group_cells.items()},
                   'tile_stats': tile_stats}, f)
    os.replace(tmp, CHECKPOINT_PATH)

def load_checkpoint():
    global tile_stats, start_idx
    if not os.path.exists(CHECKPOINT_PATH):
        return
    d = json.load(open(CHECKPOINT_PATH))
    for row in d['cells']:
        e, n, rank, cnt, zs, x, y, epsg, off = row
        cells[(e, n)] = [rank, cnt, zs, x, y, epsg, off]
    for s, keys in d['group_cells'].items():
        group_cells[s] = set(tuple(k) for k in keys)
    tile_stats = d['tile_stats']
    start_idx = d['next_idx']
    print(f"RESUMED from checkpoint: next_idx={start_idx}, cells={len(cells)}", flush=True)

def add_z(cur, z):
    cur[1] += 1
    zs = cur[2]
    if len(zs) < ZK:
        zs.append(z)
    else:
        j = rng.randrange(cur[1])
        if j < ZK:
            zs[j] = z

def process_one(tile):
    tmpdir = tempfile.mkdtemp(dir=SCRATCH)
    try:
        with zipfile.ZipFile(os.path.join(SRC_DIR, tile['outer'])) as z:
            z.extract(tile['path'], tmpdir)
        with zipfile.ZipFile(os.path.join(tmpdir, tile['path'])) as z:
            las_names = [n for n in z.namelist() if n.lower().endswith(('.las', '.laz'))]
            if not las_names:
                return 0, 0
            z.extract(las_names[0], tmpdir)
        las = laspy.read(os.path.join(tmpdir, las_names[0]))
        cls = np.asarray(las.classification)
        mg = cls == 2
        n_raw = int(mg.sum())
        if n_raw == 0:
            return 0, 0
        x = np.asarray(las.x)[mg]; y = np.asarray(las.y)[mg]; zz = np.asarray(las.z)[mg]
        me = (zz >= ELEV_MIN) & (zz <= ELEV_MAX)
        n_clip = int(me.sum())
        if n_clip == 0:
            return n_raw, 0
        x, y, zz = x[me], y[me], zz[me]
        ex = np.round(x / GRID).astype(np.int64)
        ny = np.round(y / GRID).astype(np.int64)
        rank, epsg, off, survey = tile['rank'], tile['epsg'], tile['offset'], tile['survey']
        gset = group_cells[survey]
        for i in range(len(zz)):
            key = (int(ex[i]), int(ny[i]))
            gset.add(key)
            cur = cells.get(key)
            if cur is None or rank < cur[0]:
                cells[key] = [rank, 1, [float(zz[i])], float(x[i]), float(y[i]), epsg, off]
            elif rank == cur[0]:
                add_z(cur, float(zz[i]))
        return n_raw, n_clip
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

load_checkpoint()
total = len(MANIFEST)
if start_idx >= total:
    print(f"Checkpoint already covers all {total} tiles — nothing to do.", flush=True)
else:
    for idx in range(start_idx, total):
        tile = MANIFEST[idx]
        try:
            n_raw, n_clip = process_one(tile)
        except Exception as e:
            print(f"[{idx+1}/{total}] ERROR {tile['name']}: {e}", flush=True)
            n_raw, n_clip = -1, -1
        tile_stats.append((tile['name'], tile['survey'], n_raw, n_clip))
        if (idx + 1) % CHECKPOINT_EVERY == 0 or idx == total - 1:
            print(f"{idx+1}/{total} tiles processed", flush=True)
            save_checkpoint(idx + 1)

json.dump(tile_stats, open(OUT_PREFIX + 'tile_stats.json', 'w'))

out_rows = []
for key, (rank, cnt, zs, x, y, epsg, off) in cells.items():
    z = float(np.median(zs))
    lon, lat = transformers[epsg].transform(x, y)
    out_rows.append((lat, lon, z, rank, off))
json.dump(out_rows, open(OUT_PREFIX + 'merged_cells.json', 'w'))
json.dump({k: list(v) for k, v in group_cells.items()},
          open(OUT_PREFIX + 'group_cells.json', 'w'))
print(f"DONE. total tiles={total} total_cells={len(cells)}", flush=True)
