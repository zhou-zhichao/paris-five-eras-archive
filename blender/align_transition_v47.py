"""Spatially retire old houses immediately before overlapping new blocks grow."""
import collections
import ast
import argparse
import json
import math
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--version',choices=['v47','v48'],default='v47')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene=bpy.context.scene
scene.frame_set(2174)
old_root=bpy.data.objects['Buildings_1700_State']
data=json.loads((ROOT/'data/late_blocks_v46.json').read_text())
block_grid=collections.defaultdict(list)
blocks=[]
def cells(bounds):
    a,b,c,d=bounds
    return ((x,y) for x in range(math.floor(a/2),math.floor(c/2)+1) for y in range(math.floor(b/2),math.floor(d/2)+1))
for block_index,block in enumerate(data['blocks']):
    if block['phase']!=3:continue
    ring=block['polygon']['coordinates'][0]
    xs=[p[0] for p in ring];ys=[p[1] for p in ring]
    bounds=(min(xs),min(ys),max(xs),max(ys))
    obj=bpy.data.objects[f'Late_Block_{block_index:05d}']
    start=int(obj['growth_start_frame'])
    idx=len(blocks);blocks.append((bounds,start))
    for key in cells(bounds):block_grid[key].append(idx)

def overlaps(a,b,pad=.015):
    return a[0]<=b[2]+pad and a[2]>=b[0]-pad and a[1]<=b[3]+pad and a[3]>=b[1]-pad

def retirement(bounds):
    expanded=(bounds[0]-.12,bounds[1]-.12,bounds[2]+.12,bounds[3]+.12)
    candidates={idx for cell in cells(expanded) for idx in block_grid.get(cell,[])}
    starts=[blocks[idx][1] for idx in candidates if overlaps(expanded,blocks[idx][0],0)]
    if starts:return max(2176,min(starts)-1)
    x=(bounds[0]+bounds[2])/2;y=(bounds[1]+bounds[3])/2
    return max(2176,2175+int(min(1,math.hypot(x,y)/52)*540)-1)

materials=[];material_ids={}
buckets={}
source_faces=0;house_groups=0;max_group_span=0
for object_index,obj in enumerate(list(old_root.children_recursive)):
    if obj.type!='MESH':continue
    if not obj.hide_render:
        mesh=obj.data
        points=[tuple(obj.matrix_world @ v.co) for v in mesh.vertices]
        parent=list(range(len(points)))
        def find(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]];i=parent[i]
            return i
        def join(a,b):
            a=find(a);b=find(b)
            if a!=b:parent[b]=a
        for edge in mesh.edges:join(*edge.vertices)
        components=collections.defaultdict(list)
        for i in range(len(points)):components[find(i)].append(i)
        component_keys=list(components)
        bounds={}
        for key,indices in components.items():
            xs=[points[i][0] for i in indices];ys=[points[i][1] for i in indices]
            bounds[key]=(min(xs),min(ys),max(xs),max(ys))
        # Attach disconnected facade/window pieces to their enclosing house.
        for i,a in enumerate(component_keys):
            for b in component_keys[i+1:]:
                if overlaps(bounds[a],bounds[b]):join(a,b)
        groups=collections.defaultdict(list)
        for key,indices in components.items():groups[find(key)].extend(indices)
        deaths={}
        for key,indices in groups.items():
            xs=[points[i][0] for i in indices];ys=[points[i][1] for i in indices]
            box=(min(xs),min(ys),max(xs),max(ys))
            deaths[key]=retirement(box)
            max_group_span=max(max_group_span,box[2]-box[0],box[3]-box[1])
        house_groups+=len(groups)
        slots=[]
        for m in mesh.materials:
            if m.name not in material_ids:
                material_ids[m.name]=len(materials);materials.append(m)
            slots.append(material_ids[m.name])
        for polygon in mesh.polygons:
            death=deaths[find(polygon.vertices[0])]
            bucket=buckets.setdefault(death,{'verts':[],'faces':[],'materials':[],'smooth':[],'indices':{}})
            face=[]
            for i in polygon.vertices:
                vertex_key=(object_index,i)
                if vertex_key not in bucket['indices']:
                    bucket['indices'][vertex_key]=len(bucket['verts']);bucket['verts'].append(points[i])
                face.append(bucket['indices'][vertex_key])
            bucket['faces'].append(face)
            bucket['materials'].append(slots[polygon.material_index])
            bucket['smooth'].append(polygon.use_smooth)
        source_faces+=len(mesh.polygons)
    obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=2175)
    obj.keyframe_insert(data_path='hide_render',frame=3600)
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            if fc.data_path=='hide_render':
                for key in fc.keyframe_points:
                    if key.co.x>=2175:key.co.y=1
    if object_index%250==0:print('SPLIT',object_index,flush=True)

clone_root=bpy.data.objects.new('1700_Spatial_Retirement_v47',None)
bpy.context.collection.objects.link(clone_root)
for death,bucket in sorted(buckets.items()):
    mesh=bpy.data.meshes.new(f'Old_Fabric_Until_{death}')
    mesh.from_pydata(bucket['verts'],[],bucket['faces'])
    for m in materials:mesh.materials.append(m)
    for p,material,smooth in zip(mesh.polygons,bucket['materials'],bucket['smooth']):
        p.material_index=material;p.use_smooth=smooth
    obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(obj);obj.parent=clone_root
    obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=1)
    obj.keyframe_insert(data_path='hide_render',frame=2174)
    obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=2175)
    obj.keyframe_insert(data_path='hide_render',frame=death-1)
    obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=death)
    obj['retirement_frame']=death
report={'source_faces':source_faces,'cloned_faces':sum(len(b['faces']) for b in buckets.values()),'spatial_groups':house_groups,'max_group_span':max_group_span,'retirement_meshes':len(buckets),'first_retirement':min(buckets),'last_retirement':max(buckets),'method':'Connected geometry and touching XY bounds group facade pieces. Conservative block bounding boxes trigger retirement before new block growth; distant legacy chunk membership is ignored.'}
assert report['source_faces']==report['cloned_faces']
source_tree=ast.parse((ROOT/'blender/build_scene.py').read_text())
city_polygons=next(ast.literal_eval(n.value) for n in source_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CITY_POLYGONS' for t in n.targets))
def inside(x,y,ring):
    result=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result
patches=json.loads((ROOT/'data/late_surfaces_v46.json').read_text())['patches']
delayed=0
for index,patch in enumerate(patches):
    x,y=patch['center']
    if inside(x,y,city_polygons[3]):continue
    obj=bpy.data.objects.get(f'Late_Surface_{index:04d}')
    if not obj:raise RuntimeError(f'Missing surface {index}')
    obj.animation_data_clear()
    start=2850+int(min(1,max(0,(math.hypot(x,y)-27)/40))*600)
    obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=1)
    obj.keyframe_insert(data_path='hide_render',frame=start-1)
    obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=start)
    delayed+=1
report['outer_surface_patches_delayed_until_modern']=delayed
(ROOT/f'reports/transition-{args.version}.json').write_text(json.dumps(report,indent=2))
scene.frame_set(2500)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'blender/paris_{args.version}_spatial_transition.blend'))
print(json.dumps(report),flush=True)
