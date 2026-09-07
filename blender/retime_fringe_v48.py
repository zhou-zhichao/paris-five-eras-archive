import json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'data/fringe_timing_v48.json').read_text())
for row in rows:
    obj=bpy.data.objects[f"Late_Block_{row['block']:05d}"]
    start=row['start']
    obj.animation_data_clear()
    obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=1)
    obj.keyframe_insert(data_path='hide_render',frame=start-1)
    obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=start)
    obj.scale.z=.01;obj.keyframe_insert(data_path='scale',frame=start)
    obj.scale.z=1;obj.keyframe_insert(data_path='scale',frame=start+8)
    obj['growth_start_frame']=start
    obj['deferred_until_modern']=row['deferred']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/paris_v48_fringe_layout.blend'))
