"""Render frames from the built scene.

usage: blender -b cache/paris_replica.blend --python render.py -- --out renders/preview --start 1 --end 5400 --step 60
       [--res 1280x720] [--samples 16] [--frames 1,300,900]  (explicit frame list)
"""
import bpy, os, sys, time

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default

out = os.path.abspath(arg("--out", "renders/preview"))
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
res = arg("--res", None)
if res:
    w, h = res.split("x"); scene.render.resolution_x = int(w); scene.render.resolution_y = int(h)
scene.eevee.taa_render_samples = int(arg("--samples", "24"))
frames = arg("--frames", None)
if frames:
    frame_list = [int(f) for f in frames.split(",")]
else:
    s, e, st = int(arg("--start", "1")), int(arg("--end", str(scene.frame_end))), int(arg("--step", "1"))
    frame_list = list(range(s, e + 1, st))
t0 = time.time()
for i, f in enumerate(frame_list):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out, f"frame_{f:05d}.png")
    if os.path.exists(scene.render.filepath) and "--force" not in ARGS:
        continue
    bpy.ops.render.render(write_still=True)
    el = time.time() - t0
    print(f"[render] {i+1}/{len(frame_list)} frame {f}  {el/(i+1):.1f}s/frame  eta {el/(i+1)*(len(frame_list)-i-1)/60:.1f} min", flush=True)
print("[render] done", out)
