"""Render a contact sheet of all procedural kits (run: blender -b --python preview_kits.py -- out.png)."""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kits

out = sys.argv[sys.argv.index("--") + 1]
scene = bpy.context.scene
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)

root = bpy.data.collections.new("KITS"); scene.collection.children.link(root)
k = kits.build_all_kits(root)
trees = kits.build_trees(root)
import json
fp = {era: [[float(o["footprint_w"]), float(o["footprint_d"]), float(o.dimensions.z)] for o in objs] for era, objs in k.items()}
json.dump(fp, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "kit_footprints.json"), "w"), indent=1)

# lay out on a grid: one row per era
row_y = 0
for era in kits.ERA_NAMES + ["trees"]:
    objs = trees if era == "trees" else k[era]
    x = 0
    for ob in objs:
        w = max(ob.dimensions.x, ob.dimensions.y) + 6
        ob.location = (x + w / 2, row_y, 0)
        x += w
    row_y -= 60
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1800; scene.render.resolution_y = 1500
w = bpy.data.worlds.new("W"); scene.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
bg = nt.nodes.new("ShaderNodeBackground"); outn = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(bg.outputs[0], outn.inputs[0]); bg.inputs[0].default_value = (0.75, 0.8, 0.85, 1)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 4; sun.rotation_euler = (math.radians(45), 0, math.radians(-40))
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 900; cam.data.clip_end = 5000
cam.location = (350, -330 - 400, 600)
cam.rotation_euler = ((cam.location - Vector((350, -330, 0))).to_track_quat('Z', 'Y').to_euler())
ground = bpy.data.objects.new("G", bpy.data.meshes.new("G")); scene.collection.objects.link(ground)
import bmesh
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1200); bm.to_mesh(ground.data); bm.free()
ground.location = (350, -330, -0.05)
ground.data.materials.append(kits.material("ground_preview", (0.30, 0.36, 0.18)))
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("KITS", {e: len(v) for e, v in k.items()}, "trees", len(trees))
