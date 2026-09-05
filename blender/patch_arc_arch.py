import sys
from pathlib import Path

import bpy


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_scene import add_arch_ring, set_constant_keyframes


old_arch = bpy.data.objects.get("Arc_Main_Arch_Ring")
if old_arch is not None:
    old_mesh = old_arch.data
    bpy.data.objects.remove(old_arch, do_unlink=True)
    if old_mesh is not None and old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

shadow = bpy.data.objects.get("Arc_Opening_Shadow")
if shadow is not None:
    shadow.location.z = 0.37
    shadow.dimensions.z = 0.5

root = bpy.data.objects["Landmark_Arc_de_Triomphe"]
material = bpy.data.materials["Landmark_Stone"]
arch = add_arch_ring(
    "Arc_Main_Arch_Ring",
    (0.0, -0.287, 0.56),
    0.148,
    0.252,
    0.08,
    material,
    root,
    segments=32,
)
arch.hide_render = True
arch.keyframe_insert(data_path="hide_render", frame=1)
arch.keyframe_insert(data_path="hide_render", frame=467)
arch.hide_render = False
arch.keyframe_insert(data_path="hide_render", frame=468)
set_constant_keyframes(arch, "hide_render")

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
