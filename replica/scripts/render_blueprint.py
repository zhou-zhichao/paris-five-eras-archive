"""Render the outro 'blueprint' still: same camera as the last frame, city hidden,
ground turned into a dark green plane with a white survey grid, river and Paris
boundary drawn as white outlines.

usage: blender -b cache/paris_replica.blend --python render_blueprint.py -- --out renders/blueprint.png [--res 2560x1440] [--frame 5100]
"""
import bpy, os, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
out = os.path.abspath(arg("--out", "renders/blueprint.png"))
frame = int(arg("--frame", "5100"))
res = arg("--res", None)
scene = bpy.context.scene
if res:
    w, h = res.split("x"); scene.render.resolution_x = int(w); scene.render.resolution_y = int(h)
scene.frame_set(frame)

# hide everything except terrain + water
for ob in scene.objects:
    if ob.type in ('MESH', 'EMPTY') and ob.name not in ("TERRAIN", "GROUND_FAR", "WATER", "CANALS"):
        ob.hide_render = True
        if ob.animation_data:
            ob.animation_data_clear()
        ob.hide_render = True

# ground: flat dark green + grid lines
mat = bpy.data.materials["ground"]
nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(bsdf.outputs[0], outn.inputs[0])
bsdf.inputs["Roughness"].default_value = 1.0; bsdf.inputs["Specular IOR Level"].default_value = 0.0
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
def grid_axis(sock, period, width):
    d = nt.nodes.new("ShaderNodeMath"); d.operation = 'DIVIDE'; d.inputs[1].default_value = period; nt.links.new(sock, d.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath"); fr.operation = 'FRACT'; nt.links.new(d.outputs[0], fr.inputs[0])
    # line where fract < width or > 1-width
    lo = nt.nodes.new("ShaderNodeMath"); lo.operation = 'LESS_THAN'; lo.inputs[1].default_value = width; nt.links.new(fr.outputs[0], lo.inputs[0])
    hi = nt.nodes.new("ShaderNodeMath"); hi.operation = 'GREATER_THAN'; hi.inputs[1].default_value = 1 - width; nt.links.new(fr.outputs[0], hi.inputs[0])
    m = nt.nodes.new("ShaderNodeMath"); m.operation = 'MAXIMUM'; nt.links.new(lo.outputs[0], m.inputs[0]); nt.links.new(hi.outputs[0], m.inputs[1])
    return m.outputs[0]
gx = grid_axis(sep.outputs[0], 500.0, 0.012); gy = grid_axis(sep.outputs[1], 500.0, 0.012)
g = nt.nodes.new("ShaderNodeMath"); g.operation = 'MAXIMUM'; nt.links.new(gx, g.inputs[0]); nt.links.new(gy, g.inputs[1])
mix = nt.nodes.new("ShaderNodeMixRGB"); mix.inputs[1].default_value = (0.06, 0.10, 0.03, 1); mix.inputs[2].default_value = (0.75, 0.80, 0.70, 1)
nt.links.new(g.outputs[0], mix.inputs[0]); nt.links.new(mix.outputs[0], bsdf.inputs["Base Color"])
em = nt.nodes.new("ShaderNodeMath"); em.operation = 'MULTIPLY'; em.inputs[1].default_value = 0.6; nt.links.new(g.outputs[0], em.inputs[0])
nt.links.new(em.outputs[0], bsdf.inputs["Emission Strength"]); bsdf.inputs["Emission Color"].default_value = (0.8, 0.85, 0.8, 1)

# water: light outline look
wm = bpy.data.materials["water"]
for n in wm.node_tree.nodes:
    if n.type == 'BSDF_PRINCIPLED':
        n.inputs["Base Color"].default_value = (0.10, 0.30, 0.34, 1)
        n.inputs["Emission Color"].default_value = (0.35, 0.65, 0.70, 1); n.inputs["Emission Strength"].default_value = 0.5

scene.eevee.taa_render_samples = 24
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("[blueprint] wrote", out)
