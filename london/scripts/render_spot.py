"""Render a close-up of a point at a given frame with a temporary camera (QA).
usage: blender -b cache/london.blend --python scripts/render_spot.py -- --x 1560 --y -600 --frame 4981 --width 900 --out spot.png [--pitch 50]
"""
import bpy, math, os, sys
ARGS = sys.argv[sys.argv.index("--") + 1:]
def arg(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d
x, y = float(arg("--x", "0")), float(arg("--y", "0"))
frame = int(arg("--frame", "4981")); width = float(arg("--width", "800")); pitch = math.radians(float(arg("--pitch", "50")))
heading = math.radians(float(arg("--heading", "68")))
out = os.path.abspath(arg("--out", "spot.png"))
scene = bpy.context.scene
scene.frame_set(frame)
for ob in bpy.data.objects:
    if ob.name.startswith("BRH_") or ob.name.startswith("BR_"):
        if "tower_bridge" in ob.name or "london_bridge" in ob.name:
            print("[spot]", ob.name, "loc", tuple(round(c, 1) for c in ob.matrix_world.translation), "scale", tuple(round(c, 3) for c in ob.scale),
                  "hide_render", ob.hide_render, "dims", tuple(round(c, 1) for c in ob.dimensions))
cam = scene.camera
cam.animation_data_clear()
for c in list(cam.constraints):
    cam.constraints.remove(c)
lens = 35.0
hf = 2 * math.tan(math.atan(18 / lens))
dist = width / hf
cx = x - math.cos(heading) * dist * math.cos(pitch); cy = y - math.sin(heading) * dist * math.cos(pitch); cz = dist * math.sin(pitch)
cam.location = (cx, cy, cz)
from mathutils import Vector
cam.rotation_euler = (Vector((x, y, 0)) - Vector((cx, cy, cz))).to_track_quat('-Z', 'Y').to_euler()
scene.render.resolution_x = 1600; scene.render.resolution_y = 900; scene.eevee.taa_render_samples = 16
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("[spot] wrote", out)
