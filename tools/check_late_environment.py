"""Check late development and paved surfaces against exported scene water."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/python_vendor'))
from shapely.geometry import Polygon,shape,Point
from shapely import affinity
from shapely.ops import unary_union

surfaces=json.loads((ROOT/'data/scene_environment.json').read_text())
def footprint(name):
    item=surfaces[name];v=item['vertices']
    return unary_union([Polygon([v[i][:2] for i in f]).buffer(0) for f in item['faces']])
water=footprint('Seine').difference(unary_union([footprint('Ile_de_la_Cite'),footprint('Ile_Saint_Louis')]))
parks=unary_union([affinity.scale(Point(x,y).buffer(1),rx,ry) for x,y,rx,ry in [(-56,4,7.5,11),(44,-5,9.5,13),(-7,12,3.6,2.8),(9,-15,3.2,2.6),(-40.6,3.7,2.25,4.9)]])
report={}
for version in ['v45','v46']:
    data=json.loads((ROOT/f'data/late_blocks_{version}.json').read_text())
    polygons=[shape(b['polygon']) for b in data['blocks']]
    report[version]={'blocks':len(polygons),'invalid':sum(not p.is_valid for p in polygons),'water_overlap':sum(p.intersection(water).area for p in polygons)}
patches=json.loads((ROOT/'data/late_surfaces_v46.json').read_text())['patches']
roads=[Polygon(t) for p in patches if p['kind']=='road' for t in p['triangles']]
report['new_roads']={'water_overlap':sum(p.intersection(water).area for p in roads),'park_overlap':sum(p.intersection(parks).area for p in roads),'triangles':len(roads)}
report['scope']='Geometric plan overlap against the current exported Seine surface and configured park masks. Excludes bridge objects, legacy meshes, historical validity and animation appearance.'
(ROOT/'reports/environment-check-v46.json').write_text(json.dumps(report,indent=2))
assert report['v46']['invalid']==0
assert report['v46']['water_overlap']<1e-7
assert report['new_roads']['water_overlap']<1e-7
assert report['new_roads']['park_overlap']<1e-7
print(json.dumps(report))
