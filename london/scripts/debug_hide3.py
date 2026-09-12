"""Render frame with WATER+TERRAIN plus ONE extra group at a time (complement of debug_hide).
usage: blender -b cache/london_sub2.blend --python scripts/debug_hide3.py -- 3601 out_dir
"""
import bpy, sys, os
args = sys.argv[sys.argv.index("--") + 1:]
frame = int(args[0]); out = os.path.abspath(args[1]); os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(frame); scene.render.use_persistent_data = False
scene.render.resolution_x = 800; scene.render.resolution_y = 450; scene.eevee.taa_render_samples = 6
scene.camera.data.lens = 120
base = {"WATER", "TERRAIN", "Camera", "CamTarget", "Sun"}
groups = {
    "city": [o.name for o in bpy.data.objects if o.name.startswith("CITY_")],
    "trees": ["TREES"],
    "groundfar": ["GROUND_FAR"],
    "walls": ["WALLS"],
    "roads": ["ROADS", "RAIL"],
    "waterhist_canals": ["WATER_HIST", "CANALS"],
}
for name, extra in groups.items():
    keep = base | set(extra)
    for o in bpy.data.objects:
        o.hide_render = o.name not in keep
    scene.render.filepath = os.path.join(out, f"plus_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("[dbg] rendered", name, flush=True)
