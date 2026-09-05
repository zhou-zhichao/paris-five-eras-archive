"""Generate new street parcels and architecture from the supplied film's framing.

All coordinates below are hand measurements of reference frames, not old project data.
One world unit represents approximately ten metres. Randomness is seeded and frozen.
"""
from pathlib import Path
import json
import math
import random
import numpy as np
from scipy.interpolate import splprep, splev
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union, polygonize, split
from shapely.prepared import prep
from shapely.strtree import STRtree
from shapely import affinity

ROOT = Path(__file__).resolve().parents[1]
R = random.Random(20260905)
OUT = ROOT / 'data'
OUT.mkdir(exist_ok=True)

def trace(points):
    return [((x - 1140) * .62, (550 - y) * .66) for x, y in points]

def smooth(points, n=250, closed=False):
    a = np.array(points).T
    tck, _ = splprep(a, s=0, k=min(3, len(points)-1), per=closed)
    return np.array(splev(np.linspace(0, 1, n), tck)).T.tolist()

def polygons(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape]
    return [p for p in getattr(shape, 'geoms', []) if p.geom_type == 'Polygon']

river_pts = trace([(-260,1900),(100,1430),(265,1070),(370,790),(470,652),(620,580),(805,530),(962,535),(1065,542),(1160,559),(1280,590),(1450,658),(1650,751),(1880,817),(2240,851),(2850,1000)])
river = LineString(smooth(river_pts, 700))
water_parts = []
for i in range(360):
    a = river.interpolate(i/360, normalized=True)
    b = river.interpolate((i+1)/360, normalized=True)
    width = 11.5 + 14.5 * math.exp(-((a.x-5)/113)**4)
    water_parts.append(LineString([a,b]).buffer(width, quad_segs=4))
water_parts.append(LineString(smooth(trace([(-500,1800),(-300,1280),(-180,980),(-250,650),(-185,365),(10,193),(219,53),(369,-100),(540,-265),(720,-600),(850,-1000)]),340)).buffer(10,quad_segs=5))
water_outer = unary_union(water_parts).buffer(1).buffer(-1).simplify(.35)
islands = [Polygon(smooth(trace(p), 70, True)).buffer(0) for p in [
    [(1046,534),(1072,530),(1103,538),(1157,551),(1178,559),(1176,570),(1150,572),(1116,560),(1075,550),(1046,534)],
    [(1192,551),(1213,549),(1254,560),(1268,570),(1255,576),(1213,568),(1192,551)],
    [(1283,569),(1294,568),(1321,582),(1321,591),(1304,586),(1283,569)],
    [(1009,532),(1022,530),(1034,535),(1020,540),(1009,532)]
]]
islands=[affinity.scale(p,1.08,1.85,origin='centroid') if i==0 else affinity.scale(p,1,1.3,origin='centroid') for i,p in enumerate(islands)]
island_union = unary_union(islands)
water = water_outer.difference(island_union)
domain = box(-1000,-790,1000,950)
land = domain.difference(water)
water_guard = prep(water.buffer(2.2))

# Parks, civic courts and important silhouettes, measured in the last city frame.
park_traces = [
    [(790,490),(922,516),(918,544),(780,526)],
    [(485,654),(587,690),(565,787),(444,746)],
    [(658,677),(711,698),(691,763),(636,735)],
    [(983,618),(1042,635),(1035,691),(971,669)],
    [(1238,240),(1336,222),(1370,313),(1283,341)],
    [(1615,349),(1733,354),(1807,394),(1748,450),(1649,419)],
    [(566,415),(648,403),(669,459),(597,476)],
    [(455,288),(509,278),(530,307),(478,328)],
    [(332,716),(397,761),(350,954),(240,973),(183,889),(220,774)],
    [(1480,812),(1580,840),(1571,890),(1505,879)],
]
parks = [Polygon(trace(p)) for p in park_traces]
landmark_specs = [
    {'name':'Notre_Dame','xy':trace([(1158,563)])[0],'kind':'notre_dame','size':13,'born':49},
    {'name':'Eiffel_Tower','xy':trace([(542,683)])[0],'kind':'eiffel','size':31,'born':137.0},
    {'name':'Louvre','xy':trace([(983,481)])[0],'kind':'palace','size':32,'born':53},
    {'name':'Les_Invalides','xy':trace([(696,694)])[0],'kind':'dome','size':18,'born':80},
    {'name':'Pantheon','xy':trace([(1105,689)])[0],'kind':'dome','size':13,'born':98},
    {'name':'Arc_de_Triomphe','xy':trace([(478,429)])[0],'kind':'arch','size':8,'born':119},
    {'name':'Sacre_Coeur','xy':trace([(1076,216)])[0],'kind':'basilica','size':17,'born':143},
    {'name':'Opera','xy':trace([(970,387)])[0],'kind':'palace','size':12,'born':128},
    {'name':'Saint_Germain','xy':trace([(990,602)])[0],'kind':'church','size':9,'born':31},
    {'name':'Tour_du_Temple','xy':trace([(1290,435)])[0],'kind':'keep','size':10,'born':49},
    {'name':'Roman_Arena','xy':[62,-76],'kind':'arena','size':12,'born':13},
    {'name':'Roman_Forum','xy':[24,-91],'kind':'forum','size':12,'born':12},
]
reserves = [Point(*p['xy']).buffer(p['size']*.72) for p in landmark_specs]
reserved = unary_union(parks + reserves)

# Major road geometry follows the source's recognizable radial intersections.
routes_pixels = [
    [(175,1020),(372,743),(474,660),(639,583),(813,550),(1030,563),(1140,595),(1310,641),(1520,734),(1785,841),(2140,897)],
    [(105,885),(478,429),(867,491),(1048,517),(1170,509),(1350,594),(1580,692),(1980,820)],
    [(478,429),(380,235),(287,42),(-40,-290)],
    [(478,429),(657,167),(740,-150)],
    [(478,429),(765,323),(970,387),(1120,437),(1320,462),(1640,477),(2170,514)],
    [(478,429),(499,643),(522,856),(503,1195)],
    [(478,429),(199,480),(-100,610)],
    [(478,429),(780,159),(900,-200)],
    [(970,387),(1016,169),(1006,-170)],
    [(970,387),(1101,291),(1277,108),(1520,-125)],
    [(970,387),(910,533),(854,708),(738,919),(650,1280)],
    [(1137,576),(1106,430),(1130,304),(1184,92),(1320,-250)],
    [(1137,576),(1120,660),(1130,770),(1120,880),(1200,1240)],
    [(1100,740),(990,780),(820,897),(620,1070)],
    [(1130,770),(1350,773),(1570,789),(1860,803)],
    [(1300,557),(1360,415),(1420,260),(1590,50),(1830,-160)],
    [(1320,462),(1180,465),(1050,480),(955,494)],
    [(1320,462),(1550,446),(1780,360),(2060,267)],
    [(1350,594),(1480,520),(1670,410),(1890,90)],
    [(1350,594),(1540,600),(1780,580),(2200,540)],
    [(1350,594),(1420,761),(1480,921),(1540,1250)],
    [(910,533),(976,688),(1100,740),(1300,832),(1560,970)],
    [(854,708),(670,818),(442,873),(158,920)],
    [(1120,437),(1220,363),(1490,290),(1740,250)],
    [(1106,430),(924,344),(696,297),(490,266)],
    [(230,763),(699,987),(1140,1080),(1450,1058),(1710,914),(1900,704),(1900,505),(1840,270),(1600,70),(1240,-15),(935,-45),(690,67),(479,236),(310,455),(230,763)],
]
major = [LineString(trace(p)) for p in routes_pixels]
# Preserve the river's continuous quay lines in the network.
for p in polygons(water_outer.buffer(5)):
    major.append(LineString(p.exterior.coords))
lines = [LineString(domain.exterior.coords)] + major
sectors = list(polygonize(unary_union(lines)))
sectors = [p.intersection(domain) for p in sectors if p.area > 12]
if not sectors:
    raise RuntimeError('Primary street network did not close')

def divide(p, depth=0):
    """Bend local streets slightly, preserving district and arterial orientations."""
    if p.area < R.uniform(350,650) or depth > 18:
        return [p]
    rect = list(p.minimum_rotated_rectangle.exterior.coords)
    edges = [(math.dist(rect[i],rect[i+1]), rect[i], rect[i+1]) for i in range(4)]
    _, a, b = max(edges)
    angle = math.atan2(b[1]-a[1],b[0]-a[0])
    angle += R.uniform(-.11,.11)
    ux,uy = math.cos(angle),math.sin(angle)
    nx,ny = -uy,ux
    c=p.centroid
    span=max(e[0] for e in edges)
    off=R.uniform(-.16,.16)*span
    cx,cy=c.x+ux*off,c.y+uy*off
    bend=R.uniform(-1.6,1.6)
    cutter=LineString([(cx-nx*3000,cy-ny*3000),(cx+ux*bend,cy+uy*bend),(cx+nx*3000,cy+ny*3000)])
    pieces=polygons(split(p,cutter))
    if len(pieces)<2 or min(q.area for q in pieces)<20:
        return [p]
    result=[]
    for q in pieces:
        result.extend(divide(q,depth+1))
    return result

blocks=[]
for sector in sectors:
    for p in polygons(sector):
        blocks.extend(divide(p))
print('Raw blocks',len(blocks),flush=True)

def growth(x,y):
    r=math.hypot((x+10)/1.04,y/1.00)
    knots=[(0,40),(50,45),(100,49),(160,58),(215,68),(270,88),(325,115),(415,135),(530,148),(670,159),(920,165)]
    t=float(np.interp(r,*zip(*knots)))
    # Right bank grows sooner; radial villages precede their surrounding infill.
    t+=3.5 if y<-35 else -2
    return t

def edge_lots(p, spacing=(1.8,2.8), depth_range=(2.0,3.2)):
    p=affinity.scale(p,1,1)
    coords=list(p.exterior.coords)
    ccw=p.exterior.is_ccw
    used=[]
    for a,b in zip(coords,coords[1:]):
        length=math.dist(a,b)
        if length<1.2:
            continue
        ux,uy=(b[0]-a[0])/length,(b[1]-a[1])/length
        nx,ny=(-uy,ux) if ccw else (uy,-ux)
        n=max(1,round(length/R.uniform(*spacing)))
        step=length/n
        for j in range(n):
            w=step*R.uniform(.94,.995)
            d=R.uniform(*depth_range)
            t=(j+.5)*step
            x,y=a[0]+ux*t+nx*(d*.5+.06),a[1]+uy*t+ny*(d*.5+.06)
            footprint=Polygon([(x+sx*ux*w/2+sy*nx*d/2,y+sx*uy*w/2+sy*ny*d/2) for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]])
            if footprint.intersection(p).area<footprint.area*.90:
                continue
            if any(footprint.intersection(q).area>.09 for q in used[-60:]):
                continue
            used.append(footprint)
            yield x,y,w,d,math.atan2(uy,ux)

buildings=[]
road_records=[]
block_records=[]
roman_zone=box(-34,-126,83,-28).difference(reserved)
exclusion=unary_union([water_outer.buffer(3),reserved,roman_zone])
templates={'roman':0,'medieval':12,'stone':24,'mansard':36,'suburban':48,'modern':60}

def add_building(kind,x,y,w,d,h,angle,born,gone=300):
    buildings.append([round(x,3),round(y,3),round(w,3),round(d,3),round(h,3),round(angle,5),round(born,3),round(gone,3),templates[kind]+R.randrange(12)])

for bi,raw in enumerate(blocks):
    cx,cy=raw.centroid.coords[0]
    if (cx/960)**2+(cy/790)**2>1.3:
        continue
    t=growth(cx,cy)+R.uniform(-2.8,2.8)
    near=min(m.distance(Point(cx,cy)) for m in major[:25])
    if near<8 and math.hypot(cx,cy)>180:
        t-=R.uniform(9,27)
    street=raw.exterior
    road_records.append({'points':list(street.coords),'width':.60,'born':max(7,t-11),'kind':'lane'})
    clipped=raw.buffer(-.58,join_style='mitre').difference(exclusion)
    for p in polygons(clipped):
        if p.area<7:
            continue
        block_records.append({'polygon':list(p.exterior.coords),'born':t-.5})
        lots=list(edge_lots(p,depth_range=(2.6,3.5)))
        if p.area>210:
            for inner in polygons(p.buffer(-5.2,join_style='mitre')):
                if inner.area>14:lots.extend(edge_lots(inner,(1.7,2.5),(1.6,2.3)))
        for x,y,w,d,a in lots:
            tb=t+R.uniform(-1.1,1.6)
            h=R.uniform(1.65,2.8)
            if -65<x<15 and 25<y<85:
                add_building('roman',x,y,w,d,R.uniform(.8,1.3),a,R.uniform(12,23),42)
                tb=42+R.uniform(0,3)
            if tb<64:
                replaced=max(tb+5, R.uniform(63,77)+math.hypot(x,y)*.008)
                add_building('medieval',x,y,w,d,h*.84,a,tb,replaced)
                tb=replaced
            if tb<123:
                rebuilt=R.uniform(123,138) if R.random()<.52 else 300
                add_building('stone',x,y,w,d,h,a,tb,rebuilt)
                if rebuilt<300:
                    add_building('mansard',x,y,w,d,h*R.uniform(1.08,1.22),a,rebuilt)
            else:
                k='mansard' if math.hypot(x,y)<610 else 'suburban'
                add_building(k,x,y,w,d,h*(.68 if k=='suburban' else 1.12),a,tb)

# Roman grid uses its own small courtyard houses and a prominent axial street.
for ix in range(10):
    for iy in range(7):
        x=-33+ix*11.5
        y=-123+iy*13.5
        p=box(x+.8,y+.8,x+10.5,y+12.5).difference(reserved).difference(water_outer.buffer(3))
        start=9+iy*.8+abs(ix-4)*1.4+R.uniform(0,2)
        road_records.append({'points':[(x,y),(x+11.5,y),(x+11.5,y+13.5)],'width':1.0,'born':7+ix*.16,'kind':'roman'})
        for q in polygons(p):
            roman_lots=list(edge_lots(q,(1.4,2.3),(1.9,2.5)))
            for inner in polygons(q.buffer(-3.5)):
                if inner.area>7:roman_lots.extend(edge_lots(inner,(1.3,1.8),(1.3,1.7)))
            for lx,ly,w,d,a in roman_lots:
                gone=R.uniform(26,39) if R.random()<.72 else 47
                add_building('roman',lx,ly,w,d,R.uniform(.85,1.38),a,start+R.uniform(0,3),gone)
                born=R.uniform(44,51)
                add_building('medieval',lx,ly,w*.98,d,R.uniform(1,1.7),a,born,69)
                add_building('stone',lx,ly,w,d,R.uniform(1.5,2),a,69+R.uniform(0,.5),126)
                add_building('mansard',lx,ly,w,d,R.uniform(1.9,2.5),a,126+R.uniform(0,.5))

# Dense island plots with a continuous central lane and shoreline orientation.
for ii,isle in enumerate(islands[:2]):
    bounds=isle.bounds
    island_blocks=[]
    for x in np.arange(bounds[0]-5,bounds[2]+10,7.8):
        for y in np.arange(bounds[1]-2,bounds[3]+5,7.5):
            island_blocks.extend(polygons(box(x+.45,y+.45,x+7.35,y+7.05).intersection(isle.buffer(-1.2)).difference(reserved)))
    for p in island_blocks:
        for x,y,w,d,a in edge_lots(p,(1.2,1.75),(1.25,1.9)):
            b=R.uniform(7,17) if ii==0 else R.uniform(70,88)
            if ii==0:
                add_building('roman',x,y,w,d,.75,a,b,42)
                add_building('medieval',x,y,w,d,R.uniform(1.2,1.9),a,R.uniform(42,46),68)
            add_building('stone',x,y,w,d,R.uniform(1.5,2.2),a,68 if ii==0 else b)

for i,m in enumerate(major):
    born=7 if i in [10,11,12,13] else (124 if i in [1,7,9,18,23] else 40)
    if i==25:
        born=149
    road_records.append({'points':list(m.coords),'width':2.2 if i<25 else 1.2,'born':born,'kind':'artery' if i<25 else 'ring'})

# Natural forest, disappearing under expanding development and preserved in parks.
park_prep=prep(unary_union(parks))
reserved_prep=prep(reserved)
land_prep=prep(land)
trees=[]
for _ in range(420000):
    x,y=R.uniform(-1080,1080),R.uniform(-850,990)
    p=Point(x,y)
    if not land_prep.contains(p) or water_guard.contains(p):
        continue
    noise=(math.sin(x*.022+math.sin(y*.012)*3)+math.sin(y*.026-x*.009)+math.cos(x*.043+y*.036)) / 3
    ispark=park_prep.contains(p)
    if reserved_prep.contains(p) and not ispark:
        continue
    if R.random()>.045+.90*max(0,noise+.08)+(.4 if ispark else 0):
        continue
    near=min(m.distance(p) for m in major[:25])
    if near<1.9:
        continue
    gone=growth(x,y)-1+R.uniform(-2,2)
    if ispark or math.hypot(x/1.1,y)>750:
        gone=300
    if roman_zone.contains(p):
        gone=8+R.uniform(0,9)
    if -65<x<15 and 25<y<85:
        gone=12+R.uniform(0,8)
    if island_union.contains(p):
        gone=8+R.uniform(0,6)
    trees.append([x,y,R.uniform(1.7,3.2),R.uniform(2.7,4.9),gone,R.randrange(8)])

# Formal tree rows along broad avenues and gardens remain in the modern city.
for i,m in enumerate(major[:25]):
    for dist in np.arange(0,m.length,3.0):
        c=m.interpolate(dist)
        ahead=m.interpolate(min(m.length,dist+.4))
        dx,dy=ahead.x-c.x,ahead.y-c.y
        norm=math.hypot(dx,dy) or 1
        for side in [-1,1]:
            x,y=c.x-side*dy/norm*1.9,c.y+side*dx/norm*1.9
            if water_guard.contains(Point(x,y)):
                continue
            trees.append([x,y,1.6,R.uniform(2.6,3.5),300,R.randrange(4),max(70,growth(x,y)-4)])

for _ in range(65):
    x=R.uniform(islands[0].bounds[0]+3,islands[0].bounds[2]-3)
    y=R.uniform(islands[0].bounds[1]+1,islands[0].bounds[3]-1)
    if islands[0].buffer(-2).contains(Point(x,y)):
        buildings.append([x,y,R.uniform(1.4,2),R.uniform(1.4,2),R.uniform(.9,1.3),R.uniform(0,6.28),R.uniform(1.6,5.5),10,72+R.randrange(6)])
for p in polygons(islands[0].buffer(-2.5)):
    road_records.append({'points':list(p.exterior.coords),'width':.5,'born':2,'kind':'island_path'})

clipped_roads=[]
for record in road_records:
    clipped=LineString(record['points']).difference(water.buffer(.7))
    segments=[clipped] if clipped.geom_type=='LineString' else list(getattr(clipped,'geoms',[]))
    for segment in segments:
        if segment.geom_type=='LineString' and segment.length>.5:
            clipped_roads.append({**record,'points':list(segment.coords)})
road_records=clipped_roads

rail_specs=[
    ('Gare_du_Nord',[(1138,302),(1155,162),(1140,-20),(1190,-210)],121),
    ('Gare_de_l_Est',[(1225,329),(1258,238),(1364,90),(1460,-150)],123),
    ('Gare_Saint_Lazare',[(857,359),(771,267),(686,80),(612,-170)],119),
    ('Gare_de_Lyon',[(1412,650),(1589,752),(1850,862),(2110,971)],123),
    ('Gare_Montparnasse',[(883,756),(814,906),(803,1107),(740,1320)],124),
    ('Gare_Austerlitz',[(1327,666),(1395,794),(1515,1000),(1680,1340)],122),
]
rails=[]
for name,points,born in rail_specs:
    pts=smooth(trace(points),70)
    route=LineString(pts)
    rails.append({'name':name,'points':pts,'born':born})
    dx,dy=pts[2][0]-pts[0][0],pts[2][1]-pts[0][1]
    landmark_specs.append({'name':name,'xy':pts[0],'kind':'rail_station','size':12,'born':born,'rotation':math.atan2(dy,dx)-math.pi/2})
    guard=prep(route.buffer(4.2))
    for b in buildings:
        if b[7]>born and guard.contains(Point(b[0],b[1])):b[7]=born
    for tr in trees:
        if tr[4]>born and guard.contains(Point(tr[0],tr[1])):tr[4]=born

data={'source':'reference/source.mp4','seed':20260905,
      'water':[{'outer':list(p.exterior.coords),'holes':[list(r.coords) for r in p.interiors]} for p in polygons(water)],
      'water_outer':[list(p.exterior.coords) for p in polygons(water_outer)],
      'islands':[list(p.exterior.coords) for p in islands],
      'parks':[list(p.exterior.coords) for p in parks],
      'buildings':buildings,'trees':trees,'roads':road_records,'blocks':block_records,
      'landmarks':landmark_specs,'rails':rails}
(OUT/'city.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
summary={'buildings_including_replacements':len(buildings),'trees':len(trees),'blocks':len(block_records),'roads':len(road_records),
         'visible_by_time':{str(t):sum(b[6]<=t<b[7] for b in buildings) for t in [6,18,24,36,48,60,80,110,127,144,165]},
         'bounds':[-1000,-790,1000,950]}
(OUT/'plan-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
