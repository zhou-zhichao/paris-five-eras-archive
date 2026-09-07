"""Inspect evaluated visibility at the old/new fabric handoff and endpoints."""
import json
import argparse
import sys
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--version',choices=['v47','v48'],default='v47')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene=bpy.context.scene
old=list(bpy.data.objects['Buildings_1700_State'].children_recursive)
clones=list(bpy.data.objects['1700_Spatial_Retirement_v47'].children_recursive)
new=[o for o in bpy.data.objects if o.name.startswith('Late_Block_') and o.type=='MESH']
rows=[]
for frame in [2100,2174,2175,2200,2250,2350,2450,2500,2800,2850,3000,3200,3350,3550]:
    scene.frame_set(frame)
    visible=lambda objects:[o for o in objects if o.type=='MESH' and not o.hide_render]
    row={'frame':frame,'original_old_meshes':len(visible(old)),'retirement_meshes':len(visible(clones)),'old_faces':sum(len(o.data.polygons) for o in visible(old)+visible(clones)),'new_blocks':len(visible(new))}
    if frame<2175:assert row['retirement_meshes']==0
    else:assert row['original_old_meshes']==0
    if frame>max(o['retirement_frame'] for o in clones):assert row['old_faces']==0
    expected=sum(frame>=o['growth_start_frame'] for o in new)
    assert row['new_blocks']==expected,(frame,row['new_blocks'],expected)
    rows.append(row)
assert next(r['old_faces'] for r in rows if r['frame']==2174)==next(r['old_faces'] for r in rows if r['frame']==2175)
(ROOT/f'reports/transition-visibility-{args.version}.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows))
