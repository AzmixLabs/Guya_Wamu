#!/usr/bin/env python3
"""
Guya Option 3 — STRICT-AND land/water mask: rasterise, combine, encode.

Reads the tiles fetched by landmask_fetch.py and produces one packed bitmap per region:

    water(cell) := OSM_water(cell)  AND  WOfS_frequency(cell) >= WOFS_FREQ_MIN

OSM_water is the union of:
  - natural=water / waterway=riverbank / natural=wetland polygons (incl. multipolygon holes)
  - the ocean, recovered by flood-filling from box-edge cells that WOfS calls open water,
    with natural=coastline rasterised as an 8-connected barrier.

The flood fill replaces the spike's vector "split the bbox by the merged coastline" step.
Same intent, but robust to the dangling coastline ends you always get when clipping ways to a
box - a raster barrier does not need closed rings. Over-inclusion from a leaking fill is
largely corrected by the AND with WOfS; under-inclusion is the direction that costs coverage,
so fidelity is measured against the spike's own per-point vector verdicts (see landmask_validate.py).

Output: data/raw/_landmask_spike/landmask_payload.json  (the blob pasted into index.html)
"""
import base64, glob, json, os, sys, time

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from shapely.geometry import Polygon, LineString, box as shbox
from shapely.ops import unary_union
from scipy.spatial import cKDTree

RAW = os.path.join('data', 'raw', '_landmask_spike')
TILES = os.path.join(RAW, 'tiles')

WOFS_FREQ_MIN = 0.2      # spike's starting value; mirrored as WOFS_FREQ_MIN in index.html
OCEAN_SEED_FREQ = 0.9    # box-edge cells this wet are certainly open water -> flood-fill seeds


def log(m):
    print('[%s] %s' % (time.strftime('%H:%M:%S'), m), flush=True)


def load_manifest():
    with open(os.path.join(RAW, 'fetch_manifest.json')) as fh:
        return json.load(fh)


def osm_geoms(region_key):
    """Water/wetland polygons and coastline lines from every tile of this region."""
    polys, lines = [], []
    nodes = {}
    files = sorted(glob.glob(os.path.join(TILES, region_key + '_*_osm.json')))
    raw = []
    for f in files:
        with open(f) as fh:
            raw.extend(json.load(fh).get('elements', []))
    # ways first (geometry is inlined by `out geom`), then relations referencing them
    ways = {}
    for el in raw:
        if el.get('type') == 'way' and el.get('geometry'):
            coords = [(p['lon'], p['lat']) for p in el['geometry']]
            ways[el['id']] = coords
            tags = el.get('tags', {}) or {}
            if tags.get('natural') == 'coastline':
                if len(coords) >= 2:
                    lines.append(LineString(coords))
            elif len(coords) >= 4 and coords[0] == coords[-1]:
                try:
                    polys.append(Polygon(coords))
                except Exception:
                    pass
    for el in raw:
        if el.get('type') != 'relation':
            continue
        outers, inners = [], []
        for m in el.get('members', []):
            g = m.get('geometry')
            c = [(p['lon'], p['lat']) for p in g] if g else ways.get(m.get('ref'))
            if not c or len(c) < 4:
                continue
            if c[0] != c[-1]:
                c = c + [c[0]]
            (outers if m.get('role') != 'inner' else inners).append(c)
        for o in outers:
            try:
                polys.append(Polygon(o, [i for i in inners if Polygon(o).contains(Polygon(i).representative_point())]))
            except Exception:
                try:
                    polys.append(Polygon(o))
                except Exception:
                    pass
    return polys, lines


def build_region(reg, cell_deg):
    key = reg['key']
    s, w, n, e = reg['s'], reg['w'], reg['n'], reg['e']
    cols = int(round((e - w) / cell_deg))
    rows = int(round((n - s) / cell_deg))
    tr = from_bounds(w, s, e, n, cols, rows)
    log('%s: %d x %d cells (%.3f deg^2)' % (key, cols, rows, (n - s) * (e - w)))

    # ---- WOfS frequency mosaic over the region grid -------------------------------------
    freq = np.full((rows, cols), np.nan, dtype='float32')
    for f in sorted(glob.glob(os.path.join(TILES, key + '_*_wofs.tif'))):
        with rasterio.open(f) as src:
            a = src.read(1)
            b = src.bounds
            # map this tile's cells into the region grid by nearest-cell index
            r0 = int(round((n - b.top) / cell_deg))
            c0 = int(round((b.left - w) / cell_deg))
            r1, c1 = min(rows, r0 + a.shape[0]), min(cols, c0 + a.shape[1])
            if r1 <= r0 or c1 <= c0:
                continue
            sub = a[:r1 - r0, :c1 - c0]
            tgt = freq[r0:r1, c0:c1]
            m = ~np.isnan(sub)
            tgt[m] = sub[m]
    wofs_ok = np.nan_to_num(freq, nan=0.0) >= WOFS_FREQ_MIN
    log('  wofs >= %.2f : %.1f%% of cells' % (WOFS_FREQ_MIN, 100.0 * wofs_ok.mean()))

    # ---- OSM polygons + coastline -------------------------------------------------------
    polys, lines = osm_geoms(key)
    log('  osm: %d polygons, %d coastline ways' % (len(polys), len(lines)))
    # all_touched=False deliberately: all_touched=True marks every cell a polygon merely clips,
    # dilating each water body by up to one 30 m cell. That biases the mask towards MORE water,
    # i.e. towards false paint - the exact direction this feature exists to suppress. Measured
    # 1.28% dry->water with dilation vs 0.79% for the spike's exact point-in-polygon test;
    # cell-centre containment is both closer to the spike and conservative in the right direction.
    poly_r = np.zeros((rows, cols), dtype='uint8')
    if polys:
        poly_r = rasterize(((g, 1) for g in polys if g.is_valid or g.buffer(0).is_valid),
                           out_shape=(rows, cols), transform=tr, fill=0,
                           all_touched=False, dtype='uint8')

    # ---- ocean by OSM's coastline-direction rule ----------------------------------------
    # A flood fill was tried first and is WRONG here: seeding from wet box-edge cells lets an
    # inland dam or river on the LAND side of the coast seed the fill, and land is one connected
    # region, so the whole box floods. Measured 99.8%/93.2%/99.3% "ocean" - which collapsed
    # STRICT-AND onto WOfS-alone and threw away the OSM half of the conjunction entirely.
    #
    # Instead use the actual OSM invariant: natural=coastline ways are directed with LAND ON THE
    # LEFT and SEA ON THE RIGHT. For a segment direction d and a vector v from the segment to the
    # cell, cross = dx*vy - dy*vx; cross < 0 means the cell lies to the right, i.e. seaward.
    # This is a purely local test - no closed rings, so clipping ways at the box edge is harmless,
    # which is exactly what defeated the fill.
    ocean = np.zeros((rows, cols), dtype=bool)
    seg_p, seg_d = [], []
    for ln in lines:
        c = np.asarray(ln.coords, dtype='float64')
        if len(c) < 2:
            continue
        a, b = c[:-1], c[1:]
        # densify so the nearest-segment lookup can't skip past long straight runs
        L = np.hypot(*(b - a).T)
        for k in range(len(a)):
            steps = max(1, int(L[k] / (cell_deg * 2)))
            t = np.linspace(0, 1, steps + 1)[:-1][:, None]
            seg_p.append(a[k] + t * (b[k] - a[k]))
            seg_d.append(np.repeat((b[k] - a[k])[None, :], len(t), axis=0))
    if seg_p:
        P = np.vstack(seg_p)
        D = np.vstack(seg_d)
        tree = cKDTree(P)
        latg = n - (np.arange(rows) + 0.5) * (n - s) / rows
        lngg = w + (np.arange(cols) + 0.5) * (e - w) / cols
        LO, LA = np.meshgrid(lngg, latg)
        q = np.column_stack([LO.ravel(), LA.ravel()])
        _, idx = tree.query(q, workers=-1)
        v = q - P[idx]
        d = D[idx]
        cross = d[:, 0] * v[:, 1] - d[:, 1] * v[:, 0]
        ocean = (cross < 0).reshape(rows, cols)
        log('  ocean (coastline side-test): %.1f%% of cells, %d densified coast pts'
            % (100.0 * ocean.mean(), len(P)))
    else:
        log('  ocean: no coastline in region - polygons + WOfS only')

    osm_water = (poly_r == 1) | ocean
    water = osm_water & wofs_ok
    log('  osm_water %.1f%%  ->  STRICT-AND %.1f%%' % (100.0 * osm_water.mean(), 100.0 * water.mean()))
    return {'key': key, 's': s, 'w': w, 'n': n, 'e': e,
            'cols': cols, 'rows': rows}, water


def rle_encode(bits):
    """Row-major run lengths, alternating, starting with a 0-run. Varint, base64."""
    flat = bits.reshape(-1)
    idx = np.flatnonzero(np.diff(flat.astype('uint8')))
    runs = np.diff(np.concatenate(([-1], idx, [flat.size - 1])))
    out = bytearray()
    if flat.size and flat[0]:
        out.append(0)                     # leading zero-length 0-run: first run is water
    for r in runs:
        v = int(r)
        while True:
            b = v & 0x7F
            v >>= 7
            out.append(b | (0x80 if v else 0))
            if not v:
                break
    return base64.b64encode(bytes(out)).decode('ascii')


def main():
    man = load_manifest()
    cell = man['cell_deg']
    regions, payload = [], []
    for reg in man['regions']:
        meta, water = build_region(reg, cell)
        enc = rle_encode(water)
        meta['rle'] = enc
        raw_kb = water.size / 8 / 1024
        log('  encoded %.1f kB (raw 1-bit would be %.1f kB, %.1fx)'
            % (len(enc) / 1024, raw_kb, raw_kb * 1024 / max(1, len(enc))))
        regions.append(meta)
        np.save(os.path.join(RAW, 'mask_%s.npy' % meta['key']), water)
    blob = {'v': 1, 'cell': cell, 'freqMin': WOFS_FREQ_MIN, 'regions': regions}
    js = json.dumps(blob, separators=(',', ':'))
    with open(os.path.join(RAW, 'landmask_payload.json'), 'w') as fh:
        fh.write(js)
    log('TOTAL payload %.1f kB (%.3f MB)' % (len(js) / 1024, len(js) / 1048576))


if __name__ == '__main__':
    main()
