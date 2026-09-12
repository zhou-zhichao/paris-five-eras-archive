"""Render an oblique preview of one or more GLB files (flat vertex colours) to PNG.

usage: blender -b --python preview_glb.py -- model1.glb [model2.glb ...] out.png
Each model is laid out left-to-right; a 10 m grid ground helps judge scale.
"""
import bpy, sys, os, math
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out = args[-1]; files = args[:-1]
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

x = 0.0
maxh = 1.0
for f in files:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(f))
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in new:
        me = o.data
        m = bpy.data.materials.new("flat_" + o.name); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear(); bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); outn = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(bsdf.outputs[0], outn.inputs[0])
        attr = nt.nodes.new("ShaderNodeVertexColor"); attr.layer_name = me.color_attributes[0].name if me.color_attributes else "Color"
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = 0.9
        me.materials.clear(); me.materials.append(m)
        for p in me.polygons: p.use_smooth = False
        w = o.dimensions.x
        o.location.x = x + w / 2
        x += w + 20
        maxh = max(maxh, o.dimensions.z)
        print(f"[preview] {os.path.basename(f)} dims x={o.dimensions.x:.1f} y={o.dimensions.y:.1f} z={o.dimensions.z:.1f} tris={len(me.polygons)}")
total_w = max(x, 30)
# ground with grid
gm = bpy.data.materials.new("ground"); gm.use_nodes = True
nt = gm.node_tree; nt.nodes.clear(); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); outn = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(b.outputs[0], outn.inputs[0])
tc = nt.nodes.new("ShaderNodeTexCoord"); ch = nt.nodes.new("ShaderNodeTexChecker"); ch.inputs["Scale"].default_value = 0.1
ch.inputs[1].default_value = (0.32, 0.40, 0.22, 1); ch.inputs[2].default_value = (0.36, 0.44, 0.25, 1)
nt.links.new(tc.outputs["Object"], ch.inputs["Vector"]); nt.links.new(ch.outputs["Color"], b.inputs["Base Color"])
bpy.ops.mesh.primitive_plane_add(size=1); g = bpy.context.object; g.scale = (total_w * 2, total_w * 2, 1); g.location = (total_w / 2, 0, -0.05)
g.data.materials.append(gm)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 40; cam.data.clip_end = 100000
center = Vector((total_w / 2, 0, maxh * 0.35))
dist = max(total_w, maxh * 1.6) * 1.35
cam.location = center + Vector((-0.35, -0.85, 0.55)).normalized() * dist
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 4; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
w = bpy.data.worlds.new("W"); scene.world = w; w.use_nodes = True; wn = w.node_tree; wn.nodes.clear(); bgn = wn.nodes.new("ShaderNodeBackground"); wo = wn.nodes.new("ShaderNodeOutputWorld"); wn.links.new(bgn.outputs[0], wo.inputs[0]); bgn.inputs[0].default_value = (0.7, 0.75, 0.8, 1)
scene.render.engine = 'BLENDER_EEVEE_NEXT'; scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 1200; scene.render.resolution_y = 800
scene.view_settings.view_transform = 'Standard'
scene.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
print("[preview] wrote", out)
