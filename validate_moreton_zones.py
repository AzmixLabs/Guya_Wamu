#!/usr/bin/env python3
"""Validate moreton_zones_2019.geojson before embedding into Guya.
Stdlib only. Exit 0 = pass, 1 = fail. Usage:
    python3 validate_moreton_zones.py moreton_zones_2019.geojson
Source geometry: Marine Parks (Moreton Bay) Zoning Plan 2008 data (QSpatial),
geometrically unchanged by the 2019 administrative remake -> labelled as the
current 2019 plan. Whole-park extent (Caloundra/Pumicestone -> Jumpinpin).
"""
import sys, json

ZT = {"MNP", "CPZ", "HPZ", "GUZ"}
# Whole Moreton Bay Marine Park, generous WGS84 box (catches GDA94-metre coords).
LNG_MIN, LNG_MAX = 152.9, 153.7
LAT_MIN, LAT_MAX = -28.05, -26.7
# Home-water sanity targets: (zid) -> (expected_zt, expected_notake)
SANITY = {
    "MNP11": ("MNP", True),   # Hays Inlet      (no-take)
    "MNP09": ("MNP", True),   # Deception Bay   (no-take)
    "HPZ06": ("HPZ", False),  # Redcliffe       (not no-take)
    "HPZ08": ("HPZ", False),  # Pine River      (not no-take)
}
PROPS = ("name", "zt", "zid", "notake", "plan", "src")

def fail(msg):
    print("FAIL:", msg); sys.exit(1)

def iter_coords(geom):
    t = geom.get("type"); c = geom.get("coordinates")
    if t == "Polygon":
        for ring in c:
            for pt in ring: yield pt
    elif t == "MultiPolygon":
        for poly in c:
            for ring in poly:
                for pt in ring: yield pt
    else:
        fail(f"geometry type must be Polygon/MultiPolygon, got {t}")

def main():
    if len(sys.argv) != 2: fail("usage: validate_moreton_zones.py <file.geojson>")
    try:
        fc = json.load(open(sys.argv[1], encoding="utf-8"))
    except Exception as e:
        fail(f"cannot read/parse: {e}")
    if fc.get("type") != "FeatureCollection": fail("top-level type != FeatureCollection")
    feats = fc.get("features") or []
    if not feats: fail("no features")

    seen = {}
    for i, f in enumerate(feats):
        if f.get("type") != "Feature": fail(f"feature {i}: type != Feature")
        p = f.get("properties") or {}
        for k in PROPS:
            if k not in p: fail(f"feature {i}: missing property '{k}'")
        if not isinstance(p["name"], str) or not p["name"]: fail(f"feature {i}: bad name")
        if p["zt"] not in ZT: fail(f"feature {i}: zt '{p['zt']}' not in {sorted(ZT)}")
        if not isinstance(p["zid"], str) or not p["zid"]: fail(f"feature {i}: bad zid")
        if not isinstance(p["notake"], bool): fail(f"feature {i}: notake not bool")
        if p["notake"] != (p["zt"] == "MNP"):
            fail(f"feature {i} ({p['zid']}): notake={p['notake']} but zt={p['zt']}")
        g = f.get("geometry") or {}
        n = 0
        for lng, lat in iter_coords(g):
            n += 1
            if not (LNG_MIN <= lng <= LNG_MAX and LAT_MIN <= lat <= LAT_MAX):
                fail(f"feature {i} ({p['zid']}): coord out of extent ({lng},{lat}) "
                     f"- not WGS84/Moreton? (GDA94-metres would land here)")
        if n == 0: fail(f"feature {i} ({p['zid']}): empty geometry")
        seen[p["zid"]] = (p["zt"], p["notake"])

    for zid, exp in SANITY.items():
        if zid not in seen: fail(f"sanity target {zid} missing")
        if seen[zid] != exp:
            fail(f"sanity {zid}: expected {exp}, got {seen[zid]}")

    from collections import Counter
    by = Counter(v[0] for v in seen.values())
    print(f"PASS: {len(feats)} features | {dict(by)} | "
          f"notake={sum(1 for v in seen.values() if v[1])} | "
          f"sanity targets ok ({', '.join(SANITY)})")
    sys.exit(0)

if __name__ == "__main__":
    main()
