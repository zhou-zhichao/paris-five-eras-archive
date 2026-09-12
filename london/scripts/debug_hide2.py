"""Render frame with only WATER (+TERRAIN) visible; print terrain z at river points.
usage: blender -b cache/london_sub2.blend --python scripts/debug_hide2.py -- 3601 out_dir
"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
frame = int(args[0]); out = os.path.abspath(args[1]); os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(frame)
scene.render.resolution_x = 800; scene.render.resolution_y = 450; scene.eevee.taa_render_samples = 6
scene.camera.data.lens = 120
ter = bpy.data.objects["TERRAIN"]
# terrain z near river points (world)
pts = [(0, -700), (500, -900), (-1500, -1500), (3000, -400)]
co = np.zeros(len(ter.data.vertices) * 3, dtype=np.float32); ter.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
for x, y in pts:
    d = (co[:, 0] - x) ** 2 + (co[:, 1] - y) ** 2
    i = int(np.argmin(d))
    print(f"[dbg] terrain vertex nearest ({x},{y}): {co[i]}")
w = bpy.data.objects["WATER"]
print("[dbg] WATER location", tuple(w.location), "dims", tuple(w.dimensions), "hide_render", w.hide_render, "materials", [m.name for m in w.data.materials])
mat = w.data.materials[0]
for n in mat.node_tree.nodes:
    if n.type == 'BSDF_PRINCIPLED':
        print("[dbg] water bsdf base colour", tuple(n.inputs["Base Color"].default_value), "linked", n.inputs["Base Color"].is_linked)
keep = {"WATER", "TERRAIN", "Camera", "CamTarget", "Sun"}
for o in bpy.data.objects:
    o.hide_render = o.name not in keep
scene.render.filepath = os.path.join(out, "water_terrain.png"); bpy.ops.render.render(write_still=True)
bpy.data.objects["TERRAIN"].hide_render = True
scene.render.filepath = os.path.join(out, "water_only.png"); bpy.ops.render.render(write_still=True)
print("[dbg] done")
