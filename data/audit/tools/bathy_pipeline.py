"""Maroochy/Noosa offshore bathymetry -> LAT-referenced lat,lng,depth CSV.

Source rules (v16.31/v16.32 investigation):
- Depth points ONLY from Classified/Offshore_AHD_tidal_data, classes 13+15.
  Onshore folders carry the ground-classified-as-seabed defect; never read them.
- Hard point-level exclusion of the Maroochy Wetland Sanctuary defect zone
  (E 503000-508000 / N 7052000-7062000 MGA56) on top of the folder restriction.
- Z treated as standard AHD (Fugro RoS: "shifted to the AHD datum"), converted
  to LAT via the same per-port offsets used by export_csv.py.
- Clip to the real Area-A block E 496000-524000 / N 7040000-7136000.

Env: SMOKE=<n> (spread sample of n tiles, no checkpoint, output to _inventory),
     CHECKPOINT_EVERY (default 50), PROGRESS_EVERY (default 25).
"""
import io, json, os, sys, zipfile
from collections import Counter
import numpy as np
import laspy
from pyproj import Transformer

ZIP_PATH = "D:/Claude Code/data/raw/Bathymetric-LiDAR-Sunshine-Coast/DP_LIDAR_SunshineCoast.zip"
SRC_PREFIX = "DP_LIDAR_SunshineCoast/DP_LIDAR_SunshineCoast/Classified/Offshore_AHD_tidal_data/"
INV = "D:/Claude Code/data/raw/_inventory/"
CHECKPOINT_PATH = INV + "bathy_checkpoint.json"
OUT_CSV = "D:/Claude Code/data/maroochy_noosa_bathy_v1.csv"

SMOKE = int(os.environ.get("SMOKE", "0"))
CHECKPOINT_EVERY = int(os.environ.get("CHECKPOINT_EVERY", "50"))
PROGRESS_EVERY = int(os.environ.get("PROGRESS_EVERY", "25"))

GRID = 25  # metres, same as intertidal pipeline
KEEP_CLASSES = (13, 15)  # Fugro RoS: 13=Seabed, 15=20m subset of 13 (14 documented but absent)

# real Area-A survey block (v16.31, tile-grid derived — not the loose ISO bbox)
EXT_E_MIN, EXT_E_MAX = 496000.0, 524000.0
EXT_N_MIN, EXT_N_MAX = 7040000.0, 7136000.0
# Maroochy Wetland Sanctuary defect zone (v16.32, empirically located, 23 tiles)
DEF_E_MIN, DEF_E_MAX = 503000.0, 508000.0
DEF_N_MIN, DEF_N_MAX = 7052000.0, 7062000.0

# port offset by latitude bucket (MSL-above-LAT(1992), MSQ 2024 Semidiurnal Tidal
# Planes) — identical to export_csv.py; keep the two in sync
def port_offset(lat):
    if lat > -26.533:
        return 1.15  # Noosa Head
    elif lat > -26.908:
        return 1.00  # Mooloolaba
    else:
        return 1.26  # Beachmere / Moreton Bay secondary

print(f"PID {os.getpid()}", flush=True)

# cells: (grid_e, grid_n) -> [weighted_sum_of_tile_medians, point_count]
cells = {}
stats = Counter()
start_idx = 0

def save_checkpoint(next_idx):
    tmp = CHECKPOINT_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({
            "next_idx": next_idx,
            "cells": [[k[0], k[1], v[0], v[1]] for k, v in cells.items()],
            "stats": dict(stats),
        }, f)
    os.replace(tmp, CHECKPOINT_PATH)

def load_checkpoint():
    global start_idx
    if SMOKE or not os.path.exists(CHECKPOINT_PATH):
        return
    with open(CHECKPOINT_PATH) as f:
        data = json.load(f)
    for ge, gn, wsum, cnt in data["cells"]:
        cells[(ge, gn)] = [wsum, cnt]
    stats.update({k: int(v) for k, v in data["stats"].items()})
    start_idx = data["next_idx"]
    print(f"RESUMED from checkpoint: next_idx={start_idx}, cells={len(cells)}", flush=True)

def process_one(zf, name):
    las = laspy.read(io.BytesIO(zf.read(name)))
    cls = np.asarray(las.classification)
    stats["points_total"] += len(cls)
    stats["class13"] += int((cls == 13).sum())
    stats["class15"] += int((cls == 15).sum())
    mask = np.isin(cls, KEEP_CLASSES)
    if not mask.any():
        return 0
    x = np.asarray(las.x)[mask]
    y = np.asarray(las.y)[mask]
    z = np.asarray(las.z)[mask]

    in_ext = (x >= EXT_E_MIN) & (x <= EXT_E_MAX) & (y >= EXT_N_MIN) & (y <= EXT_N_MAX)
    stats["dropped_extent"] += int((~in_ext).sum())
    in_def = (x >= DEF_E_MIN) & (x <= DEF_E_MAX) & (y >= DEF_N_MIN) & (y <= DEF_N_MAX)
    stats["dropped_defect_zone"] += int((in_def & in_ext).sum())
    keep = in_ext & ~in_def
    if not keep.any():
        return 0
    x, y, z = x[keep], y[keep], z[keep]
    stats["points_kept"] += len(z)

    ge = np.round(x / GRID).astype(np.int64)
    gn = np.round(y / GRID).astype(np.int64)
    key = ge * 1_000_000 + gn  # gn max ~285,440 < 1e6, no collision
    order = np.argsort(key, kind="stable")
    key_s, z_s = key[order], z[order]
    bounds = np.flatnonzero(np.r_[True, key_s[1:] != key_s[:-1], True])
    for i in range(len(bounds) - 1):
        lo, hi = bounds[i], bounds[i + 1]
        k = int(key_s[lo])
        cell = (k // 1_000_000, k % 1_000_000)
        med = float(np.median(z_s[lo:hi]))
        cnt = int(hi - lo)  # cast: np.int64 is not JSON-serializable at checkpoint
        cur = cells.get(cell)
        if cur is None:
            cells[cell] = [med * cnt, cnt]
        else:
            cur[0] += med * cnt
            cur[1] += cnt
    return len(z)

with zipfile.ZipFile(ZIP_PATH) as zf:
    names = sorted(n for n in zf.namelist()
                   if n.startswith(SRC_PREFIX) and n.lower().endswith(".las"))
    print(f"source tiles in scope: {len(names)} (Offshore_AHD_tidal_data only)", flush=True)
    if SMOKE:
        step = max(1, len(names) // SMOKE)
        names = names[::step][:SMOKE]
        print(f"SMOKE MODE: {len(names)} tiles, even spread, no checkpointing", flush=True)

    load_checkpoint()
    total = len(names)
    for idx in range(start_idx, total):
        try:
            process_one(zf, names[idx])
        except Exception as e:
            stats["tile_errors"] += 1
            print(f"[{idx+1}/{total}] ERROR {os.path.basename(names[idx])}: {e}", flush=True)
        if (idx + 1) % PROGRESS_EVERY == 0 or idx == total - 1:
            print(f"{idx+1}/{total} tiles | cells={len(cells):,} | kept={stats['points_kept']:,}", flush=True)
        if not SMOKE and ((idx + 1) % CHECKPOINT_EVERY == 0 or idx == total - 1):
            save_checkpoint(idx + 1)

print(f"tiles done. stats: {dict(stats)}", flush=True)

# collapse: cell centre -> lat/lng, AHD -> LAT depth
ge = np.array([k[0] for k in cells], dtype=np.float64) * GRID
gn = np.array([k[1] for k in cells], dtype=np.float64) * GRID
z_ahd = np.array([v[0] / v[1] for v in cells.values()], dtype=np.float64)

tr = Transformer.from_crs("EPSG:28356", "EPSG:4326", always_xy=True)
lon, lat = tr.transform(ge, gn)
off = np.where(lat > -26.533, 1.15, np.where(lat > -26.908, 1.00, 1.26))
assert float(off.min()) >= 1.00, "unexpected Beachmere-bucket latitude in this block"
depth = -z_ahd - off  # positive = submerged below LAT, negative = dries above LAT

n = len(depth)
n_neg = int((depth < 0).sum())
n_pos = n - n_neg
print(f"cells={n:,}  depth range {depth.min():.2f} .. {depth.max():.2f} m", flush=True)
print(f"negative (dries above LAT): {n_neg:,} ({100*n_neg/max(n,1):.1f}%)  "
      f"positive (submerged): {n_pos:,} ({100*n_pos/max(n,1):.1f}%)", flush=True)
for lo_b, hi_b in [(0, 5), (5, 10), (10, 20), (20, 30), (30, 45)]:
    c = int(((depth >= lo_b) & (depth < hi_b)).sum())
    print(f"  depth {lo_b:>2}-{hi_b}m: {c:,}", flush=True)

# sanity gate (rule 7): a bathy export must NOT look like an intertidal export.
# Require a real submerged majority reaching genuine offshore depths.
if n == 0 or n_pos / n < 0.5 or float(depth.max()) < 20.0:
    print("SANITY GATE FAILED — output looks wrong for offshore bathymetry "
          "(expected mostly-positive depths reaching 30-40m). NOT writing CSV.", flush=True)
    sys.exit(2)

out_path = INV + "bathy_smoke.csv" if SMOKE else OUT_CSV
with open(out_path, "w", newline="") as f:
    f.write("lat,lng,depth\n")
    for i in range(n):
        f.write(f"{lat[i]:.6f},{lon[i]:.6f},{depth[i]:.2f}\n")
print(f"wrote {n:,} rows to {out_path}", flush=True)
print(f"OVER 25000-POINT IMPORT CAP: {'YES' if n > 25000 else 'no'} -- app will auto-thin on import", flush=True)
