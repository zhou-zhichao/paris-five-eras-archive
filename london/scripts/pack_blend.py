"""Pack external images into the blend and save a self-contained copy for the render server.

usage: blender -b cache/paris_replica.blend --python pack_blend.py -- --out cache/paris_replica_packed.blend
"""
import bpy, os, sys, json

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(ARGS[ARGS.index("--out") + 1]) if "--out" in ARGS else bpy.data.filepath.replace(".blend", "_packed.blend")
missing = [im.name for im in bpy.data.images if im.source == 'FILE' and im.packed_file is None and not os.path.exists(bpy.path.abspath(im.filepath))]
if missing:
    raise SystemExit(f"missing images: {missing}")
bpy.ops.file.pack_all()
scene = bpy.context.scene
scene.render.use_persistent_data = False    # safer across many worker processes
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
info = {"out": out, "bytes": os.path.getsize(out), "images": [(im.name, im.packed_file is not None) for im in bpy.data.images],
        "frames": [scene.frame_start, scene.frame_end], "res": [scene.render.resolution_x, scene.render.resolution_y],
        "objects": len(bpy.data.objects)}
print("PACK_SUMMARY=" + json.dumps(info))
