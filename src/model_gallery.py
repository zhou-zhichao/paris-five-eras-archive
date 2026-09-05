"""Render the newly authored building families for close visual inspection."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from mesh_assets import Mesh, palette, house, MATERIALS
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU'
ids=palette()
names=['ROMAN','MEDIEVAL','LIMESTONE','MANSARD','SUBURBAN','MODERN']
for kind in range(6):
    x=(kind%3)*9-9;y=-(kind//3)*8
    base=Mesh();base.box(x,y,-.25,8.2,6.9,.25,ids['sand']);base.object(names[kind]+' model plinth')
    for variant,dx,dy in [(0,-1.9,1),(5,.2,1),(11,2.3,1),(2,-1.8,-1.1),(7,.3,-1.1),(9,2.4,-1.1)]:
        ob=house(kind,variant,ids).object(names[kind]+f' {variant}')
        ob.location=(x+dx,y+dy,0);ob.scale=(1.7,1.8,[1.1,1.8,2.4,2.7,1.5,3.2][kind])
    text=bpy.data.curves.new(names[kind],'FONT');text.body=names[kind];text.size=.65;text.align_x='CENTER';text.extrude=.003
    ob=bpy.data.objects.new(names[kind]+' label',text);s.collection.objects.link(ob);ob.location=(x,y-3,.04)
    text.materials.append(MATERIALS[ids['timber']])
ground=Mesh();ground.box(0,-3,-.55,200,200,.2,ids['lawn']);ground.object('Gallery background')
s.world=bpy.data.worlds.new('Gallery world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.6,.7,.8,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.4
light=bpy.data.lights.new('Sun','SUN');light.energy=3;light.angle=.11
ob=bpy.data.objects.new('Sun',light);s.collection.objects.link(ob);ob.rotation_euler=Vector((-.6,-.4,-.8)).to_track_quat('-Z','Y').to_euler()
c=bpy.data.cameras.new('Inspection camera');ob=bpy.data.objects.new('Inspection camera',c);s.collection.objects.link(ob);s.camera=ob
target=Vector((0,-3,0));ob.location=(0,-31,37);ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();c.type='ORTHO';c.ortho_scale=31
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
s.render.resolution_x=1920;s.render.resolution_y=1280;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'review/original-building-library.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'output/original_building_library.blend'),compress=True)
bpy.ops.render.render(write_still=True)
