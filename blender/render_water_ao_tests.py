import argparse
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def render(scene, path):
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def stable_material():
    material = bpy.data.materials.new("Water_Stable_AO_Test")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.08, 0.36, 0.46, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.22
    bsdf.inputs["IOR"].default_value = 1.333
    bsdf.inputs["Specular IOR Level"].default_value = 0.55
    bsdf.inputs["Coat Weight"].default_value = 0.24
    bsdf.inputs["Coat Roughness"].default_value = 0.15
    output = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return material


def main():
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1470)
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_motion_blur = False
    scene.eevee.taa_render_samples = 24

    gtao_state = scene.eevee.use_gtao
    scene.eevee.use_gtao = False
    render(scene, output_dir / "01_current_no_gtao.png")

    seine = bpy.data.objects["Seine"]
    original_material = seine.data.materials[0]
    seine.data.materials.clear()
    seine.data.materials.append(stable_material())
    render(scene, output_dir / "02_stable_no_gtao.png")
    seine.data.materials.clear()
    seine.data.materials.append(original_material)
    scene.eevee.use_gtao = gtao_state

    shadows_state = scene.eevee.use_shadows
    scene.eevee.use_shadows = False
    render(scene, output_dir / "03_current_no_global_shadows.png")
    scene.eevee.use_shadows = shadows_state


if __name__ == "__main__":
    main()
