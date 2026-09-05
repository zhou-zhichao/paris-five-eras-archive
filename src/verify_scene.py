"""Check native timeline counters, packed assets, and the render contract."""
from pathlib import Path
import json
import math
import bpy

ROOT=Path(__file__).resolve().parents[1]
s=bpy.context.scene
assert s.render.resolution_x==2560 and s.render.resolution_y==1440
assert s.render.fps==30 and s.frame_start==1 and s.frame_end==5400
assert s.camera.data.clip_start>=10
assert len(bpy.data.collections['Original architecture library - 72 variants'].objects)==78
assert s['building_records']>100000
assert s['tree_records']>50000
assert all(im.packed_file or im.source in ['GENERATED','VIEWER'] for im in bpy.data.images)
checks=[]
for t,expected in [(0,-300),(1,-269),(6,-115),(12,71),(24,428),(54,1316),(80,1674),(127,1857),(165,2024),(168,2025)]:
    s.frame_set(round(t*30)+1)
    group=bpy.data.node_groups['Reference year curve and decimal digits']
    value=next(n.outputs[0].default_value for n in group.nodes if n.bl_idname=='ShaderNodeValue')
    assert round(value)==expected,(t,value,expected)
    visible=[ob.name for ob in s.objects if ob.name.endswith('ERA') and not ob.hide_render]
    assert len(visible)==1,(t,visible)
    assert all(math.isfinite(v) for v in s.camera.location)
    checks.append({'seconds':t,'year':expected,'era':visible[0]})
s.frame_set(5251)
assert bpy.data.objects['Animated year counter'].hide_render
assert not any(ob.name.endswith('ERA') and not ob.hide_render for ob in s.objects)
report={'passed':True,'resolution':[2560,1440],'fps':30,'frames':5400,'native_typography':True,'packed_assets':True,'timeline_samples':checks}
(ROOT/'review/scene-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
