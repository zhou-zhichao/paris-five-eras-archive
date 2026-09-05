from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills" / "landmark_v4"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


camera_data = bpy.data.cameras.new("Landmark_Diagnostic_Camera")
camera = bpy.data.objects.new("Landmark_Diagnostic_Camera", camera_data)
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
    scene.render.resolution_percentage = 70
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT_DIR / filename)
    bpy.ops.render.render(write_still=True)


render_view(148, (1.4, -8.1, 0.0), 8.0, "01_roman_forum_land_clearance.png", (-10.0, -13.0, 15.0))
render_view(300, (0.15, 0.25, 0.25), 4.6, "02_notre_dame_close.png", (-6.5, -8.5, 9.5))
render_view(300, (0.15, 0.25, 0.38), 3.8, "02b_notre_dame_west_facade.png", (-7.0, 4.4, 8.5))
render_view(748, (-40.6, 3.0, 0.3), 15.5, "03_eiffel_district.png", (-16.0, -21.0, 23.0))
render_view(748, (-40.6, 6.0, 2.2), 7.8, "04_eiffel_close.png", (-8.0, -10.0, 11.0))
render_view(600, (-40.2, 23.2, 0.45), 4.2, "05_arc_close.png", (-6.0, -8.0, 8.5))
render_view(748, (-45.0, 28.5, 0.8), 8.5, "06_la_defense_close.png", (-10.0, -13.0, 14.0))

transition_target = (0.0, 0.5, 0.0)
for frame in (178, 214, 250, 286):
    render_view(
        frame,
        transition_target,
        30.0,
        f"transition_roman_medieval_{frame}.png",
        (-27.0, -37.0, 41.0),
    )
