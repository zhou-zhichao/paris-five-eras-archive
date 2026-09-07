"""Build reviewable perimeter blocks from the existing OSM road network.

Roads are a modern spatial proxy, not a verified historical cadastral layer.
"""
import ast
import argparse
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/python_vendor"))
from shapely import affinity
from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import polygonize, unary_union

parser=argparse.ArgumentParser()
parser.add_argument('--version',choices=['v45','v46'],default='v45')
args=parser.parse_args()

tree = ast.parse((ROOT / "blender/build_scene.py").read_text())
constants = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {"CITY_POLYGONS", "MODERN_STATIONS"}:
        try:
            constants[node.targets[0].id] = ast.literal_eval(node.value)
        except ValueError:
            pass
city = [Polygon(p) for p in constants["CITY_POLYGONS"]]
data = json.loads((ROOT / "data/paris_geodata.json").read_text())
river = data["river"]
def river_width(x):
    return 1.62 + .16 * (.5 + .5 * math.sin((x+2)/8.5)) + 2.18*math.exp(-((x+2)/11.5)**4) + .68*math.exp(-((x-5.5)/6.8)**4)
exclusions = [LineString([a,b]).buffer(max(river_width(a[0]), river_width(b[0])) + .18) for a,b in zip(river,river[1:])]
exclusions += [Polygon(p).buffer(.1) for p in data["islands"].values()]
water_mask=None
if args.version=='v46':
    surfaces=json.loads((ROOT/'data/scene_environment.json').read_text())
    def surface_polygon(name):
        item=surfaces[name];vertices=item['vertices']
        return unary_union([Polygon([vertices[i][:2] for i in f]).buffer(0) for f in item['faces']])
    islands=unary_union([surface_polygon('Ile_de_la_Cite'),surface_polygon('Ile_Saint_Louis')])
    water_mask=surface_polygon('Seine').difference(islands)
    exclusions=[water_mask.buffer(.14),islands.buffer(.04)]
parks=[]
for x,y,rx,ry in [(-56,4,7.5,11),(44,-5,9.5,13),(-7,12,3.6,2.8),(9,-15,3.2,2.6),(-40.6,3.7,2.25,4.9)]:
    park=affinity.scale(Point(x,y).buffer(1),rx,ry)
    parks.append(park);exclusions.append(park)
protection = json.loads((ROOT / "previews/v44-modern.json").read_text())
for landmark in protection["protected_landmarks"]:
    ignored={"Modern_Stations"}
    if args.version=='v46':ignored.add("Landmark_Medieval_Cite_Wall")
    if landmark["name"] not in ignored:
        exclusions.append(box(*landmark["bounds"]).buffer(.15))
for line in [[(6.5,24),(7.4,31),(10.5,42)],[(-18,18),(-26,26),(-39,35)],[(14,-4),(23,-13),(39,-29)],[(-10,-16),(-18,-27),(-27,-42)]]:
    exclusions.append(LineString(line).buffer(.6))
    if args.version=='v45':exclusions.append(Point(line[0]).buffer(2.8))
    else:
        x,y=line[0]
        angle=math.degrees(math.atan2(line[1][1]-y,line[1][0]-x))-90
        exclusions.append(affinity.rotate(box(x-2,y-1.25,x+2,y+1.25),angle,origin=(x,y)))
protected = unary_union(exclusions)
roads = []
road_masks = []
for road in data["roads"]:
    if road["bridge"] or road["class"] not in {"primary","secondary","tertiary","residential","unclassified"}:
        continue
    line = LineString(road["points"]).intersection(city[4])
    if line.is_empty:
        continue
    roads.append(line)
    road_masks.append(line.buffer(max(.045,road["width"]*.55),join_style="mitre"))
road_mask = unary_union(road_masks)
if args.version=='v46':
    clipped_roads=road_mask.difference(unary_union([water_mask.buffer(.025),*parks]))
    quay=water_mask.buffer(.13).difference(water_mask).intersection(city[4])
    # Spatial chunks retain a readable outward reveal without one giant road pop.
    patches=[]
    for ix in range(-60,61,4):
        for iy in range(-48,49,4):
            cell=box(ix,iy,ix+4,iy+4)
            for kind,geom in [('road',clipped_roads),('quay',quay)]:
                part=geom.intersection(cell)
                if part.is_empty:continue
                triangles=[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(part).geoms]
                if triangles:patches.append({'kind':kind,'center':[ix+2,iy+2],'triangles':triangles})
    (ROOT/'data/late_surfaces_v46.json').write_text(json.dumps({'patches':patches,'water_area':water_mask.area},separators=(',',':')))
exclusion = unary_union([protected,road_mask])
raw_blocks = list(polygonize(unary_union(roads+[city[4].boundary])))
blocks = []
for block in raw_blocks:
    if not city[4].covers(block.representative_point()): continue
    if block.area <= 8:
        blocks.append(block)
        continue
    # Missing minor OSM streets leave enormous cells. Subdivide those cells
    # along their dominant street axis, retaining the observed outer boundary.
    rectangle=list(block.minimum_rotated_rectangle.exterior.coords)
    a,b=rectangle[:2]
    angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
    local=affinity.rotate(block,-angle,origin=(0,0))
    x0,y0,x1,y1=local.bounds
    pitch=1.65
    for i in range(math.ceil((x1-x0)/pitch)):
        for j in range(math.ceil((y1-y0)/pitch)):
            cell=box(x0+i*pitch+.035,y0+j*pitch+.035,x0+(i+1)*pitch-.035,y0+(j+1)*pitch-.035).intersection(local)
            if cell.geom_type=='Polygon' and cell.area>.08:
                blocks.append(affinity.rotate(cell,angle,origin=(0,0)))
blocks.sort(key=lambda p:(round(p.centroid.y,4),round(p.centroid.x,4)))
def parts(g):
    if g.is_empty: return []
    if g.geom_type == "Polygon": return [g]
    return [p for p in g.geoms if p.geom_type == "Polygon"]
result=[]
rng=random.Random(4501)
for block in blocks:
    if not .08 < block.area < 45 or not city[4].covers(block.representative_point()):
        continue
    for plot in parts(block.difference(exclusion)):
        if plot.area < .045: continue
        # Closed street walls with interior courtyards; large blocks retain gardens.
        # Fit the court to each plot instead of leaving giant empty interiors.
        target=plot.area*rng.uniform(.16,.26)
        low,high=0,math.sqrt(plot.area)
        for _ in range(18):
            mid=(low+high)/2
            if plot.buffer(-mid,join_style="mitre").area>target: low=mid
            else: high=mid
        depth=high
        inner = plot.buffer(-depth,join_style="mitre")
        fabric = plot.difference(inner).simplify(.006,preserve_topology=True)
        for footprint in parts(fabric):
            if footprint.area < .025: continue
            center = footprint.representative_point()
            phase = 3 if city[3].covers(center) else 4
            triangles = [list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(footprint).geoms]
            rectangle=list(footprint.minimum_rotated_rectangle.exterior.coords)
            a,b=rectangle[:2]
            angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
            local=affinity.rotate(footprint,-angle,origin=(0,0))
            x0,y0,x1,y1=local.bounds
            parcels=[]
            for ix in range(math.ceil((x1-x0)/.34)):
                for iy in range(math.ceil((y1-y0)/.42)):
                    cell=box(x0+ix*.34+.003,y0+iy*.42+.003,x0+(ix+1)*.34-.003,y0+(iy+1)*.42-.003)
                    for piece in parts(local.intersection(cell)):
                        if piece.area<.003:continue
                        piece=affinity.rotate(piece,angle,origin=(0,0))
                        peak=piece.representative_point()
                        parcels.append({'rings':[list(piece.exterior.coords)]+[list(r.coords) for r in piece.interiors],'height':rng.uniform(.20,.34),'peak':[peak.x,peak.y],'convex':not piece.interiors and piece.convex_hull.area-piece.area<.0001,'triangles':[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(piece).geoms],'palette':rng.randrange(5)})
            result.append({"phase":phase,"center":[center.x,center.y],"height":rng.uniform(.24,.38),"palette":rng.randrange(5),"polygon":mapping(footprint),"roof_triangles":triangles,"parcels":parcels})
out=ROOT/f'data/late_blocks_{args.version}.json'
out.write_text(json.dumps({"source":"Existing modern OSM road proxy; historical timing remains approximate", "blocks":result},separators=(',',':')))
report={"blocks":len(result),"phase_3":sum(b['phase']==3 for b in result),"phase_4":sum(b['phase']==4 for b in result),"footprint_area":sum(Polygon(b['polygon']['coordinates'][0],b['polygon']['coordinates'][1:]).area for b in result)}
(ROOT/f'reports/late_blocks_{args.version}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
