# Diagnostic-only audit: class-2 "ground" co-located with class-9 "water" at the same
# elevation in the same 25 m cell = the misclassified-water-surface signature confirmed
# at Brighton/Bramble Bay (Brisbane_2019_Prj). READS raw tiles only; writes nothing to
# data/ or any source/output file — results land in _inventory/audit_* scratch files.
import json, os, tempfile, shutil, zipfile
import numpy as np
import laspy
from pyproj import Transformer

BASE = 'D:/Claude Code/data/raw/_inventory/'
MANIFEST_PATH = os.environ.get('AUDIT_MANIFEST', BASE + 'audit_manifest.json')
OUT_PREFIX = os.environ.get('AUDIT_OUT', BASE)
EVERY = int(os.environ.get('AUDIT_EVERY', '20'))

MANIFEST = json.load(open(MANIFEST_PATH))
SCRATCH = OUT_PREFIX + 'audit_work'
os.makedirs(SCRATCH, exist_ok=True)
CKPT = OUT_PREFIX + 'audit_checkpoint.json'
GRID = 25
MIN_W, MIN_G, ZTOL = 20, 100, 0.5  # suspect cell: >=20 class-9 + >=100 class-2, medians within 0.5 m

transformers = {
    28356: Transformer.from_crs('EPSG:28356', 'EPSG:4326', always_xy=True),
    7856:  Transformer.from_crs('EPSG:7856', 'EPSG:4326', always_xy=True),
}

results = []
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

def audit_one(tile):
    tmpdir = tempfile.mkdtemp(dir=SCRATCH)
    try:
        with zipfile.ZipFile(os.path.join(tile['src'], tile['outer'])) as z:
            z.extract(tile['path'], tmpdir)
        with zipfile.ZipFile(os.path.join(tmpdir, tile['path'])) as z:
            names = [n for n in z.namelist() if n.lower().endswith(('.las', '.laz'))]
            if not names:
                return dict(status='no_las')
            z.extract(names[0], tmpdir)
        las = laspy.read(os.path.join(tmpdir, names[0]))
        cls = np.asarray(las.classification)
        n2 = int((cls == 2).sum()); n9 = int((cls == 9).sum())
        if n2 == 0 or n9 == 0:
            return dict(status='clean_by_absence', n2=n2, n9=n9)
        x = np.asarray(las.x); y = np.asarray(las.y); zz = np.asarray(las.z)
        cx = (x // GRID).astype(np.int64); cy = (y // GRID).astype(np.int64)
        key = cx * 10_000_000 + cy

        def cell_stats(mask):
            k = key[mask]; zv = zz[mask]
            order = np.argsort(k, kind='stable')
            k, zv = k[order], zv[order]
            uk, starts = np.unique(k, return_index=True)
            meds = [float(np.median(zv[s:e])) for s, e in zip(starts, list(starts[1:]) + [len(zv)])]
            cnts = np.diff(list(starts) + [len(zv)])
            return dict(zip(uk.tolist(), zip(cnts.tolist(), meds)))

        w = cell_stats(cls == 9)
        g = cell_stats(cls == 2)
        sus = []
        for k9, (c9, m9) in w.items():
            if c9 < MIN_W or k9 not in g:
                continue
            c2, m2 = g[k9]
            if c2 >= MIN_G and abs(m2 - m9) <= ZTOL:
                sus.append((k9, c2, c9, m2, m9))
        if not sus:
            return dict(status='clean', n2=n2, n9=n9)
        dens = [c2 for _, c2, _, _, _ in sus]
        t = transformers[tile['epsg']]
        examples = []
        for k9, c2, c9, m2, m9 in sorted(sus, key=lambda r: -r[1])[:3]:
            ce = (k9 // 10_000_000) * GRID + GRID / 2
            cn = (k9 % 10_000_000) * GRID + GRID / 2
            lon, lat = t.transform(ce, cn)
            examples.append(dict(lat=round(lat, 6), lon=round(lon, 6), c2=c2, c9=c9,
                                 z2=round(m2, 2), z9=round(m9, 2)))
        return dict(status='HIT', n2=n2, n9=n9, sus_cells=len(sus),
                    max_density=int(max(dens)), mean_density=int(np.mean(dens)),
                    area_km2=round(len(sus) * GRID * GRID / 1e6, 4), examples=examples)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

load_ckpt()
total = len(MANIFEST)
if start_idx >= total:
    print(f"Checkpoint already covers all {total} tiles.", flush=True)
else:
    for idx in range(start_idx, total):
        tile = MANIFEST[idx]
        try:
            r = audit_one(tile)
        except Exception as e:
            r = dict(status='error', err=str(e)[:200])
        r['name'] = tile['name']; r['survey'] = tile['survey']; r['src'] = os.path.basename(tile['src'])
        results.append(r)
        if (idx + 1) % EVERY == 0 or idx == total - 1:
            hits = sum(1 for q in results if q['status'] == 'HIT')
            print(f"{idx+1}/{total} tiles audited (hits so far: {hits})", flush=True)
            save_ckpt(idx + 1)

json.dump(results, open(OUT_PREFIX + 'audit_results.json', 'w'))
hits = [r for r in results if r['status'] == 'HIT']
print(f"AUDIT DONE. tiles={len(results)} hits={len(hits)}", flush=True)
