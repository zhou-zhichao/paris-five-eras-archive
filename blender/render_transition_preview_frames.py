from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "previews" / "transition_v4_frames"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

camera_data = bpy.data.cameras.new("Transition_Preview_Camera")
camera = bpy.data.objects.new("Transition_Preview_Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.data.type = "ORTHO"

target = Vector((0.0, 0.5, 0.0))
camera.location = target + Vector((-27.0, -37.0, 41.0))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.ortho_scale = 30.0

scene = bpy.context.scene
scene.render.resolution_percentage = 45
scene.render.image_settings.file_format = "PNG"
for output_index, frame in enumerate(range(160, 311, 5)):
    scene.frame_set(frame)
    scene.render.filepath = str(OUTPUT_DIR / f"frame_{output_index:04d}.png")
    bpy.ops.render.render(write_still=True)
