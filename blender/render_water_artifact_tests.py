import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def render(scene, output):
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)


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

    outputs = []
    output = output_dir / "01_current.png"
    render(scene, output)
    outputs.append(str(output))

    lights = [obj.data for obj in bpy.data.objects if obj.type == "LIGHT"]
    shadow_states = [light.use_shadow for light in lights]
    for light in lights:
        light.use_shadow = False
    output = output_dir / "02_no_light_shadows.png"
    render(scene, output)
    outputs.append(str(output))
    for light, state in zip(lights, shadow_states):
        light.use_shadow = state

    probe = bpy.data.objects.get("Seine_Planar_Reflection_Probe")
    probe_state = probe.hide_render if probe else None
    if probe:
        probe.hide_render = True
    output = output_dir / "03_no_planar_probe.png"
    render(scene, output)
    outputs.append(str(output))
    if probe:
        probe.hide_render = probe_state

    raytracing_state = scene.eevee.use_raytracing
    scene.eevee.use_raytracing = False
    output = output_dir / "04_no_raytracing.png"
    render(scene, output)
    outputs.append(str(output))
    scene.eevee.use_raytracing = raytracing_state

    riverbank = bpy.data.objects.get("Seine_Riverbank")
    riverbank_state = riverbank.hide_render if riverbank else None
    if riverbank:
        riverbank.hide_render = True
    output = output_dir / "05_no_riverbank.png"
    render(scene, output)
    outputs.append(str(output))
    if riverbank:
        riverbank.hide_render = riverbank_state

    land = bpy.data.objects.get("Land")
    land_state = land.hide_render if land else None
    if land:
        land.hide_render = True
    output = output_dir / "06_no_land.png"
    render(scene, output)
    outputs.append(str(output))
    if land:
        land.hide_render = land_state

    margin_objects = [
        bpy.data.objects.get("Ile_de_la_Cite_Margin"),
        bpy.data.objects.get("Ile_Saint_Louis_Margin"),
    ]
    margin_objects = [obj for obj in margin_objects if obj]
    margin_states = [obj.hide_render for obj in margin_objects]
    for obj in margin_objects:
        obj.hide_render = True
    output = output_dir / "07_no_island_margins.png"
    render(scene, output)
    outputs.append(str(output))
    for obj, state in zip(margin_objects, margin_states):
        obj.hide_render = state

    seine = bpy.data.objects.get("Seine")
    original_material = seine.data.materials[0] if seine and seine.data.materials else None
    emission_material = bpy.data.materials.new("Water_Artifact_Emission_Test")
    emission_material.use_nodes = True
    emission_nodes = emission_material.node_tree.nodes
    emission_nodes.clear()
    emission = emission_nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.08, 0.42, 0.52, 1.0)
    emission.inputs["Strength"].default_value = 1.0
    output_node = emission_nodes.new("ShaderNodeOutputMaterial")
    emission_material.node_tree.links.new(emission.outputs["Emission"], output_node.inputs["Surface"])
    if seine:
        seine.data.materials.clear()
        seine.data.materials.append(emission_material)
    output = output_dir / "08_emission_only_water.png"
    render(scene, output)
    outputs.append(str(output))
    if seine:
        seine.data.materials.clear()
        if original_material:
            seine.data.materials.append(original_material)

    stable_material = bpy.data.materials.new("Water_Artifact_Stable_Principled_Test")
    stable_material.use_nodes = True
    stable_nodes = stable_material.node_tree.nodes
    stable_nodes.clear()
    stable_bsdf = stable_nodes.new("ShaderNodeBsdfPrincipled")
    stable_bsdf.inputs["Base Color"].default_value = (0.08, 0.36, 0.46, 1.0)
    stable_bsdf.inputs["Roughness"].default_value = 0.22
    stable_bsdf.inputs["Metallic"].default_value = 0.0
    stable_bsdf.inputs["IOR"].default_value = 1.333
    stable_bsdf.inputs["Specular IOR Level"].default_value = 0.55
    stable_bsdf.inputs["Coat Weight"].default_value = 0.24
    stable_bsdf.inputs["Coat Roughness"].default_value = 0.15
    stable_bsdf.inputs["Emission Color"].default_value = (0.025, 0.12, 0.15, 1.0)
    stable_bsdf.inputs["Emission Strength"].default_value = 0.08
    stable_output = stable_nodes.new("ShaderNodeOutputMaterial")
    stable_material.node_tree.links.new(stable_bsdf.outputs["BSDF"], stable_output.inputs["Surface"])
    if seine:
        seine.data.materials.clear()
        seine.data.materials.append(stable_material)
    output = output_dir / "09_stable_principled_water.png"
    render(scene, output)
    outputs.append(str(output))
    if seine:
        seine.data.materials.clear()
        if original_material:
            seine.data.materials.append(original_material)

    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
