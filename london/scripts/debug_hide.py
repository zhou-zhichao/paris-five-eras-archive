"""Render one frame several times with different object groups hidden, to find what covers the river.
usage: blender -b cache/london_sub2.blend --python scripts/debug_hide.py -- 3601 out_dir
"""
import bpy, sys, os
args = sys.argv[sys.argv.index("--") + 1:]
frame = int(args[0]); out = os.path.abspath(args[1]); os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(frame); scene.render.use_persistent_data = False
scene.render.resolution_x = 800; scene.render.resolution_y = 450; scene.eevee.taa_render_samples = 6
scene.camera.data.lens = 120
groups = {
    "all": [],
    "no_waterhist": ["WATER_HIST"],
    "no_roads": ["ROADS", "RAIL"],
    "no_canals": ["CANALS"],
    "no_landmarks": [o.name for o in bpy.data.objects if o.name.startswith(("LM_", "LMH_", "BR_", "BRH_"))],
    "no_water": ["WATER"],
}
for name, hide in groups.items():
    for o in bpy.data.objects:
        if o.name in hide:
            o.hide_render = True
    scene.render.filepath = os.path.join(out, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("[dbg] rendered", name, flush=True)
    for o in bpy.data.objects:
        if o.name in hide:
            o.hide_render = False
