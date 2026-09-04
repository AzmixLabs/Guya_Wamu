# PATH 2 mask re-scan (roadmap item 2 build, v16.23 hybrid scope): re-runs the exact
# v16.17-v16.21 class-9-adjacency method over the 1,184 hybrid-scope HIT tiles and dumps
# EVERY flagged cell's key — (epsg, cx, cy), 25 m grid anchored at the projection origin,
# cx = floor(easting/25), cy = floor(northing/25) in the tile's native CRS — plus a per-tile
# count cross-validated against the sus_cells already recorded in audit_results.json.
# Thresholds are IDENTICAL to the audit (re-scan, not re-audit): GRID=25, MIN_W=20,
# MIN_G=100, ZTOL=0.5. READS raw zips only; writes only _inventory/hybrid_* scratch.
# No points dropped here — the CSV mask application is a separate step.
import json, os, tempfile, shutil, zipfile, sys, time
import numpy as np
import laspy

BASE = 'D:/Claude Code/data/raw/_inventory/'
MANIFEST_PATH = os.environ.get('HYB_MANIFEST', BASE + 'hybrid_manifest.json')
OUT_PREFIX = os.environ.get('HYB_OUT', BASE + 'hybrid_')
EVERY = int(os.environ.get('HYB_EVERY', '25'))
LIMIT = int(os.environ.get('HYB_LIMIT', '0'))  # >0: stop after N tiles this session (smoke test)

MANIFEST = json.load(open(MANIFEST_PATH))
SCRATCH = BASE + 'audit_work'
os.makedirs(SCRATCH, exist_ok=True)
CKPT = OUT_PREFIX + 'checkpoint.json'
GRID = 25
MIN_W, MIN_G, ZTOL = 20, 100, 0.5  # identical to v16.17-v16.21 — do not vary

results = []   # per tile: name, survey, epsg, cells [[cx,cy],...], n_cells, expected, match
start_idx = 0

def save_ckpt(next_idx):
    tmp = CKPT + '.tmp'
    with open(tmp, 'w') as f:
        json.dump({'next_idx': next_idx, 'results': results}, f)
    os.replace(tmp, CKPT)

def load_ckpt():
    global results, start_idx
    if not os.path.exists(CKPT):
        return
    d = json.load(open(CKPT))
    results = d['results']
    start_idx = d['next_idx']
    print(f"RESUMED from checkpoint: next_idx={start_idx}, results={len(results)}", flush=True)

def cell_stats(key, zz, mask):
    k = key[mask]; zv = zz[mask]
    order = np.argsort(k, kind='stable')
    k, zv = k[order], zv[order]
    uk, starts = np.unique(k, return_index=True)
    meds = [float(np.median(zv[s:e])) for s, e in zip(starts, list(starts[1:]) + [len(zv)])]
    cnts = np.diff(list(starts) + [len(zv)])
    return dict(zip(uk.tolist(), zip(cnts.tolist(), meds)))

def scan_one(tile):
    tmpdir = tempfile.mkdtemp(dir=SCRATCH)
    try:
        with zipfile.ZipFile(os.path.join(tile['src'], tile['outer'])) as z:
            z.extract(tile['path'], tmpdir)
        with zipfile.ZipFile(os.path.join(tmpdir, tile['path'])) as z:
            names = [n for n in z.namelist() if n.lower().endswith(('.las', '.laz'))]
            if not names:
                return dict(status='no_las', cells=[])
            z.extract(names[0], tmpdir)
        las = laspy.read(os.path.join(tmpdir, names[0]))
        cls = np.asarray(las.classification)
        x = np.asarray(las.x); y = np.asarray(las.y); zz = np.asarray(las.z)
        cx = (x // GRID).astype(np.int64); cy = (y // GRID).astype(np.int64)
        key = cx * 10_000_000 + cy
        g = cell_stats(key, zz, cls == 2)
        w = cell_stats(key, zz, cls == 9)
        cells = []
        for k9, (c9, m9) in w.items():
            if c9 < MIN_W or k9 not in g:
                continue
            c2, m2 = g[k9]
            if c2 >= MIN_G and abs(m2 - m9) <= ZTOL:
                cells.append([int(k9 // 10_000_000), int(k9 % 10_000_000)])
        return dict(status='ok', cells=cells)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

load_ckpt()
total = len(MANIFEST)
t0 = time.time()
if start_idx >= total:
    print(f"Checkpoint already covers all {total} tiles.", flush=True)
else:
    done_this_session = 0
    for idx in range(start_idx, total):
        tile = MANIFEST[idx]
        try:
            r = scan_one(tile)
        except Exception as e:
            r = dict(status='error', err=str(e)[:200], cells=[])
        r['name'] = tile['name']; r['survey'] = tile['survey']; r['epsg'] = tile['epsg']
        r['n_cells'] = len(r['cells'])
        r['expected'] = tile['expected_sus']
        r['match'] = (r['n_cells'] == r['expected'])
        results.append(r)
        done_this_session += 1
        if (idx + 1) % EVERY == 0 or idx == total - 1:
            mism = sum(1 for q in results if not q['match'])
            el = time.time() - t0
            print(f"{idx+1}/{total} tiles re-scanned (count mismatches so far: {mism}, {el:.0f}s elapsed)", flush=True)
            save_ckpt(idx + 1)
        if LIMIT and done_this_session >= LIMIT:
            save_ckpt(idx + 1)
            print(f"LIMIT={LIMIT} reached; checkpoint saved at next_idx={idx+1}. Exiting.", flush=True)
            sys.exit(0)

tmp = OUT_PREFIX + 'mask_cells.json.tmp'
json.dump(results, open(tmp, 'w'))
os.replace(tmp, OUT_PREFIX + 'mask_cells.json')
mism = [r for r in results if not r['match']]
tot_cells = sum(r['n_cells'] for r in results)
print(f"MASK RE-SCAN DONE. tiles={len(results)} flagged_cells={tot_cells} "
      f"count_mismatches={len(mism)} wall={time.time()-t0:.0f}s", flush=True)
for r in mism[:20]:
    print(f"  MISMATCH {r['survey']} {r['name']}: got {r['n_cells']} expected {r['expected']}", flush=True)
