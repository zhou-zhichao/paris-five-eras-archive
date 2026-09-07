"""Export the actual scene surfaces for spatially consistent urban masks."""
import json
from pathlib import Path
import bpy

root=Path(__file__).resolve().parents[1]
bpy.context.scene.frame_set(3550)
result={}
for name in ['Seine','Seine_Riverbank','Ile_de_la_Cite','Ile_Saint_Louis']:
    obj=bpy.data.objects.get(name)
    if not obj:continue
    points=[obj.matrix_world @ v.co for v in obj.data.vertices]
    result[name]={'vertices':[[p.x,p.y,p.z] for p in points],'faces':[list(f.vertices) for f in obj.data.polygons]}
roads=[]
for obj in bpy.data.objects:
    if obj.type=='MESH' and obj.name.startswith('Roads_'):
        roads.append({'name':obj.name,'hidden':obj.hide_render,'vertices':len(obj.data.vertices),'z':list(obj.location)})
result['road_states']=roads
(root/'data/scene_environment.json').write_text(json.dumps(result,separators=(',',':')))
print('SURFACES',[(k,len(v['faces'])) for k,v in result.items() if isinstance(v,dict)])
print('VISIBLE_ROADS',sum(not r['hidden'] for r in roads))
