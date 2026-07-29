#!/usr/bin/env python3
"""
Guya Option 3 — STRICT-AND land/water mask: data acquisition.

Extends the v16.43 spike (data/raw/_landmask_spike/) from its single pilot bbox to the
full four-region footprint. Sourcing method is the spike's, unchanged:
  - OSM water/coastline/wetland via Overpass  (see overpass_query.txt)
  - DEA WOfS multi-year frequency via WCS 1.0 (see wcs_desc.xml)

Long-run discipline (v16.33 lesson): progress print per tile with flush, atomic
checkpoint (tmp + os.replace) after every tile, resume-from-checkpoint on restart,
and a --smoke mode that exercises all three paths on a small subset.

Usage:
  python tools/landmask_fetch.py --smoke     # 1 tile per region, exercises checkpoint+resume
  python tools/landmask_fetch.py             # full run, resumes from checkpoint if present
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

RAW = os.path.join('data', 'raw', '_landmask_spike')
TILES_DIR = os.path.join(RAW, 'tiles')
CKPT = os.path.join(RAW, 'fetch_checkpoint.json')

# NOTE: overpass.osm.ch is deliberately NOT here. It is a Switzerland-only instance and answers
# Australian bboxes with HTTP 200 + zero elements - a silent empty result, not an error. It wiped
# central Brisbane and Mooloolaba/Maroochy in the first full run before the empty-result guard in
# fetch_osm() was added. Any mirror added here must be verified to carry planet-wide data.
OVERPASS_MIRRORS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
]
_mirror_n = [0]
WCS = ('https://ows.dea.ga.gov.au/?service=WCS&version=1.0.0&request=GetCoverage'
       '&coverage=ga_ls_wo_fq_myear_3&measurements=frequency&format=GeoTIFF'
       '&crs=EPSG:4326&response_crs=EPSG:4326'
       '&bbox={w},{s},{e},{n}&width={cols}&height={rows}')

# Four current regions, as tight per-region boxes (Aaron's call: gaps between regions are
# pure waste in one combined box). Sunshine Coast and Moreton Bay overlap heavily and are
# contiguous, so they share one box - the union is SMALLER than the two boxes separately.
# Extents measured from the shipped CSVs + Woongarra/Bargara (Burnett Heads -24.7607,152.4063),
# each padded ~0.02 deg. maroochy_noosa is NOT covered: it is mask-exempt (genuine Fugro
# bathymetric soundings), so spending payload on it would be waste.
REGIONS = [
    # key,             south,   west,    north,   east
    ('woongarra',     -24.98, 152.30, -24.66, 152.60),
    ('seq_coast',     -27.35, 153.02, -26.34, 153.22),  # sunshine_coast + moreton_bay
    ('brisbane_river',-27.66, 152.72, -27.27, 153.34),
]

TILE_DEG = 0.25          # Overpass/WCS tile size - keeps each request well inside timeouts
CELL_DEG = 30.0 / 111320.0   # ~30 m, WOfS native resolution

OVERPASS_TPL = """[out:json][timeout:180];
(
  way["natural"="water"]({s},{w},{n},{e});
  relation["natural"="water"]({s},{w},{n},{e});
  way["waterway"="riverbank"]({s},{w},{n},{e});
  relation["waterway"="riverbank"]({s},{w},{n},{e});
  way["natural"="coastline"]({s},{w},{n},{e});
  way["natural"="wetland"]({s},{w},{n},{e});
  relation["natural"="wetland"]({s},{w},{n},{e});
);
out geom;
"""


def log(msg):
    print('[%s] %s' % (time.strftime('%H:%M:%S'), msg), flush=True)


def atomic_write(path, data, binary=False):
    """tmp + os.replace - never leave a half-written artefact on disk."""
    tmp = path + '.tmp'
    mode = 'wb' if binary else 'w'
    with open(tmp, mode) as fh:
        fh.write(data)
    os.replace(tmp, path)


def load_ckpt():
    if os.path.exists(CKPT):
        try:
            with open(CKPT) as fh:
                return json.load(fh)
        except Exception:
            log('checkpoint unreadable, starting clean')
    return {'done': []}


def save_ckpt(ck):
    atomic_write(CKPT, json.dumps(ck))


def tiles_for(key, s, w, n, e):
    out = []
    i = 0
    la = s
    while la < n - 1e-9:
        la2 = min(la + TILE_DEG, n)
        lo = w
        while lo < e - 1e-9:
            lo2 = min(lo + TILE_DEG, e)
            out.append({'id': '%s_%02d' % (key, i), 'region': key,
                        's': round(la, 6), 'w': round(lo, 6),
                        'n': round(la2, 6), 'e': round(lo2, 6)})
            i += 1
            lo = lo2
        la = la2
    return out


def fetch(url, data=None, tries=4, timeout=300):
    """Retry with backoff - Overpass rate-limits and DEA occasionally 503s."""
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data,
                                         headers={'User-Agent': 'Guya-landmask/1.0 (personal fishing app)'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as ex:
            last = ex
            wait = 5 * (2 ** k)
            log('  retry %d/%d after %s (%ss)' % (k + 1, tries, type(ex).__name__, wait))
            time.sleep(wait)
    raise RuntimeError('fetch failed after %d tries: %s' % (tries, last))


def ocean_fraction(tif_path):
    """Fraction of the tile WOfS calls near-permanent water. Used only as an independent
    sanity signal for accepting an empty Overpass result - never as a mask input itself."""
    try:
        import rasterio, numpy as np
        with rasterio.open(tif_path) as src:
            a = src.read(1)
        return float((np.nan_to_num(a, nan=0.0) >= 0.9).mean())
    except Exception:
        return 0.0


def fetch_osm(s, w, n, e, depth=0, ocean_hint=0.0):
    """Overpass, with adaptive quartering on timeout.

    Brisbane/Moreton are mapped densely enough that a flat 0.25 deg tile 504s outright
    (confirmed in the smoke run). Rather than pick a globally tiny tile size - which would
    multiply request count everywhere, including the sparse Woongarra coast - split only the
    tiles that actually fail, and merge the pieces back into one element list. Rotates
    mirrors per attempt: the public overpass-api.de instance rate-limits hard on bursts.
    """
    q = OVERPASS_TPL.format(s=s, w=w, n=n, e=e)
    empties = 0
    for m in range(len(OVERPASS_MIRRORS)):
        url = OVERPASS_MIRRORS[(_mirror_n[0] + m) % len(OVERPASS_MIRRORS)]
        try:
            body = fetch(url, data=q.encode('utf-8'), tries=2)
            els = json.loads(body.decode('utf-8', 'replace')).get('elements', [])
            if not els:
                # An empty result is ambiguous: a pure-ocean tile genuinely has no water
                # polygons and no coastline, but a misconfigured/regional mirror also answers
                # 200-with-nothing (overpass.osm.ch did exactly that - see MIRRORS above).
                # Prefer a second mirror's agreement; accept one if ocean_hint independently
                # says the tile is open water, since that is the case that legitimately has
                # nothing to return.
                empties += 1
                log('  mirror %s returned EMPTY (%d agree, ocean_hint=%.2f)'
                    % (url.split('/')[2], empties, ocean_hint))
                if empties >= 2 or ocean_hint >= 0.95:
                    log('  empty accepted - tile is genuinely featureless')
                    return []
                continue
            _mirror_n[0] = (_mirror_n[0] + m) % len(OVERPASS_MIRRORS)
            return els
        except Exception as ex:
            log('  mirror %s failed (%s)' % (url.split('/')[2], type(ex).__name__))
    if empties:
        # A mirror DID answer, and answered "nothing here". Splitting cannot help: this query
        # is spatially decomposable, so an empty result over the box implies an empty result
        # over every sub-box. Recursing here just multiplies rate-limited requests for no new
        # information (it burned ~18 min on one pure-ocean Woongarra tile before this guard).
        log('  empty from %d mirror(s), others unreachable - accepting empty, split cannot help' % empties)
        return []
    if depth >= 3:
        raise RuntimeError('overpass failed at max split depth for %s,%s,%s,%s' % (s, w, n, e))
    mla, mlo = (s + n) / 2.0, (w + e) / 2.0
    log('  splitting %.3f,%.3f,%.3f,%.3f (depth %d)' % (s, w, n, e, depth + 1))
    out = []
    seen = set()
    for (a, b, c, d) in ((s, w, mla, mlo), (s, mlo, mla, e), (mla, w, n, mlo), (mla, mlo, n, e)):
        for el in fetch_osm(a, b, c, d, depth + 1, ocean_hint):
            k = (el.get('type'), el.get('id'))
            if k not in seen:
                seen.add(k)
                out.append(el)
        time.sleep(1)
    return out


def do_tile(t):
    osm_path = os.path.join(TILES_DIR, t['id'] + '_osm.json')
    tif_path = os.path.join(TILES_DIR, t['id'] + '_wofs.tif')

    # WOfS first: it is fast, never rate-limited, and its open-water fraction is what lets an
    # empty Overpass answer be accepted on one mirror instead of two (see fetch_osm).
    if not os.path.exists(tif_path):
        cols = max(1, int(round((t['e'] - t['w']) / CELL_DEG)))
        rows = max(1, int(round((t['n'] - t['s']) / CELL_DEG)))
        url = WCS.format(w=t['w'], s=t['s'], e=t['e'], n=t['n'], cols=cols, rows=rows)
        body = fetch(url)
        if body[:2] not in (b'II', b'MM'):
            raise RuntimeError('WCS returned non-GeoTIFF for %s: %s' % (t['id'], body[:300]))
        atomic_write(tif_path, body, binary=True)

    if not os.path.exists(osm_path):
        els = fetch_osm(t['s'], t['w'], t['n'], t['e'], 0, ocean_fraction(tif_path))
        atomic_write(osm_path, json.dumps({'elements': els}))
        time.sleep(2)   # be polite to Overpass between tiles

    return os.path.getsize(osm_path), os.path.getsize(tif_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--smoke', action='store_true',
                    help='one tile per region; exercises progress+checkpoint+resume')
    args = ap.parse_args()

    os.makedirs(TILES_DIR, exist_ok=True)
    log('pid %d  mode=%s' % (os.getpid(), 'SMOKE' if args.smoke else 'FULL'))

    all_tiles = []
    for r in REGIONS:
        ts = tiles_for(*r)
        all_tiles.extend(ts[:1] if args.smoke else ts)

    ck = load_ckpt()
    done = set(ck['done'])
    log('%d tiles planned, %d already done (resuming)' % (len(all_tiles), len(done)))

    t0 = time.time()
    for i, t in enumerate(all_tiles, 1):
        if t['id'] in done:
            log('%3d/%d %s SKIP (checkpoint)' % (i, len(all_tiles), t['id']))
            continue
        a, b = do_tile(t)
        done.add(t['id'])
        ck['done'] = sorted(done)
        save_ckpt(ck)          # atomic checkpoint after EVERY tile
        log('%3d/%d %s ok  osm=%.1fkB wofs=%.1fkB  (%.0fs elapsed)'
            % (i, len(all_tiles), t['id'], a / 1024, b / 1024, time.time() - t0))

    manifest = {'regions': [{'key': r[0], 's': r[1], 'w': r[2], 'n': r[3], 'e': r[4]} for r in REGIONS],
                'tiles': all_tiles, 'cell_deg': CELL_DEG, 'smoke': args.smoke}
    atomic_write(os.path.join(RAW, 'fetch_manifest.json'), json.dumps(manifest, indent=1))
    log('DONE %d tiles in %.0fs' % (len(all_tiles), time.time() - t0))


if __name__ == '__main__':
    main()
