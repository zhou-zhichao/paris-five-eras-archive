from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills"


def render_view(frame, target, ortho_scale, filename, offset=(-18.0, -24.0, 28.0)):
    scene = bpy.context.scene
    scene.frame_set(frame)
    camera.location = Vector(target) + Vector(offset)
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT_DIR / filename)
    bpy.ops.render.render(write_still=True)


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
camera_data = bpy.data.cameras.new("Diagnostic_Camera")
camera = bpy.data.objects.new("Diagnostic_Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
render_view(150, (0.0, 0.0, 0.0), 24.0, "12_roman_state_v2.png", (-24.0, -32.0, 36.0))
render_view(150, (6.4, 6.25, 0.0), 8.5, "13_roman_theatre_v2.png", (-12.0, -16.0, 19.0))
render_view(295, (-1.0, 1.5, 0.0), 35.0, "14_medieval_state_v2.png", (-32.0, -43.0, 48.0))
render_view(440, (-2.0, 3.0, 0.0), 48.0, "15_royal_state_v2.png", (-38.0, -52.0, 58.0))
