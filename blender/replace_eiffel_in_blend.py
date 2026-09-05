import sys
from pathlib import Path

import bpy


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_scene import build_eiffel, make_material


def remove_root_and_children(root_name):
    root = bpy.data.objects.get(root_name)
    if root is None:
        return
    for child in list(root.children):
        bpy.data.objects.remove(child, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)


remove_root_and_children("Landmark_Eiffel_Tower")

iron = bpy.data.materials.get("Eiffel_Iron")
if iron is None:
    iron = make_material("Eiffel_Iron", (0.27, 0.085, 0.022), metallic=0.42, roughness=0.3, ior_level=0.66, coat_weight=0.2)

detail = bpy.data.materials.get("Eiffel_Iron_Highlight")
if detail is None:
    detail = make_material("Eiffel_Iron_Highlight", (0.48, 0.19, 0.052), metallic=0.32, roughness=0.34, ior_level=0.62, coat_weight=0.15)

build_eiffel(iron, detail)
bpy.context.scene.frame_set(748)
bpy.ops.wm.save_as_mainfile(filepath=str(SCRIPT_DIR / "paris_5_eras.blend"))
