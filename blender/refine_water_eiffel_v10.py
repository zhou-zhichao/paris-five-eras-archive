import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def principled(material):
    if not material.use_nodes or material.node_tree is None:
        raise RuntimeError(f"Material does not use nodes: {material.name}")
    node = next(
        (item for item in material.node_tree.nodes if item.type == "BSDF_PRINCIPLED"),
        None,
    )
    if node is None:
        raise RuntimeError(f"Missing Principled BSDF: {material.name}")
    return node


def unlink_input(material, socket):
    for link in list(material.node_tree.links):
        if link.to_socket == socket:
            material.node_tree.links.remove(link)


def refine_water(scene):
    material = bpy.data.materials.get("Water_Material")
    if material is None:
        raise RuntimeError("Missing Water_Material")
    bsdf = principled(material)
    nodes = material.node_tree.nodes

    ramp = next((node for node in nodes if node.type == "VALTORGB"), None)
    roughness_map = next((node for node in nodes if node.type == "MAP_RANGE"), None)
    bump = next((node for node in nodes if node.type == "BUMP"), None)
    noises = [node for node in nodes if node.type == "TEX_NOISE"]
    if ramp is None or roughness_map is None or bump is None or len(noises) < 2:
        raise RuntimeError("Water node graph is incomplete")

    ramp.color_ramp.interpolation = "EASE"
    ramp.color_ramp.elements[0].position = 0.16
    ramp.color_ramp.elements[0].color = (0.11, 0.40, 0.48, 1.0)
    ramp.color_ramp.elements[1].position = 0.84
    ramp.color_ramp.elements[1].color = (0.15, 0.49, 0.55, 1.0)
    roughness_map.inputs["To Min"].default_value = 0.09
    roughness_map.inputs["To Max"].default_value = 0.14

    noises = sorted(noises, key=lambda node: node.inputs["Scale"].default_value)
    noises[0].inputs["Scale"].default_value = 1.1
    noises[0].inputs["Detail"].default_value = 1.8
    noises[0].inputs["Roughness"].default_value = 0.28
    noises[1].inputs["Scale"].default_value = 7.5
    noises[1].inputs["Detail"].default_value = 1.5
    noises[1].inputs["Roughness"].default_value = 0.3
    bump.inputs["Strength"].default_value = 0.012
    bump.inputs["Distance"].default_value = 0.018

    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.333
    bsdf.inputs["Specular IOR Level"].default_value = 0.62
    bsdf.inputs["Transmission Weight"].default_value = 0.02
    bsdf.inputs["Coat Weight"].default_value = 0.28
    bsdf.inputs["Coat Roughness"].default_value = 0.09
    material.diffuse_color = (0.12, 0.4, 0.47, 1.0)
    material.use_screen_refraction = True
    material.refraction_depth = 0.35

    glossy = nodes.get("Water_Reflection_Glossy")
    if glossy is None:
        glossy = nodes.new("ShaderNodeBsdfGlossy")
        glossy.name = "Water_Reflection_Glossy"
        glossy.label = "Clear grazing-angle river reflection"
    glossy.inputs["Color"].default_value = (0.55, 0.78, 0.85, 1.0)
    glossy.inputs["Roughness"].default_value = 0.075
    if "Weight" in glossy.inputs:
        glossy.inputs["Weight"].default_value = 1.0
    glossy.location = (bsdf.location.x + 20, bsdf.location.y - 260)
    material.node_tree.links.new(bump.outputs["Normal"], glossy.inputs["Normal"])

    fresnel = nodes.get("Water_Reflection_Fresnel")
    if fresnel is None:
        fresnel = nodes.new("ShaderNodeFresnel")
        fresnel.name = "Water_Reflection_Fresnel"
    fresnel.inputs["IOR"].default_value = 1.333
    fresnel.location = (bsdf.location.x - 220, bsdf.location.y - 390)

    reflection_amount = nodes.get("Water_Reflection_Amount")
    if reflection_amount is None:
        reflection_amount = nodes.new("ShaderNodeMapRange")
        reflection_amount.name = "Water_Reflection_Amount"
    reflection_amount.clamp = True
    reflection_amount.interpolation_type = "SMOOTHERSTEP"
    reflection_amount.inputs["From Min"].default_value = 0.0
    reflection_amount.inputs["From Max"].default_value = 0.4
    reflection_amount.inputs["To Min"].default_value = 0.12
    reflection_amount.inputs["To Max"].default_value = 0.38
    reflection_amount.location = (bsdf.location.x, bsdf.location.y - 390)
    material.node_tree.links.new(fresnel.outputs["Fac"], reflection_amount.inputs["Value"])

    reflection_mix = nodes.get("Water_Reflection_Mix")
    if reflection_mix is None:
        reflection_mix = nodes.new("ShaderNodeMixShader")
        reflection_mix.name = "Water_Reflection_Mix"
    reflection_mix.location = (bsdf.location.x + 250, bsdf.location.y - 60)
    material.node_tree.links.new(reflection_amount.outputs["Result"], reflection_mix.inputs[0])
    material.node_tree.links.new(bsdf.outputs["BSDF"], reflection_mix.inputs[1])
    material.node_tree.links.new(glossy.outputs["BSDF"], reflection_mix.inputs[2])
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    unlink_input(material, output.inputs["Surface"])
    material.node_tree.links.new(reflection_mix.outputs["Shader"], output.inputs["Surface"])

    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_method = "SCREEN"
    options = scene.eevee.ray_tracing_options
    options.resolution_scale = "1"
    options.use_denoise = True
    options.denoise_spatial = True
    options.denoise_temporal = True
    options.denoise_bilateral = True
    options.screen_trace_quality = 0.8
    options.screen_trace_thickness = 0.35
    options.trace_max_roughness = 0.35

    probe_object = bpy.data.objects.get("Seine_Planar_Reflection_Probe")
    if probe_object is None:
        probe_data = bpy.data.lightprobes.new("Seine_Planar_Reflection_Probe_Data", "PLANE")
        probe_object = bpy.data.objects.new("Seine_Planar_Reflection_Probe", probe_data)
        bpy.context.collection.objects.link(probe_object)
    probe_object.location = (0.0, 0.0, 0.045)
    probe_object.rotation_euler = (0.0, 0.0, 0.0)
    probe_object.scale = (90.0, 60.0, 1.0)
    probe_object.data.clip_start = 0.05
    probe_object.data.influence_distance = 1.5

    return {
        "material": material.name,
        "colors": [list(element.color) for element in ramp.color_ramp.elements],
        "roughness_range": [
            roughness_map.inputs["To Min"].default_value,
            roughness_map.inputs["To Max"].default_value,
        ],
        "transmission": bsdf.inputs["Transmission Weight"].default_value,
        "coat": bsdf.inputs["Coat Weight"].default_value,
        "raytracing": scene.eevee.use_raytracing,
        "raytracing_resolution": options.resolution_scale,
        "planar_probe": probe_object.name,
    }


def refine_eiffel():
    material = next(
        (
            item
            for item in bpy.data.materials
            if item.name.startswith("Landmark_Eiffel_Tower_GLB_Material")
        ),
        None,
    )
    if material is None:
        raise RuntimeError("Missing imported Eiffel Tower material")
    bsdf = principled(material)
    nodes = material.node_tree.nodes

    for input_name in ("Metallic", "Roughness"):
        unlink_input(material, bsdf.inputs[input_name])
    bsdf.inputs["Metallic"].default_value = 0.38
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["IOR"].default_value = 1.46
    bsdf.inputs["Specular IOR Level"].default_value = 0.58
    bsdf.inputs["Anisotropic"].default_value = 0.08
    bsdf.inputs["Coat Weight"].default_value = 0.2
    bsdf.inputs["Coat Roughness"].default_value = 0.18
    bsdf.inputs["Emission Strength"].default_value = 0.035

    color_lift = nodes.get("Landmark_Eiffel_Tower_GLB_Color_Lift")
    shadow_lift = nodes.get("Landmark_Eiffel_Tower_GLB_Shadow_Lift")
    if color_lift is None or shadow_lift is None:
        raise RuntimeError("Missing Eiffel color correction nodes")
    color_lift.inputs["Saturation"].default_value = 0.82
    color_lift.inputs["Value"].default_value = 1.45
    shadow_lift.inputs["Gamma"].default_value = 0.62

    bronze_mix = nodes.get("Landmark_Eiffel_Tower_GLB_Bronze_Mix")
    if bronze_mix is None:
        bronze_mix = nodes.new("ShaderNodeMixRGB")
        bronze_mix.name = "Landmark_Eiffel_Tower_GLB_Bronze_Mix"
        bronze_mix.label = "Lift iron texture toward warm Eiffel brown"
    bronze_mix.blend_type = "MIX"
    bronze_mix.inputs[0].default_value = 0.26
    bronze_mix.inputs[2].default_value = (0.2, 0.065, 0.018, 1.0)
    bronze_mix.location = (shadow_lift.location.x + 210, shadow_lift.location.y)
    material.node_tree.links.new(shadow_lift.outputs["Color"], bronze_mix.inputs[1])
    for input_name in ("Base Color", "Emission Color"):
        unlink_input(material, bsdf.inputs[input_name])
        material.node_tree.links.new(bronze_mix.outputs["Color"], bsdf.inputs[input_name])
    material.diffuse_color = (0.28, 0.115, 0.035, 1.0)

    return {
        "material": material.name,
        "metallic": bsdf.inputs["Metallic"].default_value,
        "roughness": bsdf.inputs["Roughness"].default_value,
        "coat": bsdf.inputs["Coat Weight"].default_value,
        "value": color_lift.inputs["Value"].default_value,
        "gamma": shadow_lift.inputs["Gamma"].default_value,
    }


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output),
        "water": refine_water(scene),
        "eiffel": refine_eiffel(),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
