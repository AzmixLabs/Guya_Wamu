"""Thin maroochy_noosa_bathy_v1.csv to an app-grade export (18-20k points).

Reads v1 (read-only), buckets on a coarser MGA56 grid using the same
origin/round() convention as the 25 m pipeline grid, keeps the DEEPEST source
point per cell (max depth value = lowest seabed, uniform across submerged and
dries; ties -> first-encountered). No averaging. v1 untouched.

Env: CELL=<metres> to run the full pass; unset = probe mode (arithmetic +
occupied-cell counts for candidate sizes, no output written).
"""
import os, sys
import numpy as np
from pyproj import Transformer

V1 = "D:/Claude Code/data/maroochy_noosa_bathy_v1.csv"
OUT = "D:/Claude Code/data/maroochy_noosa_bathy_v2_appgrade.csv"
TARGET_LO, TARGET_HI = 18000, 20000

# Maroochy Wetland Sanctuary exclusion box (must stay empty post-thin)
DEF_E_MIN, DEF_E_MAX = 503000.0, 508000.0
DEF_N_MIN, DEF_N_MAX = 7052000.0, 7062000.0

data = np.genfromtxt(V1, delimiter=",", skip_header=1, dtype=np.float64)
lat, lng, depth = data[:, 0], data[:, 1], data[:, 2]
n_rows = len(depth)
print(f"v1 rows: {n_rows:,}  depth {depth.min():.2f}..{depth.max():.2f}", flush=True)

# lat/lng back to MGA56 for gridding (inverse of the v1 export transform)
tr = Transformer.from_crs("EPSG:4326", "EPSG:28356", always_xy=True)
e, n = tr.transform(lng, lat)
e, n = np.asarray(e), np.asarray(n)

# v1 quirk: 13 rows are 25m-cell centres sitting exactly ON the exclusion box's
# eastern edge (E=508,000, penetration <=0.05m float noise) — their source points
# were all strictly outside the box, but the coordinates are boundary-ambiguous.
# Drop them so the v2 output tests clean against the inclusive box.
src_in_box = ((e >= DEF_E_MIN) & (e <= DEF_E_MAX) &
              (n >= DEF_N_MIN) & (n <= DEF_N_MAX))
if src_in_box.any():
    print(f"dropping {int(src_in_box.sum())} v1 boundary-edge rows (cell centres on the exclusion box line)", flush=True)
    keep_src = ~src_in_box
    lat, lng, depth = lat[keep_src], lng[keep_src], depth[keep_src]
    e, n = e[keep_src], n[keep_src]
    n_rows = len(depth)

def occupied(cell):
    ge = np.round(np.asarray(e) / cell).astype(np.int64)
    gn = np.round(np.asarray(n) / cell).astype(np.int64)
    return len(np.unique(ge * 1_000_000 + gn)), ge, gn

CELL = os.environ.get("CELL")
if CELL is None:
    mid = (TARGET_LO + TARGET_HI) / 2
    ratio = n_rows / mid
    lin = ratio ** 0.5
    print(f"arithmetic: {n_rows:,} / {mid:,.0f} target = {ratio:.1f}x area reduction", flush=True)
    print(f"            sqrt({ratio:.1f}) = {lin:.2f}x linear -> 25 m x {lin:.2f} = {25*lin:.1f} m cell", flush=True)
    for cand in (150, 175, 180, 200):
        cnt, _, _ = occupied(cand)
        mark = " <-- in 18-20k range" if TARGET_LO <= cnt <= TARGET_HI else ""
        print(f"  CELL={cand} m -> {cnt:,} occupied cells{mark}", flush=True)
    sys.exit(0)

cell = float(CELL)
cnt, ge, gn = occupied(cell)
print(f"full pass at CELL={cell:g} m -> {cnt:,} cells", flush=True)

# conditional per-cell selection, ties -> first-encountered:
#   cell has ANY submerged point (depth >= 0, matching the split convention)
#     -> keep greatest signed depth (protects shallow water in mixed cells)
#   cell is all-negative (pure dries)
#     -> keep greatest |depth| = most-negative (most-exposed crest)
key = ge * 1_000_000 + gn
uk, inv = np.unique(key, return_inverse=True)
cell_has_sub = np.zeros(len(uk), dtype=bool)
np.logical_or.at(cell_has_sub, inv, depth >= 0)
score = np.where(cell_has_sub[inv], depth, -depth)
order = np.lexsort((np.arange(n_rows), -score, key))  # key asc, score desc, row asc
key_s = key[order]
first = np.r_[True, key_s[1:] != key_s[:-1]]
keep_idx = order[first]

# diff vs both prior rules (run 1 signed-max, run 2 flat |depth|)
def keep_under(sort_col):
    o = np.lexsort((np.arange(n_rows), sort_col, key))
    return o[np.r_[True, key[o][1:] != key[o][:-1]]]
keep_r1 = keep_under(-depth)
keep_r2 = keep_under(-np.abs(depth))
print(f"diff vs run 1 (signed-max): {int((depth[keep_idx] != depth[keep_r1]).sum())} cells differ; "
      f"mixed flips vs run 1: {int(((depth[keep_idx] < 0) & (depth[keep_r1] >= 0)).sum())} (must be 0)", flush=True)
print(f"diff vs run 2 (flat |depth|): {int((depth[keep_idx] != depth[keep_r2]).sum())} cells differ", flush=True)

# show one run-2-flipped mixed cell recovering its submerged reading
flip2 = np.flatnonzero((depth[keep_r2] < 0) & (depth[keep_r1] >= 0))
if len(flip2):
    p = flip2[0]
    lo, hi = np.flatnonzero(np.r_[first, True])[p], np.flatnonzero(np.r_[first, True])[p + 1]
    grp = order[lo:hi]
    ge_c, gn_c = int(key_s[lo] // 1_000_000), int(key_s[lo] % 1_000_000)
    ds = ", ".join(f"{d:.2f}" for d in np.sort(depth[grp]))
    print(f"flipped-cell check cell({ge_c},{gn_c}) n={hi-lo}: depths[{ds}] "
          f"run1={depth[keep_r1][p]:.2f} run2={depth[keep_r2][p]:.2f} now={depth[keep_idx][p]:.2f}", flush=True)

k_lat, k_lng, k_dep = lat[keep_idx], lng[keep_idx], depth[keep_idx]
k_e, k_n = np.asarray(e)[keep_idx], np.asarray(n)[keep_idx]

in_box = ((k_e >= DEF_E_MIN) & (k_e <= DEF_E_MAX) &
          (k_n >= DEF_N_MIN) & (k_n <= DEF_N_MAX))
print(f"exclusion-box check: {int(in_box.sum())} kept points inside Wetland Sanctuary box (must be 0)", flush=True)
assert not in_box.any(), "exclusion zone violated"

# spot-check: 5 spread cells with >=3 source points
sizes = np.diff(np.flatnonzero(np.r_[first, True]))
rich = np.flatnonzero(sizes >= 3)
picks = rich[np.linspace(0, len(rich) - 1, 5).astype(int)]
bounds = np.flatnonzero(np.r_[first, True])
print("spot-check (kept must be signed-max if cell has submerged, else most-negative):", flush=True)
ok = True
for p in picks:
    lo, hi = bounds[p], bounds[p + 1]
    grp = order[lo:hi]
    kept = depth[order[lo]]
    d_grp = depth[grp]
    expected = d_grp.max() if (d_grp >= 0).any() else d_grp.min()
    ok &= (kept == expected)
    ge_c, gn_c = int(key_s[lo] // 1_000_000), int(key_s[lo] % 1_000_000)
    ds = np.sort(d_grp)
    show = ", ".join(f"{d:.2f}" for d in (ds if len(ds) <= 8 else ds[-8:]))
    print(f"  cell({ge_c},{gn_c}) n={hi-lo}: depths[{'...' if len(ds) > 8 else ''}{show}] kept={kept:.2f} expected={expected:.2f} {'OK' if kept == expected else 'MISMATCH'}", flush=True)
assert ok, "spot-check failed"

with open(OUT, "w", newline="") as f:
    f.write("lat,lng,depth\n")
    for i in range(len(k_dep)):
        f.write(f"{k_lat[i]:.6f},{k_lng[i]:.6f},{k_dep[i]:.2f}\n")
mb = os.path.getsize(OUT) / 1e6
print(f"wrote {len(k_dep):,} rows to {OUT} ({mb:.2f} MB)", flush=True)
print(f"depth range {k_dep.min():.2f}..{k_dep.max():.2f}  "
      f"negative {int((k_dep < 0).sum()):,} / positive {int((k_dep >= 0).sum()):,}", flush=True)
print(f"UNDER 25k CAP: {'yes' if len(k_dep) <= 25000 else 'NO'}", flush=True)
