# Diagnostic-only gap audit (roadmap v16.20 item 1): closes the Sunshine Coast audit gap.
# Group A (class9_adjacency): Sunshine_Coast_2022/2014/2008, Noosa_2022/2015 — same method,
#   thresholds and schema as audit_class2.py (v16.17-v16.18 audit): suspect 25 m cell =
#   >=20 class-9 pts + >=100 class-2 pts with medians within 0.5 m.
# Group B (density_only): Brisbane_2009, Redland_2009, MoretonBay_2009 — no class-9 in these
#   vintages, so flag 25 m cells with class-2 count >= 1500 (confirmed artifact floor,
#   v16.17-v16.18 signature 1,500-14,800 pts/cell) AND median z <= +1.5 m AHD (water-plausible
#   band). Calibrated 10 Jul 2026 on 9 sample 2009 tiles: legit low-band max 1,064 pts/cell,
#   legit overall max 1,917 (upslope, excluded by the z gate).
# READS raw zips only. Writes only _inventory/gap_* scratch. Does NOT touch audit_results.json
# (merge is a separate, explicit step after review). No points dropped/masked/re-exported.
import json, os, tempfile, shutil, zipfile, sys, time
import numpy as np
import laspy
from pyproj import Transformer

BASE = 'D:/Claude Code/data/raw/_inventory/'
MANIFEST_PATH = os.environ.get('GAP_MANIFEST', BASE + 'gap_manifest.json')
OUT_PREFIX = os.environ.get('GAP_OUT', BASE + 'gap_')
EVERY = int(os.environ.get('GAP_EVERY', '25'))
LIMIT = int(os.environ.get('GAP_LIMIT', '0'))  # >0: stop after N tiles this session (smoke test)

MANIFEST = json.load(open(MANIFEST_PATH))
SCRATCH = BASE + 'audit_work'
os.makedirs(SCRATCH, exist_ok=True)
CKPT = OUT_PREFIX + 'checkpoint.json'
GRID = 25
MIN_W, MIN_G, ZTOL = 20, 100, 0.5      # Group A: identical to v16.17-v16.18 audit
DENS_MIN, Z_MAX = 1500, 1.5            # Group B: artifact floor + water-plausible band

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

def cell_stats(key, zz, mask):
    k = key[mask]; zv = zz[mask]
    order = np.argsort(k, kind='stable')
    k, zv = k[order], zv[order]
    uk, starts = np.unique(k, return_index=True)
    meds = [float(np.median(zv[s:e])) for s, e in zip(starts, list(starts[1:]) + [len(zv)])]
    cnts = np.diff(list(starts) + [len(zv)])
    return dict(zip(uk.tolist(), zip(cnts.tolist(), meds)))

def examples_for(sus, tile):
    # sus: list of (cellkey, c2, c9, z2, z9) — c9/z9 None for density_only
    t = transformers[tile['epsg']]
    out = []
    for k9, c2, c9, m2, m9 in sorted(sus, key=lambda r: -r[1])[:3]:
        ce = (k9 // 10_000_000) * GRID + GRID / 2
        cn = (k9 % 10_000_000) * GRID + GRID / 2
        lon, lat = t.transform(ce, cn)
        ex = dict(lat=round(lat, 6), lon=round(lon, 6), c2=c2, z2=round(m2, 2))
        if c9 is not None:
            ex['c9'] = c9; ex['z9'] = round(m9, 2)
        out.append(ex)
    return out

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
        if tile['method'] == 'class9_adjacency':
            if n2 == 0 or n9 == 0:
                return dict(status='clean_by_absence', n2=n2, n9=n9)
        else:
            if n2 == 0:
                return dict(status='clean_by_absence', n2=n2, n9=n9)
        x = np.asarray(las.x); y = np.asarray(las.y); zz = np.asarray(las.z)
        cx = (x // GRID).astype(np.int64); cy = (y // GRID).astype(np.int64)
        key = cx * 10_000_000 + cy
        g = cell_stats(key, zz, cls == 2)
        sus = []
        if tile['method'] == 'class9_adjacency':
            w = cell_stats(key, zz, cls == 9)
            for k9, (c9, m9) in w.items():
                if c9 < MIN_W or k9 not in g:
                    continue
                c2, m2 = g[k9]
                if c2 >= MIN_G and abs(m2 - m9) <= ZTOL:
                    sus.append((k9, c2, c9, m2, m9))
        else:  # density_only
            for k2, (c2, m2) in g.items():
                if c2 >= DENS_MIN and m2 <= Z_MAX:
                    sus.append((k2, c2, None, m2, None))
        if not sus:
            return dict(status='clean', n2=n2, n9=n9)
        dens = [c2 for _, c2, _, _, _ in sus]
        return dict(status='HIT', n2=n2, n9=n9, sus_cells=len(sus),
                    max_density=int(max(dens)), mean_density=int(np.mean(dens)),
                    area_km2=round(len(sus) * GRID * GRID / 1e6, 4),
                    examples=examples_for(sus, tile))
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
            r = audit_one(tile)
        except Exception as e:
            r = dict(status='error', err=str(e)[:200])
        r['name'] = tile['name']; r['survey'] = tile['survey']
        r['src'] = os.path.basename(tile['src'])
        r['method'] = tile['method']; r['group'] = tile['group']
        results.append(r)
        done_this_session += 1
        if (idx + 1) % EVERY == 0 or idx == total - 1:
            hits = sum(1 for q in results if q['status'] == 'HIT')
            el = time.time() - t0
            print(f"{idx+1}/{total} tiles audited (hits so far: {hits}, {el:.0f}s elapsed)", flush=True)
            save_ckpt(idx + 1)
        if LIMIT and done_this_session >= LIMIT:
            save_ckpt(idx + 1)
            print(f"LIMIT={LIMIT} reached; checkpoint saved at next_idx={idx+1}. Exiting.", flush=True)
            sys.exit(0)

tmp = OUT_PREFIX + 'results.json.tmp'
json.dump(results, open(tmp, 'w'))
os.replace(tmp, OUT_PREFIX + 'results.json')
hits = [r for r in results if r['status'] == 'HIT']
print(f"GAP AUDIT DONE. tiles={len(results)} hits={len(hits)} wall={time.time()-t0:.0f}s", flush=True)
