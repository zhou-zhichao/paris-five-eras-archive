from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills" / "landmark_v6"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

camera_data = bpy.data.cameras.new("Eiffel_Diagnostic_Camera")
camera = bpy.data.objects.new("Eiffel_Diagnostic_Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.data.type = "ORTHO"


def render_view(target, ortho_scale, filename, offset):
    scene = bpy.context.scene
    scene.frame_set(748)
    target_vector = Vector(target)
    camera.location = target_vector + Vector(offset)
    camera.rotation_euler = (target_vector - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = ortho_scale
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 85
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT_DIR / filename)
    bpy.ops.render.render(write_still=True)


render_view((-40.6, 3.0, 3.4), 20.0, "01_eiffel_district_rebuilt.png", (-16.0, -21.0, 23.0))
render_view((-40.6, 6.0, 3.65), 13.0, "02_eiffel_close_rebuilt.png", (-8.0, -10.0, 10.0))
