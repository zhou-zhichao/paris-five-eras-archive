"""Diagnostics: count evaluated water faces per frame, list water attribute ranges, ray-cast image points.
usage: blender -b cache/london_sub2.blend --python scripts/debug_water.py -- 3601 4981
"""
import bpy, sys, json, os
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["3601"]
scene = bpy.context.scene
HERE = os.path.dirname(os.path.abspath(__file__))
META = json.load(open(os.path.join(HERE, "..", "cache", "scene_meta.json")))
kinds = {}
for w in META["water_tris"]:
    kinds.setdefault(w["kind"], [0, 0]); kinds[w["kind"]][0] += 1; kinds[w["kind"]][1] += len(w["tris"])
print("[dbg] water_tris per kind (polys, tris):", kinds)
empty = [(w["kind"], w["name"], len(w["outer"])) for w in META["water_tris"] if not w["tris"]]
print("[dbg] polygons with NO triangles:", len(empty), empty[:10])

ob = bpy.data.objects["WATER"]
me = ob.data
b = np.zeros(len(me.polygons), dtype=np.float32); d = np.zeros(len(me.polygons), dtype=np.float32)
me.attributes["birth"].data.foreach_get("value", b); me.attributes["death"].data.foreach_get("value", d)
print("[dbg] WATER faces", len(me.polygons), "birth unique", np.unique(b)[:20], "death unique", np.unique(d)[:10])
for f in args:
    scene.frame_set(int(f))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    mod = ob.modifiers["life"]
    yid = [k for k in mod.keys()][0]
    print(f"[dbg] frame {f}: year input {mod[yid]:.1f}, evaluated WATER faces {len(m.polygons)}")
    ev.to_mesh_clear()
    # ray casts from the camera through a few image points (u, v in 0..1 from top-left)
    cam = scene.camera
    from bpy_extras.object_utils import world_to_camera_view
    import mathutils
    for (u, v) in [(0.09, 0.53), (0.08, 0.94), (0.5, 0.5)]:
        # build a ray: use camera frame
        frame = [cam.matrix_world @ p for p in cam.data.view_frame(scene=scene)]
        # view_frame returns 4 corners: (right-top, right-bottom, left-bottom, left-top) in camera space
        tr, br, bl, tl = frame
        p = tl + (tr - tl) * u + (bl - tl) * v
        origin = cam.matrix_world.translation
        direction = (p - origin).normalized()
        hit, loc, nrm, idx, hob, mat = scene.ray_cast(dg, origin, direction, distance=1e6)
        print(f"[dbg]   pixel ({u:.2f},{v:.2f}) -> hit {hit} {hob.name if hob else None} at {tuple(round(c) for c in loc) if hit else None}")
