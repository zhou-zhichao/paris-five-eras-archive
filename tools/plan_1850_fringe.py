"""Reference-driven settlement timing; modern OSM is a spatial proxy only."""
import json
import math
import random
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/python_vendor'))
from shapely.geometry import LineString,Point
from shapely.ops import unary_union

geo=json.loads((ROOT/'data/paris_geodata.json').read_text())
roads=unary_union([LineString(r['points']) for r in geo['roads'] if r['class']=='primary' and not r['bridge']])
blocks=json.loads((ROOT/'data/late_blocks_v46.json').read_text())['blocks']
rows=[]
for i,b in enumerate(blocks):
    if b['phase']!=3:continue
    x,y=b['center'];radius=math.hypot(x,y)
    distance=roads.distance(Point(x,y))
    density=max(.04,min(1,(29-radius)/12))
    corridor=.48*math.exp(-distance/1.1)
    probability=min(.98,density+corridor)
    if radius<19:keep=True
    else:
        cell=(math.floor(x/2.6),math.floor(y/2.6))
        sample=random.Random(4800+cell[0]*9176+cell[1]*13457).random()
        keep=sample<probability
    if keep:start=2175+int(min(1,radius/52)*540)
    else:start=2850+int(min(1,max(0,(radius-19)/35))*430)
    rows.append({'block':i,'start':start,'deferred':not keep})
(ROOT/'data/fringe_timing_v48.json').write_text(json.dumps(rows,separators=(',',':')))
print(json.dumps({'kept_1850':sum(not r['deferred'] for r in rows),'deferred_to_modern':sum(r['deferred'] for r in rows)}))
