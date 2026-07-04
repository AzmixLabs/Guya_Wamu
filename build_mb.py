import shapefile, json
from shapely.geometry import shape, mapping
from shapely.ops import transform

SRC = 'QSC_Extracted_Data_20260620_212645195589-27920/Moreton_Bay_marine_park_zoning_2008.shp'
ZT = {'Marine National Park Zone':'MNP','Conservation Park Zone':'CPZ',
      'Habitat Protection Zone':'HPZ','General Use Zone':'GUZ'}
SIMPLIFY = 0.0001   # ~11 m
NDP = 5              # ~1.1 m coord rounding

def rnd(geom):
    return transform(lambda *a: tuple(round(c, NDP) for c in a), geom)

r = shapefile.Reader(SRC, encoding='utf-8')
feats=[]
for sr in r.shapeRecords():
    d = sr.record.as_dict()
    zt = ZT[d['zone_type'].strip()]
    g = shape(sr.shape.__geo_interface__)
    if not g.is_valid:
        g = g.buffer(0)
    g = g.simplify(SIMPLIFY, preserve_topology=True)
    g = rnd(g)
    feats.append({
        'type':'Feature',
        'properties':{
            'name': d['zone_name'].strip(),
            'zt': zt,
            'zid': d['zone_id'].strip(),
            'notake': (zt=='MNP'),
            'plan':'Moreton Bay MP',
            'src':'https://parks.qld.gov.au/parks/moreton-bay/zoning/app-and-maps',
        },
        'geometry': mapping(g),
    })
fc={'type':'FeatureCollection','features':feats}
out='moreton_zones_2019.geojson'
json.dump(fc, open(out,'w'), separators=(',',':'))
import os
print('features', len(feats))
print('bytes', os.path.getsize(out))
# bbox
xs=[];ys=[]
def walk(c):
    if isinstance(c[0],(int,float)): xs.append(c[0]); ys.append(c[1])
    else:
        for x in c: walk(x)
for f in feats: walk(f['geometry']['coordinates'])
print('bbox lng', round(min(xs),4), round(max(xs),4),'lat', round(min(ys),4), round(max(ys),4))
