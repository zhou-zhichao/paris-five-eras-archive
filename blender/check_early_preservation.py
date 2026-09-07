"""Compare evaluated visible early geometry before and after the late-era edit."""
import hashlib
import argparse
import json
import sys
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--version',default='v45',choices=['v45','v46','v47','v48'])
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
def fingerprint(path,frames=(750,1450,2100)):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    result={}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        records=[]
        for obj in bpy.data.objects:
            if obj.type!='MESH' or obj.hide_render:continue
            records.append((obj.name,len(obj.data.vertices),len(obj.data.polygons),[round(v,6) for row in obj.matrix_world for v in row],[m.name if m else None for m in obj.data.materials]))
        records.sort()
        result[frame]={'count':len(records),'sha256':hashlib.sha256(json.dumps(records).encode()).hexdigest()}
    return result
before=fingerprint(ROOT/'blender/paris_5_eras_roman_medieval_v44_temple_enclosure.blend')
candidate=f'paris_{args.version}_spatial_transition.blend' if args.version in ('v47','v48') else f'paris_{args.version}_late_blocks.blend'
after=fingerprint(ROOT/'blender'/candidate)
report={'before':before,'after':after,'matches':before==after,'scope':'Visible mesh names, topology counts, world transforms and assigned material names at frames 750, 1450, 2100. Not a pixel-equivalence test.'}
if args.version in ('v47','v48'):
    late_before=fingerprint(ROOT/'blender/paris_v46_late_blocks.blend',(3550,))
    late_after=fingerprint(ROOT/'blender'/candidate,(3550,))
    report['modern_matches_v46']=late_before==late_after
    assert report['modern_matches_v46']
(ROOT/f'reports/early-preservation-{args.version}.json').write_text(json.dumps(report,indent=2))
print('EARLY_PRESERVATION',report['matches'])
if not report['matches']:raise RuntimeError('Early scene changed')
