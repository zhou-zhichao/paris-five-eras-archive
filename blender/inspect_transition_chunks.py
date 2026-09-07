import json
from pathlib import Path
import bpy

scene=bpy.context.scene
scene.frame_set(2174)
root=bpy.data.objects['Buildings_1700_State']
rows=[]
for obj in root.children_recursive:
    if obj.type!='MESH':continue
    vertices=obj.data.vertices
    x=[v.co.x for v in vertices];y=[v.co.y for v in vertices]
    rows.append({'name':obj.name,'vertices':len(vertices),'faces':len(obj.data.polygons),'span':[max(x)-min(x),max(y)-min(y)],'hidden':obj.hide_render,'uv':len(obj.data.uv_layers),'attributes':[a.name for a in obj.data.attributes]})
rows.sort(key=lambda r:max(r['span']),reverse=True)
report={'objects':len(rows),'faces':sum(r['faces'] for r in rows),'wide_chunks':sum(max(r['span'])>5 for r in rows),'largest':rows[:4]}
Path('reports/transition-chunks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
