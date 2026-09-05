from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills" / "building_details_v1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


camera_data = bpy.data.cameras.new("Building_Detail_Diagnostic_Camera")
camera = bpy.data.objects.new("Building_Detail_Diagnostic_Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.data.type = "ORTHO"


def render_view(frame, target, ortho_scale, filename, offset):
    scene = bpy.context.scene
    scene.frame_set(frame)
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


shared_target = (0.0, 5.3, 0.28)
shared_offset = (-8.0, -11.0, 10.0)

render_view(145, shared_target, 7.2, "01_roman_facades.png", shared_offset)
render_view(300, shared_target, 7.2, "02_medieval_facades.png", shared_offset)
render_view(450, shared_target, 7.2, "03_royal_facades.png", shared_offset)
render_view(600, shared_target, 7.2, "04_haussmann_facades.png", shared_offset)
render_view(748, shared_target, 7.2, "05_modern_facades.png", shared_offset)
render_view(300, (0.0, 0.15, 0.3), 5.8, "06_medieval_island_facades.png", (-7.0, -9.0, 8.5))
