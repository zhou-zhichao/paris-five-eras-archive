"""Render independent material, architecture, and camera checks from the saved scene."""
import bpy
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
s=bpy.context.scene
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'cycles'
s.frame_set(721)
s.render.resolution_x=1280;s.render.resolution_y=720
if mode=='close':
    s.camera.animation_data_clear();s.camera.data.animation_data_clear()
    target=Vector((20,-72,0));s.camera.location=target+Vector((-28,-40,40))
    s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()
    s.camera.data.type='ORTHO';s.camera.data.ortho_scale=65
    s.camera.data.clip_start=.1;s.camera.data.dof.use_dof=False
    for ob in s.objects:
        if ob.parent==s.camera:ob.hide_render=True
    s.render.filepath=str(ROOT/'review/houses-close-eevee.png')
else:
    s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
    for d in p.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU'
    s.render.filepath=str(ROOT/'review/roman-cycles.png')
bpy.ops.render.render(write_still=True)
print('CAMERA',tuple(s.camera.location),tuple(s.camera.rotation_euler),s.camera.data.ortho_scale,flush=True)
