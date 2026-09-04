# Merge gap-audit results into audit_results.json (append-only) + final summary.
# - Backs up audit_results.json to audit_results.pre_gap.bak.json first.
# - Appends gap_results.json entries; never alters existing entries.
# - Refuses to run twice (checks for a sentinel entry already merged).
# Artifact-scale filter = HIT with sus_cells >= 50 (reproduces the v16.18 table exactly:
# 192 tiles / 13.61 km2 on the existing results).
import json, os, shutil
from collections import defaultdict

BASE = 'D:/Claude Code/data/raw/_inventory/'
res = json.load(open(BASE + 'audit_results.json'))
gap = json.load(open(BASE + 'gap_results.json'))

existing_names = {r['name'] for r in res}
gap_a = [r for r in gap if r['group'] == 'A']
gap_b = [r for r in gap if r['group'] == 'B']
dup_a = [r['name'] for r in gap_a if r['name'] in existing_names]
if dup_a:
    raise SystemExit(f'REFUSING: {len(dup_a)} Group A names already in audit_results.json: {dup_a[:5]}')
already = [r for r in res if r.get('method')]
if already:
    raise SystemExit(f'REFUSING: audit_results.json already contains {len(already)} method-tagged entries — merge appears done.')

shutil.copy2(BASE + 'audit_results.json', BASE + 'audit_results.pre_gap.bak.json')
merged = res + gap
tmp = BASE + 'audit_results.json.tmp'
json.dump(merged, open(tmp, 'w'))
os.replace(tmp, BASE + 'audit_results.json')
print(f'MERGED: {len(res)} existing + {len(gap)} new = {len(merged)} entries '
      f'(backup: audit_results.pre_gap.bak.json)')

def table(rows, label):
    agg = defaultdict(lambda: [0, 0, 0, 0.0])  # tiles, raw hits, artifact tiles, artifact km2
    for r in rows:
        a = agg[r['survey']]
        a[0] += 1
        if r['status'] == 'HIT':
            a[1] += 1
            if r.get('sus_cells', 0) >= 50:
                a[2] += 1; a[3] += r['area_km2']
    print(f'\n{label}')
    print(f'{"survey":30s} {"tiles":>6s} {"rawHIT":>7s} {"artTiles":>9s} {"artKm2":>8s}')
    tt = [0, 0, 0, 0.0]
    for s, a in sorted(agg.items()):
        print(f'{s:30s} {a[0]:6d} {a[1]:7d} {a[2]:9d} {a[3]:8.2f}')
        for i in range(4): tt[i] += a[i]
    print(f'{"TOTAL":30s} {tt[0]:6d} {tt[1]:7d} {tt[2]:9d} {tt[3]:8.2f}')
    return tt

# include the 12 already-audited Group A spot tiles in the Group A picture
spot = [r for r in res if r['survey'] in
        ('Sunshine_Coast_2022_LGA', 'SunshineCoast_2014_LGA', 'Noosa_2022_LGA')
        and not r.get('method')]
ta = table(gap_a + spot, 'GROUP A (class-9 adjacency, incl. 12 spot-sample tiles)')
tb = table(gap_b, 'GROUP B (density-only, 2009 vintages)')

err = [r for r in gap if r['status'] == 'error']
print(f'\nerrors: {len(err)}')
for r in err[:10]: print(' ', r['name'], r.get('err', ''))

prev_art_tiles, prev_art_km2 = 192, 13.61
# spot tiles were already inside the 192/13.61 figure — count only NEW artifact-scale adds
new_a = [r for r in gap_a if r['status'] == 'HIT' and r.get('sus_cells', 0) >= 50]
new_b = [r for r in gap_b if r['status'] == 'HIT' and r.get('sus_cells', 0) >= 50]
add_t = len(new_a) + len(new_b)
add_k = sum(r['area_km2'] for r in new_a + new_b)
print(f'\nROADMAP FIGURE UPDATE: was {prev_art_tiles} tiles / {prev_art_km2} km2 (v16.18).')
print(f'Gap audit adds {len(new_a)} Group A + {len(new_b)} Group B artifact-scale tiles '
      f'(+{add_k:.2f} km2).')
print(f'NEW TOTAL: {prev_art_tiles + add_t} tiles / {prev_art_km2 + add_k:.2f} km2 at artifact scale.')
