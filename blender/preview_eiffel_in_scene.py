import sys
from pathlib import Path

import bpy
from mathutils import Vector


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_scene import make_material, new_landmark_root, populate_eiffel


def remove_root_and_children(root_name):
    root = bpy.data.objects.get(root_name)
    if root is None:
        return
    for child in list(root.children):
        bpy.data.objects.remove(child, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)


remove_root_and_children("Landmark_Eiffel_Tower")
iron = make_material("Eiffel_Iron_Preview", (0.27, 0.085, 0.022), metallic=0.42, roughness=0.3, ior_level=0.66, coat_weight=0.2)
detail = make_material("Eiffel_Iron_Highlight_Preview", (0.48, 0.19, 0.052), metallic=0.32, roughness=0.34, ior_level=0.62, coat_weight=0.15)
eiffel_root = new_landmark_root("Landmark_Eiffel_Tower", (-40.6, 6.0, 0.0))
populate_eiffel(eiffel_root, iron, detail)

scene = bpy.context.scene
scene.frame_set(748)
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 50
scene.render.image_settings.file_format = "PNG"
output_dir = PROJECT_DIR / "stills" / "eiffel_rebuild"
output_dir.mkdir(parents=True, exist_ok=True)

main_camera = scene.camera
scene.render.filepath = str(output_dir / "03_scene_main.png")
bpy.ops.render.render(write_still=True)

if "--main-only" in sys.argv:
    raise SystemExit(0)

scene.render.resolution_percentage = 85

camera_data = bpy.data.cameras.new("Eiffel_Scene_Preview_Camera")
camera = bpy.data.objects.new("Eiffel_Scene_Preview_Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.data.type = "ORTHO"
scene.camera = camera


def render_view(filename, target, offset, ortho_scale):
    target_vector = Vector(target)
    camera.location = target_vector + Vector(offset)
    camera.rotation_euler = (target_vector - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = ortho_scale
    scene.render.filepath = str(output_dir / filename)
    bpy.ops.render.render(write_still=True)


render_view("04_scene_close.png", (-40.6, 6.0, 3.4), (-9.0, -12.0, 7.5), 10.8)
render_view("05_scene_district.png", (-40.6, 3.0, 1.5), (-16.0, -21.0, 23.0), 17.5)
scene.camera = main_camera
