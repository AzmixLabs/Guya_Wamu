import json, os, sys, tempfile, shutil, zipfile
from collections import defaultdict
import numpy as np
import laspy
from pyproj import Transformer

MANIFEST_PATH = os.environ.get('MANIFEST_PATH', 'D:/Claude Code/data/raw/_inventory/manifest.json')
OUT_PREFIX = os.environ.get('OUT_PREFIX', 'D:/Claude Code/data/raw/_inventory/')
CHECKPOINT_EVERY = int(os.environ.get('CHECKPOINT_EVERY', '50'))

MANIFEST = json.load(open(MANIFEST_PATH))
SUNSHINE_DIR = "D:/Claude Code/data/raw/Sunshine-Coast"
SCRATCH = OUT_PREFIX + "work"
os.makedirs(SCRATCH, exist_ok=True)

GRID = 25  # metres
ELEV_MIN, ELEV_MAX = -3.0, 5.0  # AHD metres, land-based reachable band

transformers = {
    28356: Transformer.from_crs('EPSG:28356', 'EPSG:4326', always_xy=True),
    7856:  Transformer.from_crs('EPSG:7856', 'EPSG:4326', always_xy=True),
}

CHECKPOINT_PATH = OUT_PREFIX + 'checkpoint.json'

# cell key -> [rank, z_list, easting, northing, epsg]
cells = {}
tile_stats = []  # (name, survey, n_ground_raw, n_ground_clipped)
group_cells = defaultdict(set)  # survey -> set of cell keys (pre-priority, for coverage-delta)
start_idx = 0

def save_checkpoint(next_idx):
    cells_ser = [[k[0], k[1]] + v for k, v in cells.items()]
    group_cells_ser = {k: list(v) for k, v in group_cells.items()}
    tmp_path = CHECKPOINT_PATH + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump({
            'next_idx': next_idx,
            'cells': cells_ser,
            'group_cells': group_cells_ser,
            'tile_stats': tile_stats,
        }, f)
    os.replace(tmp_path, CHECKPOINT_PATH)  # atomic-ish overwrite

def load_checkpoint():
    global cells, group_cells, tile_stats, start_idx
    if not os.path.exists(CHECKPOINT_PATH):
        return
    with open(CHECKPOINT_PATH) as f:
        data = json.load(f)
    for row in data['cells']:
        e, n, rank, zlist, x, y, epsg = row
        cells[(e, n)] = [rank, zlist, x, y, epsg]
    for survey, keys in data['group_cells'].items():
        group_cells[survey] = set(tuple(k) for k in keys)
    tile_stats = data['tile_stats']
    start_idx = data['next_idx']
    print(f"RESUMED from checkpoint: next_idx={start_idx}, cells={len(cells)}", flush=True)

def process_one(tile):
    outer_path = os.path.join(SUNSHINE_DIR, tile['outer'])
    tmpdir = tempfile.mkdtemp(dir=SCRATCH)
    try:
        with zipfile.ZipFile(outer_path) as z:
            z.extract(tile['path'], tmpdir)
        nested_zip = os.path.join(tmpdir, tile['path'])
        with zipfile.ZipFile(nested_zip) as z:
            las_names = [n for n in z.namelist() if n.lower().endswith(('.las', '.laz'))]
            if not las_names:
                return 0, 0
            z.extract(las_names[0], tmpdir)
        las_path = os.path.join(tmpdir, las_names[0])

        las = laspy.read(las_path)
        cls = np.asarray(las.classification)
        mask_ground = cls == 2
        n_raw = int(mask_ground.sum())
        if n_raw == 0:
            return 0, 0

        x = np.asarray(las.x)[mask_ground]
        y = np.asarray(las.y)[mask_ground]
        zz = np.asarray(las.z)[mask_ground]

        mask_elev = (zz >= ELEV_MIN) & (zz <= ELEV_MAX)
        n_clip = int(mask_elev.sum())
        if n_clip == 0:
            return n_raw, 0
        x, y, zz = x[mask_elev], y[mask_elev], zz[mask_elev]

        ex = np.round(x / GRID).astype(np.int64)
        ny = np.round(y / GRID).astype(np.int64)
        rank = tile['rank']
        epsg = tile['epsg']
        survey = tile['survey']

        gset = group_cells[survey]
        for i in range(len(zz)):
            key = (int(ex[i]), int(ny[i]))
            gset.add(key)
            cur = cells.get(key)
            if cur is None or rank < cur[0]:
                cells[key] = [rank, [float(zz[i])], float(x[i]), float(y[i]), epsg]
            elif rank == cur[0]:
                cur[1].append(float(zz[i]))

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

with open(OUT_PREFIX + 'tile_stats.json', 'w') as f:
    json.dump(tile_stats, f)

# collapse cells (median z per cell), reproject
out_rows = []
for key, (rank, zlist, x, y, epsg) in cells.items():
    z = float(np.median(zlist))
    lon, lat = transformers[epsg].transform(x, y)
    out_rows.append((lat, lon, z, rank))

with open(OUT_PREFIX + 'merged_cells.json', 'w') as f:
    json.dump(out_rows, f)

with open(OUT_PREFIX + 'group_cells.json', 'w') as f:
    json.dump({k: list(v) for k, v in group_cells.items()}, f)

print(f"DONE. total tiles={total} total_cells={len(cells)}", flush=True)
