"""Replace late-era scattered houses with street perimeter blocks."""
import json
import argparse
import sys
import math
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--version',choices=['v45','v46'],default='v45')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene=bpy.context.scene
data=json.loads((ROOT/f'data/late_blocks_{args.version}.json').read_text())
for name in ['Buildings_1850_State','Buildings_Modern_State']:
    obj=bpy.data.objects.get(name)
    if obj:
        bpy.data.batch_remove(list(obj.children_recursive)+[obj])

def mat(name,color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bsdf=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Roughness'].default_value=.85
    return m
materials=[mat('Late_Limestone_'+str(i),c) for i,c in enumerate([(.63,.58,.47),(.72,.67,.56),(.58,.54,.46),(.68,.62,.51),(.57,.54,.49)])]
materials += [mat('Late_Zinc',(.24,.22,.19)),mat('Late_Recess',(.095,.105,.105)),mat('Late_Cornice',(.46,.43,.37))]
parent=bpy.data.objects.new(f'Late_Perimeter_Blocks_{args.version}',None)
bpy.context.collection.objects.link(parent)
for index,block in enumerate(data['blocks']):
    verts=[];faces=[];ids=[]
    h=block['height']; wall=block['palette']
    def face(points,material):
        start=len(verts);verts.extend(points)
        faces.append(tuple(range(start,start+len(points))));ids.append(material)
    for parcel in block['parcels']:
        h=parcel['height'];wall=parcel['palette']
        for ring in parcel['rings']:
            for a,b in zip(ring,ring[1:]):
                ax,ay=a;bx,by=b
                face([(ax,ay,.035),(bx,by,.035),(bx,by,h),(ax,ay,h)],wall)
                dx=bx-ax;dy=by-ay;length=math.hypot(dx,dy)
                if length<.08:continue
                nx=dy/length*.001;ny=-dx/length*.001
                count=max(1,int(length/.14))
                for k in range(count):
                    t=(k+.5)/count;half=min(.025,length/count*.22)
                    cx=ax+dx*t+nx;cy=ay+dy*t+ny
                    ux=dx/length*half;uy=dy/length*half
                    for floor in range(2):
                        z=.075+floor*(h-.09)/2
                        face([(cx-ux,cy-uy,z),(cx+ux,cy+uy,z),(cx+ux,cy+uy,z+.04),(cx-ux,cy-uy,z+.04)],6)
        if parcel['convex']:
            cx,cy=parcel['peak']
            ring=parcel['rings'][0]
            for a,b in zip(ring,ring[1:]):
                face([(a[0],a[1],h),(b[0],b[1],h),(cx,cy,h+.065)],5)
        else:
            for tri in parcel['triangles']:
                face([(x,y,h+.02) for x,y in tri],5)
    mesh=bpy.data.meshes.new(f'Late_Block_{index:05d}')
    mesh.from_pydata(verts,[],faces)
    for m in materials:mesh.materials.append(m)
    for polygon,material in zip(mesh.polygons,ids):polygon.material_index=material
    mesh.update()
    obj=bpy.data.objects.new(mesh.name,mesh)
    bpy.context.collection.objects.link(obj);obj.parent=parent
    x,y=block['center']
    distance=math.hypot(x,y)
    phase=block['phase']
    start=2175+int(min(1,distance/52)*540) if phase==3 else 2850+int(min(1,max(0,(distance-27)/40))*620)
    obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=1)
    obj.keyframe_insert(data_path='hide_render',frame=start-1)
    obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=start)
    obj.scale.z=.01;obj.keyframe_insert(data_path='scale',frame=start)
    obj.scale.z=1;obj.keyframe_insert(data_path='scale',frame=start+8)
    obj['growth_start_frame']=start
    obj['era_proxy']=phase
    if index%1000==0:print('BLOCKS',index,flush=True)
land=bpy.data.materials.get('Land_Material')
if land and land.use_nodes:
    nodes=land.node_tree.nodes
    bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    socket=bsdf.inputs['Base Color']
    source=socket.links[0].from_socket if socket.is_linked else None
    tint=nodes.new('ShaderNodeMixRGB');tint.name='Late_Ground_Tone_v45'
    tint.blend_type='MULTIPLY'
    if source:land.node_tree.links.new(source,tint.inputs[1])
    else:tint.inputs[1].default_value=socket.default_value
    tint.inputs[2].default_value=(.30,.37,.25,1)
    land.node_tree.links.new(tint.outputs[0],socket)
    tint.inputs[0].default_value=0
    tint.inputs[0].keyframe_insert(data_path='default_value',frame=1)
    tint.inputs[0].keyframe_insert(data_path='default_value',frame=2174)
    tint.inputs[0].default_value=1
    tint.inputs[0].keyframe_insert(data_path='default_value',frame=2850)
if args.version=='v46':
    for obj in bpy.data.objects:
        if obj.type=='MESH' and obj.name.startswith('Roads_'):
            obj.hide_render=True
            obj.keyframe_insert(data_path='hide_render',frame=2175)
            obj.keyframe_insert(data_path='hide_render',frame=3600)
            # Later original growth keys must not turn a retired road back on.
            if obj.animation_data and obj.animation_data.action:
                for fc in obj.animation_data.action.fcurves:
                    if fc.data_path=='hide_render':
                        for key in fc.keyframe_points:
                            if key.co.x>=2175:key.co.y=1
    surface_data=json.loads((ROOT/'data/late_surfaces_v46.json').read_text())
    road_mat=mat('Late_Street_Asphalt',(.20,.19,.16))
    quay_mat=mat('Late_Quay_Stone',(.46,.44,.37))
    for index,patch in enumerate(surface_data['patches']):
        mesh=bpy.data.meshes.new(f'Late_Surface_{index:04d}')
        z=.025 if patch['kind']=='road' else -.015
        verts=[(x,y,z) for tri in patch['triangles'] for x,y in tri]
        mesh.from_pydata(verts,[],[(i,i+1,i+2) for i in range(0,len(verts),3)])
        mesh.materials.append(road_mat if patch['kind']=='road' else quay_mat)
        obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(obj)
        # Replace the existing mature inner network at the era boundary.
        distance=math.hypot(*patch['center'])
        start=2175 if distance<30 else 2175+int(min(1,(distance-30)/35)*600)
        obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=1)
        obj.keyframe_insert(data_path='hide_render',frame=start-1)
        obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=start)
scene.frame_set(3550)
output=ROOT/f'blender/paris_{args.version}_late_blocks.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(output))
print('SAVED',output,flush=True)
