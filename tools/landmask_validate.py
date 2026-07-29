#!/usr/bin/env python3
"""
Guya Option 3 — validate the built mask against the v16.43 spike's own ground truth.

Two distinct questions, deliberately kept separate:

 1. FIDELITY - does this raster reimplementation reproduce the spike's vector verdicts?
    The spike's per-point OSM class and WOfS frequency survive in score_results.json, so
    every one of the 13,178 pilot points can be compared directly. This is what catches a
    botched flood-fill or a grid-alignment error.

 2. OUTCOME  - the real false-paint / kept-coverage figures for the mask as built, plus the
    17 named probes and the Maroochy Wetland Sanctuary defect grid.

Run AFTER landmask_build.py. Reads the .npy masks it writes.
"""
import json, os, sys
import numpy as np

RAW = os.path.join('data', 'raw', '_landmask_spike')
WOFS_FREQ_MIN = 0.2

_cache = {}


def load_regions():
    with open(os.path.join(RAW, 'landmask_payload.json')) as fh:
        blob = json.load(fh)
    out = []
    for r in blob['regions']:
        m = np.load(os.path.join(RAW, 'mask_%s.npy' % r['key']))
        out.append((r, m))
    return blob, out


def mask_at(regions, la, lo):
    """None = outside every region box (mask cannot speak -> caller must not exclude)."""
    for r, m in regions:
        if r['s'] <= la <= r['n'] and r['w'] <= lo <= r['e']:
            row = int((r['n'] - la) / (r['n'] - r['s']) * r['rows'])
            col = int((lo - r['w']) / (r['e'] - r['w']) * r['cols'])
            row = min(max(row, 0), r['rows'] - 1)
            col = min(max(col, 0), r['cols'] - 1)
            return bool(m[row, col])
    return None


def main():
    blob, regions = load_regions()
    with open(os.path.join(RAW, 'score_results.json')) as fh:
        sr = json.load(fh)
    rows = sr['results']
    probes = sr['probes']

    print('=' * 78)
    print('1. FIDELITY vs the v16.43 spike vector verdicts (13,178 pilot points)')
    print('=' * 78)
    agree = dis = outside = 0
    dis_dry = dis_wet = 0
    for cohort, la, lo, d, osm, wf in rows:
        mine = mask_at(regions, la, lo)
        if mine is None:
            outside += 1
            continue
        spike = (osm != 'land') and (wf is not None and wf >= WOFS_FREQ_MIN)
        if mine == spike:
            agree += 1
        else:
            dis += 1
            if cohort == 'dry':
                dis_dry += 1
            elif cohort == 'wet':
                dis_wet += 1
    tot = agree + dis
    print('  in-box %d, outside all boxes %d' % (tot, outside))
    if tot:
        print('  agreement %d/%d = %.2f%%   disagreements: %d (dry %d, wet %d)'
              % (agree, tot, 100.0 * agree / tot, dis, dis_dry, dis_wet))

    print()
    print('=' * 78)
    print('2. OUTCOME - mask as built')
    print('=' * 78)
    for cohort in ('dry', 'wet', 'messy'):
        pts = [r for r in rows if r[0] == cohort]
        inb = [r for r in pts if mask_at(regions, r[1], r[2]) is not None]
        wet = [r for r in inb if mask_at(regions, r[1], r[2])]
        if not inb:
            continue
        lbl = {'dry': 'dry->water  (FALSE PAINT)', 'wet': 'wet->water  (COVERAGE KEPT)',
               'messy': 'messy->water'}[cohort]
        print('  %-28s %5d / %-5d = %6.2f%%' % (lbl, len(wet), len(inb), 100.0 * len(wet) / len(inb)))

    print()
    print('  --- named probes ---')
    for p in probes:
        mine = mask_at(regions, p['la'], p['lo'])
        v = 'OUTSIDE' if mine is None else ('water' if mine else 'land ')
        exp = p['expect']
        ok = ('water' in exp and mine) or ('land' in exp and mine is False) or ('either' in exp or 'intertidal' in exp)
        print('   %-7s %-6s exp=%-22s %s' % (v, 'OK' if ok else 'FLAG', exp, p['name'][:46]))

    # ---- 3. Maroochy Wetland Sanctuary defect grid ---------------------------------------
    # The Fugro ground-classified-as-seabed defect zone (roadmap v16.17-v16.18). The spike's
    # 36-pt grid scored OSM 31 land / WOfS 34 land - the strongest evidence that both sources
    # structurally catch this defect class. Re-scored here against the mask as actually built.
    print()
    print('=' * 78)
    print('3. Maroochy Wetland Sanctuary defect grid (36 pts)')
    print('=' * 78)
    las = np.linspace(-26.653, -26.563, 6)
    los = np.linspace(153.030, 153.080, 6)
    vals = [mask_at(regions, la, lo) for la in las for lo in los]
    land = sum(1 for v in vals if v is False)
    water = sum(1 for v in vals if v is True)
    print('  land %d / water %d / outside %d  (spike: OSM 31 land, WOfS 34 land)'
          % (land, water, sum(1 for v in vals if v is None)))
    print('  -> defect zone suppressed' if land >= 30 else '  -> FLAG: defect zone not suppressed as expected')

    # ---- 4. genuine bathymetric soundings must not be false-negatived --------------------
    print()
    print('=' * 78)
    print('4. Genuine bathymetric soundings (mask must not kill real depth data)')
    print('=' * 78)
    import csv
    for name, path in (('Maroochy/Noosa v2 (19,178)', os.path.join('data', 'maroochy_noosa_bathy_v2_appgrade.csv')),
                       ('Maroochy/Noosa v1 (946,877)', os.path.join('data', 'maroochy_noosa_bathy_v1.csv'))):
        if not os.path.exists(path):
            continue
        tot = wet = outside = 0
        with open(path) as fh:
            rd = csv.reader(fh)
            next(rd)
            for i, row in enumerate(rd):
                if i % 7:           # thin v1; v2 is small enough that this is still thousands
                    continue
                try:
                    la, lo = float(row[0]), float(row[1])
                except Exception:
                    continue
                m = mask_at(regions, la, lo)
                tot += 1
                if m is None:
                    outside += 1
                elif m:
                    wet += 1
        if tot:
            print('  %-28s sampled %6d: mask=water %6d (%.1f%%), outside-box %6d (%.1f%%)'
                  % (name, tot, wet, 100.0 * wet / tot, outside, 100.0 * outside / tot))
    print('  NOTE: maroochy_noosa is EXEMPT by region key in depthSamples(), so the figures above')
    print('        are diagnostic only - no MN sample is filtered regardless of what the mask says.')
    print('  NOTE: Woongarra real depth data lives ONLY in the phone-side legacy blob (not in this')
    print('        repo), so it cannot be scored offline. Region key woongarra is exempt; the')
    print('        untagged legacy_unknown blob is NOT - see the on-phone check in the roadmap.')


if __name__ == '__main__':
    main()
