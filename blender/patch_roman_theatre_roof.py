import importlib.util
from pathlib import Path

import bpy


SCRIPT_PATH = Path(__file__).with_name("build_scene.py")
BLEND_PATH = Path(__file__).with_name("paris_5_eras.blend")

spec = importlib.util.spec_from_file_location("paris_build_scene", SCRIPT_PATH)
scene_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scene_builder)

old_roof = bpy.data.objects.get("Roman_Theatre_Stage_Roof")
if old_roof is not None:
    old_mesh = old_roof.data
    bpy.data.objects.remove(old_roof, do_unlink=True)
    if old_mesh is not None and old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

root = bpy.data.objects["Landmark_Roman_Theatre"]
roof_material = bpy.data.materials["Roof_Terracotta"]
scene_builder.add_mansard_roof(
    "Roman_Theatre_Stage_Roof",
    (6.4, 6.25 + 0.95 * 0.74, 0.46),
    2.15,
    0.36,
    0.16,
    roof_material,
    root,
)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
