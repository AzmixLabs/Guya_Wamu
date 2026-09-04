import re, glob, json

# survey group -> (port offset above LAT, horizontal EPSG, priority rank; lower=newer=wins)
GROUP_META = {
    'Sunshine_Coast_2022_LGA': dict(port='Mooloolaba', offset=1.00, epsg=7856, rank=0),
    'Noosa_2022_LGA':          dict(port='Noosa Head', offset=1.15, epsg=7856, rank=0),
    'Moreton_Bay_2018_LGA':    dict(port='Beachmere',  offset=1.26, epsg=28356, rank=1),
    'SunshineCoast_2014_LGA':  dict(port='Mooloolaba', offset=1.00, epsg=28356, rank=2),
    'MoretonBay_2014_LGA':     dict(port='Beachmere',  offset=1.26, epsg=28356, rank=2),
    'Noosa_2015_LGA':          dict(port='Noosa Head', offset=1.15, epsg=28356, rank=2),  # bad VLR, force GDA94/56
    'SunshineCoast_2008_LGA':  dict(port='Mooloolaba', offset=1.00, epsg=28356, rank=3),
    'MoretonBay_2009_LGA':     dict(port='Beachmere',  offset=1.26, epsg=28356, rank=3),
}

pat = re.compile(r'\d+\s+[\d-]+\s+[\d:]+\s+(QLD Government/Point Clouds/AHD/(\S+))')

manifest = []
for fn in sorted(glob.glob('D:/Claude Code/data/raw/_inventory/*.listing.txt')):
    outer = fn.replace('\\', '/').split('/')[-1].replace('.listing.txt', '')
    if outer not in {f"DATA_{n}.zip" for n in [2047212,2047214,2047216,2047218,2047220,2047224,2047226,2047229,2047239,2047251,2047261,2047263,2047270,2047277]}:
        continue
    with open(fn, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            m = pat.search(line)
            if not m: continue
            path, name = m.group(1), m.group(2)
            gm = re.match(r'(.+?)_(?:SW|sw)_(\d+)_(\d+)_1[Kk]', name)
            if not gm: continue
            survey = gm.group(1)
            if survey not in GROUP_META: continue
            e, n = int(gm.group(2)), int(gm.group(3))
            manifest.append(dict(outer=outer, path=path, name=name, survey=survey, e=e, n=n, **GROUP_META[survey]))

with open('D:/Claude Code/data/raw/_inventory/manifest.json', 'w') as f:
    json.dump(manifest, f)

print(f"total tiles in manifest: {len(manifest)}")
from collections import Counter
print(Counter(m['survey'] for m in manifest))
