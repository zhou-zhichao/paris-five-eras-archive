"""Build a self-contained animated Blender reconstruction from new parcel data."""
from pathlib import Path
import sys
import json
import math
import argparse
import random
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from mesh_assets import Mesh, MATERIALS, palette, material, srgb, house, tree, landmark

def args():
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview',type=float,nargs='*')
    parser.add_argument('--width',type=int,default=1280)
    parser.add_argument('--engine',default='BLENDER_EEVEE_NEXT')
    return parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

OPT=args()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine=OPT.engine
scene.render.resolution_x=2560;scene.render.resolution_y=1440;scene.render.resolution_percentage=100
scene.render.fps=30;scene.frame_start=1;scene.frame_end=5400
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
scene.render.film_transparent=False
scene.render.use_file_extension=True
scene.render.image_settings.compression=15
scene.world=bpy.data.worlds.new('Soft cool fill')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.53,.60,.70,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.22
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.45
if hasattr(scene,'eevee'):
    scene.eevee.taa_render_samples=48
    scene.eevee.use_raytracing=False
    scene.eevee.shadow_resolution_scale=1
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.cycles.max_bounces=5
scene.cycles.diffuse_bounces=2
scene.cycles.glossy_bounces=2
scene.cycles.transparent_max_bounces=4
scene.render.use_persistent_data=True
ids=palette()
data=json.loads((ROOT/'data/city.json').read_text())
rng=random.Random(42)

def key(ob,path,t,value):
    setattr(ob,path,value)
    ob.keyframe_insert(data_path=path,frame=round(t*30)+1)

def linear_animation(owner):
    if owner.animation_data and owner.animation_data.action:
        for fc in owner.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'

def appear(ob,born,gone=300):
    base=ob.scale.copy()
    if born>0:
        key(ob,'scale',max(0,born-.05),(.0001,)*3)
        key(ob,'scale',born+.7,base)
    if gone<180:
        key(ob,'scale',gone,base)
        key(ob,'scale',gone+.55,(.0001,)*3)
    wipe=169.7+(750-ob.location.x)/380
    key(ob,'scale',wipe,base if gone>180 else (.0001,)*3)
    key(ob,'scale',wipe+.3,(.0001,)*3)
    linear_animation(ob)

def poly_surface(points,z,mat,m=None,born=-100):
    m=m or Mesh()
    vv=[Vector((x,y,z)) for x,y in points[:-1] if len(points)>3]
    if len(vv)<3:return m
    for tri in tessellate_polygon([vv]):m.face([tuple(vv[v] if isinstance(v,int) else v) for v in tri],mat,born)
    return m

def ribbon(m,points,width,z,mat,born=-100):
    for a,b in zip(points,points[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy)
        if length<.001:continue
        nx,ny=-dy/length*width/2,dx/length*width/2
        m.face([(a[0]+nx,a[1]+ny,z),(a[0]-nx,a[1]-ny,z),(b[0]-nx,b[1]-ny,z),(b[0]+nx,b[1]+ny,z)],mat,born)

def nodes_base(name):
    g=bpy.data.node_groups.new(name,'GeometryNodeTree')
    g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    ni=g.nodes.new('NodeGroupInput');no=g.nodes.new('NodeGroupOutput')
    return g,ni,no

def mathnode(g,op,a,b=None):
    n=g.nodes.new('ShaderNodeMath');n.operation=op
    for val,inp in [(a,n.inputs[0]),(b,n.inputs[1])]:
        if val is None:continue
        if isinstance(val,(float,int)):inp.default_value=val
        else:g.links.new(val,inp)
    return n.outputs[0]

def named(g,name,typ='FLOAT'):
    n=g.nodes.new('GeometryNodeInputNamedAttribute');n.data_type=typ;n.inputs['Name'].default_value=name
    return n.outputs['Attribute']

def wipe_field(g,t):
    pos=g.nodes.new('GeometryNodeInputPosition')
    sep=g.nodes.new('ShaderNodeSeparateXYZ');g.links.new(pos.outputs[0],sep.inputs[0])
    limit=mathnode(g,'SUBTRACT',750,mathnode(g,'MULTIPLY',mathnode(g,'SUBTRACT',t,169.7),380))
    return mathnode(g,'GREATER_THAN',sep.outputs['X'],limit)

def timed_surface(ob):
    g,ni,no=nodes_base(ob.name+' construction visibility')
    time=g.nodes.new('GeometryNodeInputSceneTime').outputs['Seconds']
    before=mathnode(g,'LESS_THAN',time,named(g,'born'))
    deleted=mathnode(g,'MAXIMUM',before,wipe_field(g,time))
    d=g.nodes.new('GeometryNodeDeleteGeometry');d.domain='FACE'
    g.links.new(ni.outputs[0],d.inputs['Geometry']);g.links.new(deleted,d.inputs['Selection']);g.links.new(d.outputs[0],no.inputs[0])
    ob.modifiers.new('Localized construction dates','NODES').node_group=g

def instances(name,records,templates,forest=False):
    a=np.array(records,dtype=np.float32)
    n=len(a)
    mesh=bpy.data.meshes.new(name+' point cloud')
    mesh.vertices.add(n)
    coords=np.zeros((n,3),dtype=np.float32);coords[:,:2]=a[:,:2];coords[:,2]=.125
    mesh.vertices.foreach_set('co',coords.ravel())
    def attr(name,typ,values):
        p=mesh.attributes.new(name,typ,'POINT')
        p.data.foreach_set('vector' if typ=='FLOAT_VECTOR' else 'value',np.array(values).ravel())
    if forest:
        attr('size','FLOAT_VECTOR',np.stack([a[:,2],a[:,2],a[:,3]],axis=1))
        rot=np.zeros((n,3));rot[:,2]=np.arange(n)*2.39996
        attr('rotation','FLOAT_VECTOR',rot)
        attr('gone','FLOAT',a[:,4]);attr('variant','INT',a[:,5].astype(np.int32));attr('born','FLOAT',a[:,6])
    else:
        sizes=a[:,2:5].copy();sizes[:,2]*=1.6
        attr('size','FLOAT_VECTOR',sizes)
        rot=np.zeros((n,3));rot[:,2]=a[:,5]
        attr('rotation','FLOAT_VECTOR',rot)
        attr('born','FLOAT',a[:,6]);attr('gone','FLOAT',a[:,7]);attr('variant','INT',a[:,8].astype(np.int32))
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
    g,ni,no=nodes_base(name+' deterministic growth')
    time=g.nodes.new('GeometryNodeInputSceneTime').outputs['Seconds']
    delta=mathnode(g,'SUBTRACT',time,named(g,'born'))
    mr=g.nodes.new('ShaderNodeMapRange');mr.interpolation_type='SMOOTHSTEP';mr.clamp=True
    g.links.new(delta,mr.inputs['Value']);mr.inputs['From Min'].default_value=0;mr.inputs['From Max'].default_value=.85
    end=mathnode(g,'MULTIPLY',mathnode(g,'SUBTRACT',named(g,'gone'),time),2.0)
    end=mathnode(g,'MINIMUM',1,mathnode(g,'MAXIMUM',0,end))
    size=mathnode(g,'MULTIPLY',mr.outputs[0],end)
    wipe=wipe_field(g,time)
    if forest:
        natural=mathnode(g,'LESS_THAN',named(g,'born'),0)
        size=mathnode(g,'ADD',mathnode(g,'MULTIPLY',size,mathnode(g,'SUBTRACT',1,wipe)),mathnode(g,'MULTIPLY',wipe,natural))
    else:size=mathnode(g,'MULTIPLY',size,mathnode(g,'SUBTRACT',1,wipe))
    dele=g.nodes.new('GeometryNodeDeleteGeometry');dele.domain='POINT'
    g.links.new(ni.outputs[0],dele.inputs['Geometry']);g.links.new(mathnode(g,'LESS_THAN',size,.001),dele.inputs['Selection'])
    coll=g.nodes.new('GeometryNodeCollectionInfo');coll.inputs['Collection'].default_value=templates
    coll.inputs['Separate Children'].default_value=True;coll.inputs['Reset Children'].default_value=True
    ins=g.nodes.new('GeometryNodeInstanceOnPoints');ins.inputs['Pick Instance'].default_value=True
    g.links.new(dele.outputs[0],ins.inputs['Points']);g.links.new(coll.outputs['Instances'],ins.inputs['Instance'])
    g.links.new(named(g,'variant','INT'),ins.inputs['Instance Index']);g.links.new(named(g,'rotation','FLOAT_VECTOR'),ins.inputs['Rotation'])
    scale=g.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE'
    g.links.new(named(g,'size','FLOAT_VECTOR'),scale.inputs[0]);g.links.new(size,scale.inputs['Scale'])
    g.links.new(scale.outputs[0],ins.inputs['Scale']);g.links.new(ins.outputs[0],no.inputs[0])
    ob.modifiers.new('Original architecture instances','NODES').node_group=g
    return ob

print('Building terrain and waterways',flush=True)
ground=Mesh();ground.box(0,0,-1,5000,5000,1,ids['lawn']);ground.object('Olive landscape')
gm=MATERIALS[ids['lawn']];nt=gm.node_tree;bs=nt.nodes.get('Principled BSDF')
tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=.007;tex.inputs['Detail'].default_value=2;tex.inputs['Roughness'].default_value=.6
coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],tex.inputs['Vector'])
ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(*srgb('#405033'),1);ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=(*srgb('#66744D'),1)
nt.links.new(tex.outputs['Fac'],ramp.inputs['Fac']);nt.links.new(ramp.outputs[0],bs.inputs['Base Color'])
water_id=material('Seine teal water','#76A79E',.33,.02)
MATERIALS[water_id].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.10
wn=MATERIALS[water_id].node_tree
wpos=wn.nodes.new('ShaderNodeTexCoord')
bank=wn.nodes.new('ShaderNodeAttribute');bank.attribute_name='bank_distance'
bm=wn.nodes.new('ShaderNodeMapRange');bm.inputs['From Max'].default_value=5
wn.links.new(bank.outputs['Fac'],bm.inputs['Value'])
bc=wn.nodes.new('ShaderNodeValToRGB');bc.color_ramp.interpolation='EASE'
bc.color_ramp.elements[0].color=(*srgb('#C2C8AA'),1)
bc.color_ramp.elements[1].color=(*srgb('#347D78'),1)
middle=bc.color_ramp.elements.new(.36);middle.color=(*srgb('#8CAC9A'),1)
wn.links.new(bm.outputs[0],bc.inputs[0]);wn.links.new(bc.outputs[0],wn.nodes['Principled BSDF'].inputs['Base Color'])
wave=wn.nodes.new('ShaderNodeTexNoise');wave.inputs['Scale'].default_value=2.2;wave.inputs['Detail'].default_value=2
wn.links.new(wpos.outputs['Object'],wave.inputs['Vector'])
bump=wn.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.045
wn.links.new(wave.outputs['Fac'],bump.inputs['Height']);wn.links.new(bump.outputs['Normal'],wn.nodes['Principled BSDF'].inputs['Normal'])
water_parts=json.loads((ROOT/'data/water_surface.json').read_text())
for i,part in enumerate(water_parts):
    wm=bpy.data.meshes.new(f'Seine shoreline topology {i}')
    wm.from_pydata([(x,y,.042) for x,y in part['vertices']],[],part['triangles']);wm.update()
    wm.materials.append(MATERIALS[water_id])
    distance=wm.attributes.new('bank_distance','FLOAT','POINT');distance.data.foreach_set('value',part['bank_distance'])
    wo=bpy.data.objects.new(f'Continuous Seine surface {i}',wm);scene.collection.objects.link(wo)
shore=Mesh()
for p in data['water_outer']:ribbon(shore,p,1.55,.062,ids['sand'])
for i,p in enumerate(data['islands']):
    poly_surface(p,.10,ids['lawn']).object('Ile de la Cite' if i==0 else f'River island {i}')
    ribbon(shore,p,.8,.12,ids['sand'])
shore.object('Pale natural banks')

print('Building newly modeled house library',flush=True)
arch_collection=bpy.data.collections.new('Original architecture library - 72 variants')
for kind in range(6):
    for variation in range(12):house(kind,variation,ids).object(f'{kind*12+variation:03d} '+['Roman courtyard wing','Medieval gabled street house','Limestone city house','Paris mansard street house','Outer suburb house','Modern apartment'][kind],arch_collection)
for i in range(6):
    hut=Mesh();hut.frustum(0,0,0,.45,.45,.48,.45,.45,ids['warm_plaster'],7)
    hut.frustum(0,0,.48,.54,.54,.49,.035,.035,ids['ochre_plaster'],7)
    hut.box(0,-.439,0,.15,.025,.29,ids['timber'])
    hut.object(f'{72+i:03d} Celtic thatched roundhouse',arch_collection)
tree_collection=bpy.data.collections.new('Original tree library - 8 variants')
for i in range(8):tree(i,ids).object(f'{i:03d} sculpted tree',tree_collection)
instances('Growing Paris - new street-aligned buildings',data['buildings'],arch_collection)
forest=[t[:2]+[t[2]*1.5,t[3]*1.5]+t[4:6]+[t[6] if len(t)>6 else -100] for i,t in enumerate(data['trees']) if i%3!=0 or len(t)>6]
instances('Forest and formal avenue trees',forest,tree_collection,True)

print('Building streets and gardens',flush=True)
court_id=material('Courtyard limestone and packed earth','#94947C',.95)
yards=Mesh()
for record in data['blocks']:
    poly_surface(record['polygon'],.111,court_id,yards,record['born'])
timed_surface(yards.object('Urban courtyard surfaces'))
roads=Mesh()
for record in data['roads']:
    # Long rural routes precede urbanization; small lanes emerge near the growth front.
    ribbon(roads,record['points'],record['width'],.13,ids['path'],record['born'])
road_ob=roads.object('Streets - local lanes and major axes');timed_surface(road_ob)
rail_id=material('Railway ballast','#666B5E',.9)
railmesh=Mesh()
for record in data.get('rails',[]):
    ribbon(railmesh,record['points'],7.4,.30,rail_id,record['born'])
    for offset in [-2.8,-1.7,-.6,.6,1.7,2.8]:
        shifted=[]
        pts=record['points']
        for i,(x,y) in enumerate(pts):
            a=pts[max(0,i-1)];b=pts[min(len(pts)-1,i+1)];l=math.dist(a,b) or 1
            shifted.append((x-(b[1]-a[1])/l*offset,y+(b[0]-a[0])/l*offset))
        ribbon(railmesh,shifted,.16,.34,ids['zinc'],record['born'])
timed_surface(railmesh.object('Six railway approaches'))
highway=Mesh()
for record in data['roads']:
    if record['kind']=='ring' and record['born']==149:
        ribbon(highway,record['points'],3.6,1.0,rail_id,149)
        ribbon(highway,record['points'],.15,1.025,ids['sand'],149)
timed_surface(highway.object('Modern boulevard peripherique'))
parkmesh=Mesh();paths=Mesh()
for pi,p in enumerate(data['parks']):
    born=70 if pi<4 else 129
    poly_surface(p+[p[0]] if p[-1]!=p[0] else p,.115,ids['garden'],parkmesh,born)
    ribbon(paths,p+[p[0]],.7,.145,ids['sand'],born)
    if pi<4:
        a,b,c,d=p[:4]
        for t in [.15,.35,.5,.65,.85]:
            q0=(a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t)
            q1=(d[0]*(1-t)+c[0]*t,d[1]*(1-t)+c[1]*t)
            ribbon(paths,[q0,q1],.70,.146,ids['sand'],born)
        ribbon(paths,[(a[0]*.5+d[0]*.5,a[1]*.5+d[1]*.5),(b[0]*.5+c[0]*.5,b[1]*.5+c[1]*.5)],1,.146,ids['sand'],born)
for m,n in [(parkmesh,'Formal gardens'),(paths,'Garden walks')]:timed_surface(m.object(n))

def pixel(x,y):return ((x-1140)*.62,(550-y)*.66)

print('Building bridges and landmarks',flush=True)
bridge_specs=[(1050,532,1044,575,8),(1135,528,1129,589,9),(1212,552,1207,593,53),(1285,574,1271,621,62),(978,520,975,562,69),(875,512,873,554,75),(778,523,784,564,91),(639,562,653,607,102),(533,611,553,648,122),(421,699,450,722,124),(340,872,365,883,133),(1382,615,1371,647,117),(1570,697,1555,735,128),(1766,781,1755,821,134)]
for i,(x0,y0,x1,y1,born) in enumerate(bridge_specs):
    a,b=pixel(x0,y0),pixel(x1,y1);length=math.dist(a,b);width=1.6 if i<4 else 2.6
    m=Mesh();m.box(0,0,.56,width,length,.26,ids['limestone'])
    for side in [-1,1]:m.box(side*width*.46,0,.82,.12,length,.20,ids['sand'])
    count=max(2,round(length/3.6))
    for j in range(count+1):m.box(0,-length/2+j*length/count,.07,width*.8,.46,.5,ids['sand'])
    ob=m.object(f'Bridge {i+1:02d}');ob.location=((a[0]+b[0])/2,(a[1]+b[1])/2,0);ob.rotation_euler.z=math.atan2(b[1]-a[1],b[0]-a[0])-math.pi/2
    appear(ob,born)

def import_landmark(spec):
    filename='notre-dame-clean-200k.glb' if spec['kind']=='notre_dame' else 'eiffel_tower_low_poly.glb'
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/models'/filename))
    imported=[o for o in bpy.data.objects if o not in before]
    meshes=[o for o in imported if o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join();ob=bpy.context.object
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    corners=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    low=Vector(tuple(min(v[i] for v in corners) for i in range(3)));high=Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    dimension=high-low
    scale=spec['size']/(dimension.z if spec['kind']=='eiffel' else max(dimension.x,dimension.y))
    centre=Vector(((high.x+low.x)/2,(high.y+low.y)/2,low.z))
    transform=ob.matrix_world.copy()
    for v in ob.data.vertices:v.co=(transform@v.co-centre)*scale
    ob.matrix_world.identity();ob.name=spec['name']+' - approved reused mesh'
    # Recolor imported meshes to the miniature's unified material palette.
    if spec['kind']=='eiffel':
        steel=material('Warm Eiffel iron','#806E50',.67,.35)
        ob.data.materials.clear();ob.data.materials.append(MATERIALS[steel])
        for p in ob.data.polygons:p.material_index=0
    for o in imported:
        if o.name in bpy.data.objects and o!=ob:bpy.data.objects.remove(o,do_unlink=True)
    ob.location=(*spec['xy'],.13)
    return ob

landmark_audit=[]
for spec in data['landmarks']:
    if spec['kind'] in ['notre_dame','eiffel']:ob=import_landmark(spec)
    else:
        ob=landmark(spec['kind'],spec['size'],ids).object(spec['name']+' - original mesh')
        ob.location=(*spec['xy'],.13)
        if spec['name']=='Louvre':ob.scale.z=.55
        ob.rotation_euler.z=spec.get('rotation',0)
    appear(ob,spec['born'],48 if spec['kind'] in ['arena','forum'] else 300)
    landmark_audit.append({'name':ob.name,'vertices':len(ob.data.vertices),'location':list(ob.location)})

# Fortification loops are hand-built walls and repeated low round towers.
for label,rx,ry,born,gone in [('Medieval enceinte',174,145,51,78),('Early modern enceinte',236,201,66,122),('Thiers fortifications',578,474,121,149)]:
    m=Mesh();points=[]
    for i in range(97):
        a=i/96*math.tau
        points.append((-26+rx*math.cos(a)*(1+.022*math.sin(a*11)),22+ry*math.sin(a)*(1+.03*math.cos(a*9))))
    for a,b in zip(points,points[1:]):
        if abs((a[1]+b[1])/2)<24 and -200<a[0]<200:continue
        dx,dy=b[0]-a[0],b[1]-a[1];n=math.hypot(dx,dy);nx,ny=-dy/n*.3,dx/n*.3
        m.face([(a[0]+nx,a[1]+ny,.1),(b[0]+nx,b[1]+ny,.1),(b[0]+nx,b[1]+ny,1.4),(a[0]+nx,a[1]+ny,1.4)],ids['sand'])
        m.face([(a[0]+nx,a[1]+ny,1.4),(b[0]+nx,b[1]+ny,1.4),(b[0]-nx,b[1]-ny,1.4),(a[0]-nx,a[1]-ny,1.4)],ids['limestone'])
        m.frustum(a[0],a[1],.1,.75,.75,1.7,.75,.75,ids['sand'],8)
    ob=m.object(label);appear(ob,born,gone)

print('Calibrating the continuous reference camera',flush=True)
traces=Mesh()
for points in [
    [(-160,20),(-175,80),(-125,150),(-45,177),(40,180),(90,155),(120,100),(100,15)],
    [(30,-10),(55,-55),(30,-80),(45,-115),(0,-150),(20,-195),(40,-210),(25,-260),(70,-310),(80,-450)],
]:
    ribbon(traces,points,.8,.15,ids['path'])
trace_ob=traces.object('Two pale routes revealed after time reversal')
g,ni,no=nodes_base('Last landscape routes');t=g.nodes.new('GeometryNodeInputSceneTime').outputs['Seconds']
hidden=mathnode(g,'SUBTRACT',1,wipe_field(g,t))
dele=g.nodes.new('GeometryNodeDeleteGeometry');dele.domain='FACE'
g.links.new(ni.outputs[0],dele.inputs[0]);g.links.new(hidden,dele.inputs['Selection']);g.links.new(dele.outputs[0],no.inputs[0])
trace_ob.modifiers.new('Reveal with undeveloped landscape','NODES').node_group=g
grid_id=material('Pale cyan time reversal grid','#B9E7ED',.8)
gb=MATERIALS[grid_id].node_tree.nodes['Principled BSDF'];gb.inputs['Emission Color'].default_value=(*srgb('#B9E7ED'),1);gb.inputs['Emission Strength'].default_value=.6
grid=Mesh()
for q in np.arange(-1700,1701,15):
    ribbon(grid,[(q,y) for y in np.arange(-1200,1201,15)],.14,9,grid_id)
    ribbon(grid,[(x,q) for x in np.arange(-1700,1701,15)],.14,9,grid_id)
angle=math.radians(20);co=math.cos(angle);si=math.sin(angle)
grid.v=[(x*co-y*si,x*si+y*co,z) for x,y,z in grid.v]
grid_ob=grid.object('Reference ending - moving survey grid')
g,ni,no=nodes_base('Survey grid reveal band');t=g.nodes.new('GeometryNodeInputSceneTime').outputs['Seconds']
pos=g.nodes.new('GeometryNodeInputPosition');sp=g.nodes.new('ShaderNodeSeparateXYZ');g.links.new(pos.outputs[0],sp.inputs[0])
front=mathnode(g,'SUBTRACT',750,mathnode(g,'MULTIPLY',mathnode(g,'SUBTRACT',t,169.7),380))
dist=mathnode(g,'ABSOLUTE',mathnode(g,'SUBTRACT',sp.outputs['X'],front))
hide=mathnode(g,'MAXIMUM',mathnode(g,'GREATER_THAN',dist,300),mathnode(g,'LESS_THAN',t,169.8))
hide=mathnode(g,'MAXIMUM',hide,mathnode(g,'GREATER_THAN',t,176.3))
dele=g.nodes.new('GeometryNodeDeleteGeometry');dele.domain='FACE';g.links.new(ni.outputs[0],dele.inputs[0]);g.links.new(hide,dele.inputs['Selection']);g.links.new(dele.outputs[0],no.inputs[0]);grid_ob.modifiers.new('Wipe window','NODES').node_group=g
camera_data=bpy.data.cameras.new('Continuous retreat camera');camera=bpy.data.objects.new('Reference camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera
camera_data.type='PERSP';camera_data.clip_start=50;camera_data.clip_end=6000;camera_data.lens=48
focus=bpy.data.objects.new('Miniature focus plane',None);scene.collection.objects.link(focus)
camera_data.dof.use_dof=True
camera_data.dof.focus_object=focus;camera_data.dof.aperture_fstop=.85
camera_keys=[(0,(-7,-21),325,-55,34),(6,(-7,-21),325,-55,34),(18,(-7,-28),325,-55,34),(24,(-7,-28),345,-54,36),(36,(-8,-20),475,-46,39),(48,(-10,-5),650,-35,42),(60,(-20,8),840,-26,46),(80,(-35,0),1030,-20,50),(100,(-45,6),1170,-13,54),(120,(-58,12),1290,-9,58),(140,(-72,15),1270,-8,60),(160,(-72,15),1270,-8,60),(180,(-72,15),1270,-8,60)]
for t,target,width,az,el in camera_keys:
    az=math.radians(az);el=math.radians(el);distance=width*48/36
    direction=Vector((math.sin(az)*math.cos(el),-math.cos(az)*math.cos(el),math.sin(el)))
    look=Vector((*target,0))
    key(camera,'location',t,look+direction*distance)
    key(camera,'rotation_euler',t,(look-camera.location).to_track_quat('-Z','Y').to_euler())
    key(camera_data,'ortho_scale',t,width)
    key(focus,'location',t,look)
linear_animation(camera);linear_animation(camera_data);linear_animation(focus)

# Native Blender typography: year digits are instanced meshes, driven by an animated value.
# No frame-change Python handler or external subtitle renderer is required by the .blend.
text_id=material('Reference white typography','#FFFFFF',1)
tn=MATERIALS[text_id].node_tree;tn.nodes.clear();te=tn.nodes.new('ShaderNodeEmission');te.inputs[0].default_value=(1,1,1,1);te.inputs[1].default_value=3
to=tn.nodes.new('ShaderNodeOutputMaterial');tn.links.new(te.outputs[0],to.inputs['Surface'])
fontpath=Path('C:/Windows/Fonts/DejaVuSansCondensed-Bold.ttf')
font=bpy.data.fonts.load(str(fontpath)) if fontpath.exists() else bpy.data.fonts.get('Bfont')
def text_mesh(name,body,size,align='LEFT'):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x=align;cu.resolution_u=8;cu.font=font
    ob=bpy.data.objects.new(name,cu);scene.collection.objects.link(ob);cu.materials.append(MATERIALS[text_id])
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH')
    return bpy.context.object
digits=bpy.data.collections.new('Year counter digit meshes')
for i,char in enumerate('0123456789-'):
    ob=text_mesh(f'{i:02d} digit {char}',char,3.6,'CENTER')
    for coll in list(ob.users_collection):coll.objects.unlink(ob)
    digits.objects.link(ob)
dm=bpy.data.meshes.new('Year counter positions');dm.from_pydata([(14.2+2.0*i,-11.65,0) for i in range(4)],[],[])
attr=dm.attributes.new('place','FLOAT','POINT');attr.data.foreach_set('value',[1000,100,10,1])
dob=bpy.data.objects.new('Animated year counter',dm);scene.collection.objects.link(dob);dob.parent=camera;dob.location=(0,0,-200);dob.scale=(200/60,)*3
g,ni,no=nodes_base('Reference year curve and decimal digits')
year=g.nodes.new('ShaderNodeValue');year.label='Year transcribed from source video'
year_knots=[(0,-300),(1,-269),(6,-115),(12,71),(18,257),(24,428),(30,594),(36,779),(42,971),(48,1159),(54,1316),(60,1441),(66,1540),(72,1616),(80,1674),(90,1735),(100,1781),(110,1809),(120,1837),(127,1857),(136,1884),(144,1924),(152,1972),(160,2010),(165,2024),(166,2025),(180,2025)]
for sec,value in year_knots:
    year.outputs[0].default_value=value;year.outputs[0].keyframe_insert(data_path='default_value',frame=round(sec*30)+1)
linear_animation(g)
y=mathnode(g,'ROUND',year.outputs[0]);absolute=mathnode(g,'ABSOLUTE',y);place=named(g,'place')
num=mathnode(g,'MODULO',mathnode(g,'FLOOR',mathnode(g,'DIVIDE',absolute,place)),10)
negative=mathnode(g,'LESS_THAN',y,0)
leading=mathnode(g,'LESS_THAN',absolute,place)
at_sign=mathnode(g,'MULTIPLY',negative,mathnode(g,'MULTIPLY',leading,mathnode(g,'GREATER_THAN',absolute,mathnode(g,'SUBTRACT',mathnode(g,'DIVIDE',place,10),1))))
index=mathnode(g,'ADD',mathnode(g,'MULTIPLY',at_sign,10),mathnode(g,'MULTIPLY',mathnode(g,'SUBTRACT',1,at_sign),num))
is_blank=mathnode(g,'MULTIPLY',leading,mathnode(g,'SUBTRACT',1,at_sign))
is_blank=mathnode(g,'MULTIPLY',is_blank,mathnode(g,'GREATER_THAN',place,1))
dele=g.nodes.new('GeometryNodeDeleteGeometry');dele.domain='POINT';g.links.new(ni.outputs[0],dele.inputs[0]);g.links.new(is_blank,dele.inputs['Selection'])
ci=g.nodes.new('GeometryNodeCollectionInfo');ci.inputs['Collection'].default_value=digits;ci.inputs['Separate Children'].default_value=True;ci.inputs['Reset Children'].default_value=True
ins=g.nodes.new('GeometryNodeInstanceOnPoints');ins.inputs['Pick Instance'].default_value=True;g.links.new(dele.outputs[0],ins.inputs['Points']);g.links.new(ci.outputs[0],ins.inputs['Instance']);g.links.new(index,ins.inputs['Instance Index']);g.links.new(ins.outputs[0],no.inputs[0]);dob.modifiers.new('Native year animation','NODES').node_group=g
key(dob,'hide_render',0,False);key(dob,'hide_render',171.2,True)
eras=[('CELTIC ERA',0,8.6),('ROMAN ERA',8.6,26.2),('FRANKISH ERA',26.2,40.5),('MEDIEVAL ERA',40.5,63.3),('MODERN ERA',63.3,107),('NAPOLEONIC ERA',107,122.1),('HAUSMANN ERA',122.1,132.7),('INDUSTRIAL ERA',132.7,149),('GLOBALIZATION ERA',149,171.2)]
for name,start,end in eras:
    ob=text_mesh(name,name,1.9);ob.parent=camera;ob.location=(-20.95*200/60,-11.65*200/60,-200);ob.scale=(.72*200/60,200/60,200/60)
    if start>0:key(ob,'hide_render',0,True)
    key(ob,'hide_render',start,False);key(ob,'hide_render',end,True)

sun_data=bpy.data.lights.new('Warm afternoon sun','SUN');sun_data.energy=3.2;sun_data.angle=.075;sun_data.color=(1,.94,.84)
sun=bpy.data.objects.new('Warm afternoon sun',sun_data);scene.collection.objects.link(sun)
sun.rotation_euler=Vector((-.58,-.40,-.63)).to_track_quat('-Z','Y').to_euler()

# A small compositing vignette matches the source without obscuring its geography.
scene.use_nodes=True
nt=scene.node_tree;nt.nodes.clear();layer=nt.nodes.new('CompositorNodeRLayers');out=nt.nodes.new('CompositorNodeComposite')
fade=nt.nodes.new('CompositorNodeMixRGB');fade.blend_type='MULTIPLY';fade.inputs[0].default_value=1
nt.links.new(layer.outputs['Image'],fade.inputs[1]);nt.links.new(fade.outputs[0],out.inputs['Image'])
for t,value in [(0,0),(2,1),(177,1),(180,0)]:
    fade.inputs[2].default_value=(value,value,value,1);fade.inputs[2].keyframe_insert(data_path='default_value',frame=round(t*30)+1)
linear_animation(nt)
scene['source_reference']='reference/source.mp4'
scene['reconstruction']='New procedural parcels and original house meshes; only Notre Dame and Eiffel reused.'
scene['timeline_seconds']=180
scene['native_render_fps']=30
scene['building_records']=len(data['buildings'])
scene['tree_records']=len(forest)
scene.frame_set(2401)
scene.render.filepath=str(ROOT/'output/frames/frame_')
(ROOT/'output').mkdir(exist_ok=True)
(ROOT/'review').mkdir(exist_ok=True)
(ROOT/'review/landmark-audit.json').write_text(json.dumps(landmark_audit,indent=2))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'output/paris_reference_rebuild.blend'),compress=True)
print('SCENE_SAVED',flush=True)
if OPT.preview:
    scene.render.resolution_x=OPT.width;scene.render.resolution_y=round(OPT.width*9/16)
    for t in OPT.preview:
        scene.frame_set(round(t*30)+1)
        scene.render.filepath=str(ROOT/f'review/rebuild-{t:06.2f}.png')
        bpy.ops.render.render(write_still=True)
        print('PREVIEW_COMPLETE',t,flush=True)
