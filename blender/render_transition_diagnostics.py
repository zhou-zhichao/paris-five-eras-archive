from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

camera_data = bpy.data.cameras.new("Transition_Diagnostic_Camera")
camera = bpy.data.objects.new("Transition_Diagnostic_Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.data.type = "ORTHO"

target = Vector((0.0, 0.0, 0.0))
camera.location = target + Vector((-28.0, -38.0, 42.0))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.ortho_scale = 31.0

scene = bpy.context.scene
scene.render.resolution_percentage = 70
scene.render.image_settings.file_format = "PNG"
for frame in (165, 205, 245, 285):
    scene.frame_set(frame)
    scene.render.filepath = str(OUTPUT_DIR / f"transition_roman_medieval_{frame}.png")
    bpy.ops.render.render(write_still=True)
