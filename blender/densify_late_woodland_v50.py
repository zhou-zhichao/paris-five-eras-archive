"""Add small woodland clusters with conservative water/road/building exclusions."""
import collections
import json
import math
import random
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
grid=collections.defaultdict(list)
def cells(bounds):
    x0,y0,x1,y1=bounds
    return ((x,y) for x in range(math.floor(x0/4),math.floor(x1/4)+1) for y in range(math.floor(y0/4),math.floor(y1/4)+1))
def add_mask(bounds,kind,value=None):
    record=(bounds,kind,value)
    for cell in cells(bounds):grid[cell].append(record)
def box(points,pad):
    return (min(p[0] for p in points)-pad,min(p[1] for p in points)-pad,max(p[0] for p in points)+pad,max(p[1] for p in points)+pad)

blocks=json.loads((ROOT/'data/late_blocks_v46.json').read_text())['blocks']
for i,block in enumerate(blocks):
    start=int(bpy.data.objects[f'Late_Block_{i:05d}']['growth_start_frame'])
    add_mask(box(block['polygon']['coordinates'][0],.18),'building',start)
environment=json.loads((ROOT/'data/scene_environment.json').read_text())['Seine']
for face in environment['faces']:
    add_mask(box([environment['vertices'][i] for i in face],.18),'water')
geo=json.loads((ROOT/'data/paris_geodata.json').read_text())
for road in geo['roads']:
    for a,b in zip(road['points'],road['points'][1:]):
        width=road['width']/2+.16
        add_mask(box([a,b],width),'road',(a,b,width))
for record in json.loads((ROOT/'previews/v49-modern.json').read_text())['protected_landmarks']:
    if record['name']=='Modern_Stations':continue
    a,b,c,d=record['bounds'];add_mask((a-.2,b-.2,c+.2,d+.2),'landmark')

# A trunk's five faces share eight vertices; collect each connected trunk.
obj=bpy.data.objects['Forest_Persistent'];mesh=obj.data
parent=list(range(len(mesh.vertices)))
def find(i):
    while parent[i]!=i:
        parent[i]=parent[parent[i]];i=parent[i]
    return i
trunk_indices=set()
for p in mesh.polygons:
    if 'Trunk' not in mesh.materials[p.material_index].name:continue
    indices=list(p.vertices);trunk_indices.update(indices)
    for i in indices[1:]:parent[find(i)]=find(indices[0])
groups=collections.defaultdict(list)
for i in trunk_indices:groups[find(i)].append(i)
basis=mesh.shape_keys.key_blocks[0]
anchors=[]
for indices in groups.values():
    x=sum(basis.data[i].co.x for i in indices)/len(indices)
    y=sum(basis.data[i].co.y for i in indices)/len(indices)
    if 28<math.hypot(x,y)<90:anchors.append((x,y))

def clearance(x,y):
    death=4000
    for (a,b,c,d),kind,value in grid.get((math.floor(x/4),math.floor(y/4)),[]):
        if not(a<=x<=c and b<=y<=d):continue
        if kind=='building':
            if value<2850:return None
            death=min(death,value-1)
        elif kind=='road':
            p,q,width=value;dx=q[0]-p[0];dy=q[1]-p[1]
            t=max(0,min(1,((x-p[0])*dx+(y-p[1])*dy)/max(1e-12,dx*dx+dy*dy)))
            if math.hypot(x-p[0]-t*dx,y-p[1]-t*dy)<width:return None
        else:return None
    return death

rng=random.Random(5001)
buckets={};occupied=set();accepted=0
for x0,y0 in sorted(anchors):
    for _ in range(30):
        angle=rng.uniform(0,math.tau);distance=2.2*math.sqrt(rng.random())
        x=x0+distance*math.cos(angle);y=y0+distance*math.sin(angle)
        if math.hypot(x,y)<28:continue
        death=clearance(x,y)
        if death is None:continue
        cell=(math.floor(x/.2),math.floor(y/.2))
        if cell in occupied:continue
        occupied.add(cell)
        vertices,faces,materials,count=buckets.setdefault(death,[[],[],[],0])
        base=len(vertices);radius=rng.uniform(.065,.12);height=rng.uniform(.15,.32)
        for i in range(6):
            theta=i*math.tau/6
            vertices.append((x+radius*math.cos(theta),y+radius*math.sin(theta),.055))
        vertices.append((x,y,height))
        shade=rng.randrange(3)
        for i in range(6):faces.append((base+i,base+(i+1)%6,base+6));materials.append(shade)
        buckets[death][3]+=1;accepted+=1

root=bpy.data.objects.new('Late_Woodland_Clusters_v50',None);bpy.context.collection.objects.link(root)
for death,(vertices,faces,materials,count) in sorted(buckets.items()):
    mesh=bpy.data.meshes.new(f'Late_Woodland_Until_{death}');mesh.from_pydata(vertices,[],faces)
    for name in ('Forest_Dark','Forest_Deep','Forest_Olive'):mesh.materials.append(bpy.data.materials[name])
    for polygon,material in zip(mesh.polygons,materials):polygon.material_index=material
    obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(obj);obj.parent=root
    obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=1);obj.keyframe_insert(data_path='hide_render',frame=2174)
    obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=2175)
    obj.scale.z=.01;obj.keyframe_insert(data_path='scale',frame=2175)
    obj.scale.z=1;obj.keyframe_insert(data_path='scale',frame=2500)
    if death<4000:
        obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=death-1)
        obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=death)
    obj['tree_count']=count;obj['retirement_frame']=death
report={'added_trees':accepted,'meshes':len(buckets),'anchors':len(anchors),'samples':[],'mask_scope':'Conservative block/water/landmark bounding boxes and center-to-road distance with crown setback. No new trees within radius 28. Existing trees are unchanged.'}
for frame in (2100,2174,2800,3000,3550):
    scene.frame_set(frame)
    visible=[o for o in root.children if not o.hide_render]
    if frame<2175:assert not visible
    assert all(frame<o['retirement_frame'] for o in visible)
    report['samples'].append({'frame':frame,'trees':sum(o['tree_count'] for o in visible)})
scene.frame_set(2800)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/paris_v50_woodland.blend'))
(ROOT/'reports/woodland-v50.json').write_text(json.dumps(report,indent=2))
print('WOODLAND_COMPLETE',json.dumps(report),flush=True)
