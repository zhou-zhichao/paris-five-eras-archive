"""Configure the packed v50 scene for a 720p review render."""
import bpy
from pathlib import Path

missing = [image.filepath for image in bpy.data.images if image.source == 'FILE' and not image.packed_file and not Path(bpy.path.abspath(image.filepath)).is_file()]
if missing:
    raise RuntimeError(f'Missing images: {missing}')
if bpy.data.libraries:
    raise RuntimeError('Unexpected linked Blender libraries')
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 3600
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.render.image_settings.compression = 18
scene.eevee.taa_render_samples = 16
scene.render.use_motion_blur = False
print('CONFIGURED_V50_720P', flush=True)
