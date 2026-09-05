import sys
from pathlib import Path

import bpy
from mathutils import Vector


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_scene import (
    clear_scene,
    configure_scene,
    create_land,
    make_material,
    new_landmark_root,
    populate_eiffel,
    setup_lighting,
)


clear_scene()
configure_scene()

land = make_material("Test_Land", (0.245, 0.315, 0.155), roughness=0.8)
iron = make_material("Test_Eiffel_Iron", (0.27, 0.085, 0.022), metallic=0.42, roughness=0.3, coat_weight=0.2)
detail = make_material("Test_Eiffel_Detail", (0.48, 0.19, 0.052), metallic=0.32, roughness=0.34, coat_weight=0.15)

create_land(land)
root = new_landmark_root("Test_Eiffel")
populate_eiffel(root, iron, detail)
setup_lighting()

camera_data = bpy.data.cameras.new("Eiffel_Test_Camera")
camera = bpy.data.objects.new("Eiffel_Test_Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.data.type = "ORTHO"

scene = bpy.context.scene
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 90
scene.render.image_settings.file_format = "PNG"
output_dir = PROJECT_DIR / "stills" / "eiffel_rebuild"
output_dir.mkdir(parents=True, exist_ok=True)


def render_view(filename, offset, ortho_scale):
    target = Vector((0.0, 0.0, 3.65))
    camera.location = target + Vector(offset)
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = ortho_scale
    scene.render.filepath = str(output_dir / filename)
    bpy.ops.render.render(write_still=True)


render_view("01_model_three_quarter.png", (-8.5, -12.5, 5.0), 9.8)
render_view("02_model_front.png", (0.0, -14.0, 3.2), 9.2)
