"""Render the outro 'blueprint' still from the built scene: the final camera pose,
the landscape reset to the pre-urban state (year -60: fields, trees, river),
a survey grid drawn on the ground and the Greater London boundary as a white outline.

usage: blender -b cache/london.blend --python render_blueprint.py -- --out renders/blueprint.png [--res 2560x1440] [--frame 5150]
"""
import bpy, os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
out = os.path.abspath(arg("--out", "renders/blueprint.png"))
frame = int(arg("--frame", "5150"))
res = arg("--res", None)
scene = bpy.context.scene
if res:
    w, h = res.split("x"); scene.render.resolution_x = int(w); scene.render.resolution_y = int(h)
scene.frame_set(frame)

YEAR = -60.0
for ob in scene.objects:
    if ob.name.startswith(("LMH_", "LM_", "BRH_", "BR_")):
        if ob.animation_data:
            ob.animation_data_clear()
        ob.hide_render = True
        continue
    for mod in ob.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            for it in mod.node_group.interface.items_tree:
                if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.name == "Year":
                    if ob.animation_data:
                        ob.animation_data_clear()
                    mod[it.identifier] = YEAR
                    print("[blueprint] year set on", ob.name, mod[it.identifier])
mat = bpy.data.materials["ground"]
if mat.node_tree.animation_data:
    mat.node_tree.animation_data_clear()
mat.node_tree.nodes["Year"].outputs[0].default_value = YEAR

# survey grid on the ground: mix lines into the base colour + emission
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
base_link = next(l for l in nt.links if l.to_node == bsdf and l.to_socket.name == "Base Color")
base_out = base_link.from_socket
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])


def grid_axis(sock, period, width):
    d = nt.nodes.new("ShaderNodeMath"); d.operation = 'DIVIDE'; d.inputs[1].default_value = period; nt.links.new(sock, d.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath"); fr.operation = 'FRACT'; nt.links.new(d.outputs[0], fr.inputs[0])
    lo = nt.nodes.new("ShaderNodeMath"); lo.operation = 'LESS_THAN'; lo.inputs[1].default_value = width; nt.links.new(fr.outputs[0], lo.inputs[0])
    hi = nt.nodes.new("ShaderNodeMath"); hi.operation = 'GREATER_THAN'; hi.inputs[1].default_value = 1 - width; nt.links.new(fr.outputs[0], hi.inputs[0])
    m = nt.nodes.new("ShaderNodeMath"); m.operation = 'MAXIMUM'; nt.links.new(lo.outputs[0], m.inputs[0]); nt.links.new(hi.outputs[0], m.inputs[1])
    return m.outputs[0]


gx = grid_axis(sep.outputs[0], 300.0, 0.009); gy = grid_axis(sep.outputs[1], 300.0, 0.009)
g = nt.nodes.new("ShaderNodeMath"); g.operation = 'MAXIMUM'; nt.links.new(gx, g.inputs[0]); nt.links.new(gy, g.inputs[1])
mix = nt.nodes.new("ShaderNodeMixRGB"); mix.inputs[2].default_value = (0.45, 0.75, 0.75, 1)
nt.links.new(g.outputs[0], mix.inputs[0]); nt.links.new(base_out, mix.inputs[1])
nt.links.new(mix.outputs[0], bsdf.inputs["Base Color"])
em = nt.nodes.new("ShaderNodeMath"); em.operation = 'MULTIPLY'; em.inputs[1].default_value = 0.5; nt.links.new(g.outputs[0], em.inputs[0])
nt.links.new(em.outputs[0], bsdf.inputs["Emission Strength"]); bsdf.inputs["Emission Color"].default_value = (0.5, 0.85, 0.85, 1)

# Paris boundary outline (white emissive strip following the terrain)
META = json.load(open(os.path.join(HERE, "..", "cache", "scene_meta.json")))
HM = np.load(os.path.join(HERE, "..", "cache", "scene_data.npz"))["hmap"]
TER = META["terrain"]


def sample_h(xs, ys):
    fx = (np.asarray(xs) - TER["x0"]) / TER["step"]; fy = (np.asarray(ys) - TER["y0"]) / TER["step"]
    i = np.clip(fx.astype(int), 0, HM.shape[1] - 2); j = np.clip(fy.astype(int), 0, HM.shape[0] - 2)
    u = fx - i; v = fy - j
    return ((1 - u) * (1 - v) * HM[j, i] + u * (1 - v) * HM[j, i + 1] + (1 - u) * v * HM[j + 1, i] + u * v * HM[j + 1, i + 1])


pts = np.array(META["london"], dtype=np.float32)
# densify so the strip follows hills
dense = []
for a_, b_ in zip(pts[:-1], pts[1:]):
    n_ = max(1, int(np.linalg.norm(b_ - a_) // 60))
    for k in range(n_):
        dense.append(a_ + (b_ - a_) * (k / n_))
dense.append(pts[-1]); pts = np.array(dense, dtype=np.float32)
p0 = pts[:-1]; p1 = pts[1:]
d = p1 - p0; L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
t = d / L; nrm = np.stack([-t[:, 1], t[:, 0]], axis=1)
wdt = 22.0
verts = np.concatenate([p0 - nrm * wdt, p1 - nrm * wdt, p1 + nrm * wdt, p0 + nrm * wdt])
zs = sample_h(verts[:, 0], verts[:, 1]).astype(np.float32) + 4.0
n = len(p0)
faces = np.stack([np.arange(n), np.arange(n) + n, np.arange(n) + 2 * n, np.arange(n) + 3 * n], axis=1)
me = bpy.data.meshes.new("LONDON_OUTLINE")
me.vertices.add(4 * n); me.vertices.foreach_set("co", np.column_stack([verts, zs]).ravel())
me.loops.add(4 * n); me.loops.foreach_set("vertex_index", faces.ravel().astype(np.int32))
me.polygons.add(n); me.polygons.foreach_set("loop_start", np.arange(0, 4 * n, 4, dtype=np.int32)); me.polygons.foreach_set("loop_total", np.full(n, 4, dtype=np.int32))
me.update()
wm = bpy.data.materials.new("outline"); wm.use_nodes = True
b = wm.node_tree.nodes["Principled BSDF"] if "Principled BSDF" in wm.node_tree.nodes else None
if b is None:
    wm.node_tree.nodes.clear(); b = wm.node_tree.nodes.new("ShaderNodeBsdfPrincipled"); o = wm.node_tree.nodes.new("ShaderNodeOutputMaterial"); wm.node_tree.links.new(b.outputs[0], o.inputs[0])
b.inputs["Base Color"].default_value = (0.9, 0.95, 0.9, 1); b.inputs["Emission Color"].default_value = (0.9, 0.95, 0.9, 1); b.inputs["Emission Strength"].default_value = 1.0
me.materials.append(wm)
ob = bpy.data.objects.new("LONDON_OUTLINE", me); scene.collection.objects.link(ob)

scene.eevee.taa_render_samples = 24
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("[blueprint] wrote", out)
