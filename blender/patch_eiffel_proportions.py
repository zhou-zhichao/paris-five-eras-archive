import sys
from pathlib import Path

import bpy


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_scene import PHASE_FRAMES, animate_layer, populate_eiffel


root = bpy.data.objects["Landmark_Eiffel_Tower"]
for child in list(root.children):
    mesh = child.data if child.type == "MESH" else None
    bpy.data.objects.remove(child, do_unlink=True)
    if mesh is not None and mesh.users == 0:
        bpy.data.meshes.remove(mesh)

material = bpy.data.materials["Landmark_Metal"]
populate_eiffel(root, material)
animate_layer(root, PHASE_FRAMES[4] + 6, duration=110)
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
