import json, csv

rows = json.load(open('D:/Claude Code/data/raw/_inventory/merged_cells.json'))
print(f"input merged cells: {len(rows):,}")

# port offset by latitude bucket (MSL-above-LAT(1992), MSQ 2024 Semidiurnal Tidal Planes,
# used as the AHD proxy per the same convention already used for Brisbane Bar in this repo)
def port_offset(lat):
    if lat > -26.533:
        return 1.15  # Noosa Head
    elif lat > -26.908:
        return 1.00  # Mooloolaba
    else:
        return 1.26  # Beachmere (Caboolture River) / Moreton Bay secondary

out = []
for lat, lon, z_ahd, rank in rows:
    off = port_offset(lat)
    depth = -(z_ahd) - off
    out.append((round(lat, 6), round(lon, 6), round(depth, 2)))

# duplicate (lat,lng) check
seen = {}
dupes = 0
for lat, lon, depth in out:
    k = (lat, lon)
    if k in seen:
        dupes += 1
    else:
        seen[k] = depth
print(f"exact lat/lng duplicate rows: {dupes:,} (0 expected — one value per 25m grid cell by construction)")

lats = [r[0] for r in out]
lons = [r[1] for r in out]
depths = [r[2] for r in out]
print(f"lat range: {min(lats)} to {max(lats)}")
print(f"lon range: {min(lons)} to {max(lons)}")
print(f"depth range: {min(depths)} to {max(depths)}  (negative = dries above LAT)")
n_dry = sum(1 for d in depths if d < 0)
n_wet = sum(1 for d in depths if d >= 0)
print(f"dries (negative, above LAT): {n_dry:,}   submerged-at-LAT (positive): {n_wet:,}")

out_path = 'D:/Claude Code/data/sunshine_coast_intertidal_ground_v1.csv'
with open(out_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['lat', 'lng', 'depth'])
    for lat, lon, depth in out:
        w.writerow([lat, lon, depth])

print(f"wrote {len(out):,} rows to {out_path}")
print(f"OVER 25000-POINT IMPORT CAP: {'YES' if len(out) > 25000 else 'no'} -- app will auto-thin on import via its existing grid-coarsening logic unless pre-thinned")
