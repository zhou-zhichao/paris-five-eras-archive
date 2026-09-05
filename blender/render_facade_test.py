import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_scene import (
    add_house_geometry,
    clear_scene,
    configure_scene,
    create_land,
    make_material,
    mesh_object,
    setup_lighting,
)


clear_scene()
configure_scene()

land = make_material("Test_Land", (0.245, 0.315, 0.155), roughness=0.8)
wall_a = make_material("Test_Wall_A", (0.64, 0.51, 0.36), roughness=0.48)
wall_b = make_material("Test_Wall_B", (0.76, 0.67, 0.51), roughness=0.46)
wall_c = make_material("Test_Wall_C", (0.53, 0.49, 0.39), roughness=0.52)
roof_red = make_material("Test_Roof_Red", (0.43, 0.075, 0.024), roughness=0.18)
roof_slate = make_material("Test_Roof_Slate", (0.14, 0.165, 0.16), roughness=0.22)
roof_zinc = make_material("Test_Roof_Zinc", (0.5, 0.48, 0.42), metallic=0.1, roughness=0.2)
wall_brick = make_material("Test_Wall_Brick", (0.5, 0.22, 0.105), roughness=0.54)
wall_ochre = make_material("Test_Wall_Ochre", (0.7, 0.4, 0.19), roughness=0.5)
roof_weathered = make_material("Test_Roof_Weathered", (0.35, 0.17, 0.075), roughness=0.28)
window_dark = make_material("Test_Window_Dark", (0.018, 0.045, 0.052), roughness=0.16, coat_weight=0.32)
window_warm = make_material("Test_Window_Warm", (0.72, 0.34, 0.075), roughness=0.19, coat_weight=0.28)
door = make_material("Test_Door", (0.12, 0.048, 0.018), roughness=0.42)
trim = make_material("Test_Trim", (0.82, 0.73, 0.57), roughness=0.4, coat_weight=0.12)
materials = [
    wall_a,
    wall_b,
    wall_c,
    roof_red,
    roof_slate,
    roof_zinc,
    wall_brick,
    wall_ochre,
    roof_weathered,
    window_dark,
    window_warm,
    door,
    trim,
]

vertices = []
faces = []
material_ids = []
samples = [
    ("roman", -1.3, 0.28, 0.22, 0.3, "gable", 2, 3),
    ("medieval", -0.65, 0.32, 0.25, 0.46, "gable", 6, 3),
    ("royal", 0.0, 0.36, 0.28, 0.58, "mansard", 1, 4),
    ("haussmann", 0.7, 0.42, 0.31, 0.68, "mansard", 1, 5),
    ("modern", 1.48, 0.48, 0.34, 0.78, "flat", 0, 5),
]
for index, (style, x, width, depth, height, roof_style, wall_id, roof_id) in enumerate(samples):
    add_house_geometry(
        vertices,
        faces,
        material_ids,
        x,
        0.0,
        width,
        depth,
        height,
        0.0,
        wall_id,
        roof_id,
        roof_style,
        "standard",
        style,
        random.Random(400 + index),
    )

mesh_object("Facade_Test_Houses", vertices, faces, material_ids, materials)
create_land(land)
setup_lighting()

camera_data = bpy.data.cameras.new("Facade_Test_Camera")
camera = bpy.data.objects.new("Facade_Test_Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.data.type = "ORTHO"
target = Vector((0.1, 0.0, 0.28))
camera.location = target + Vector((-3.5, -5.5, 4.1))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.ortho_scale = 3.8

scene = bpy.context.scene
scene.camera = camera
scene.render.resolution_percentage = 70
scene.render.image_settings.file_format = "PNG"
output = PROJECT_DIR / "stills" / "facade_test.png"
output.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(output)
bpy.ops.render.render(write_still=True)
