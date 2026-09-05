import sys
from pathlib import Path

import bpy
from mathutils import Vector


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
SOURCE_GLB = PROJECT_DIR / "assets" / "models" / "notre-dame-clean-200k.glb"
OUTPUT_DIR = PROJECT_DIR / "stills" / "notre_dame_glb"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_scene import add_cube, clear_scene, configure_scene, make_material, setup_lighting


clear_scene()
configure_scene()
bpy.ops.import_scene.gltf(filepath=str(SOURCE_GLB))

ground_material = make_material("GLB_Preview_Ground", (0.245, 0.315, 0.155), roughness=0.8)
add_cube("GLB_Preview_Ground", (0.0, 0.0, -1.035), (5.0, 5.0, 0.05), ground_material)
setup_lighting()

camera_data = bpy.data.cameras.new("GLB_Preview_Camera")
camera = bpy.data.objects.new("GLB_Preview_Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.data.type = "ORTHO"

scene = bpy.context.scene
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 80
scene.render.image_settings.file_format = "PNG"


def render_view(filename, target, offset, ortho_scale):
    target_vector = Vector(target)
    camera.location = target_vector + Vector(offset)
    camera.rotation_euler = (target_vector - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = ortho_scale
    scene.render.filepath = str(OUTPUT_DIR / filename)
    bpy.ops.render.render(write_still=True)


render_view("01_three_quarter.png", (0.0, 0.0, -0.05), (-3.5, -5.0, 3.2), 2.85)
render_view("02_front.png", (0.0, 0.0, -0.05), (0.0, -5.0, 1.2), 2.65)
render_view("03_aerial.png", (0.0, 0.0, -0.05), (-4.5, -6.0, 6.0), 3.0)
