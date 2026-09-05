import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import bpy


HOUSE_PREFIXES = (
    "Buildings_Medieval_State_Chunk_",
    "Island_Cite_1_State_Chunk_",
    "Island_Saint_Louis_1_State_Chunk_",
)

WALL_COLORS = (
    (0.62, 0.53, 0.40, 1.0),
    (0.55, 0.46, 0.35, 1.0),
    (0.69, 0.61, 0.48, 1.0),
    (0.48, 0.42, 0.35, 1.0),
    (0.60, 0.49, 0.37, 1.0),
    (0.54, 0.50, 0.42, 1.0),
)

ROOF_COLORS = (
    (0.24, 0.052, 0.026, 1.0),
    (0.30, 0.066, 0.029, 1.0),
    (0.18, 0.045, 0.030, 1.0),
    (0.32, 0.080, 0.036, 1.0),
    (0.15, 0.050, 0.040, 1.0),
    (0.27, 0.061, 0.031, 1.0),
)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def scaled_color(color, factor):
    return tuple(min(1.0, max(0.0, channel * factor)) for channel in color[:3]) + (1.0,)


def set_input(node, name, value):
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def new_principled_material(
    name,
    color,
    roughness,
    specular,
    metallic=0.0,
    coat=0.0,
):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = color
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (500, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (220, 0)
    set_input(bsdf, "Base Color", color)
    set_input(bsdf, "Metallic", metallic)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "Diffuse Roughness", 0.28)
    set_input(bsdf, "Specular IOR Level", specular)
    set_input(bsdf, "Coat Weight", coat)
    set_input(bsdf, "Coat Roughness", 0.55)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    material["v37_material_system"] = "shared historical house material"
    return material, bsdf


def add_noise_surface(
    material,
    bsdf,
    color,
    scale,
    roughness_range,
    bump_strength,
    bump_distance,
    ground_gradient=False,
):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    geometry = nodes.new("ShaderNodeNewGeometry")
    geometry.location = (-900, 60)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-680, 120)
    noise.noise_dimensions = "3D"
    set_input(noise, "Scale", scale)
    set_input(noise, "Detail", 3.0)
    set_input(noise, "Roughness", 0.68)
    set_input(noise, "Distortion", 0.12)
    links.new(geometry.outputs["Position"], noise.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-430, 160)
    ramp.color_ramp.elements[0].position = 0.27
    ramp.color_ramp.elements[0].color = scaled_color(color, 0.91)
    ramp.color_ramp.elements[1].position = 0.76
    ramp.color_ramp.elements[1].color = scaled_color(color, 1.055)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])

    color_output = ramp.outputs["Color"]
    if ground_gradient:
        separate = nodes.new("ShaderNodeSeparateXYZ")
        separate.location = (-680, -165)
        links.new(geometry.outputs["Position"], separate.inputs["Vector"])
        ground = nodes.new("ShaderNodeMapRange")
        ground.location = (-430, -170)
        ground.clamp = True
        set_input(ground, "From Min", 0.0)
        set_input(ground, "From Max", 0.18)
        set_input(ground, "To Min", 0.84)
        set_input(ground, "To Max", 1.0)
        links.new(separate.outputs["Z"], ground.inputs["Value"])
        multiply = nodes.new("ShaderNodeMixRGB")
        multiply.location = (-170, 130)
        multiply.blend_type = "MULTIPLY"
        multiply.inputs["Fac"].default_value = 1.0
        links.new(ramp.outputs["Color"], multiply.inputs[1])
        links.new(ground.outputs["Result"], multiply.inputs[2])
        color_output = multiply.outputs["Color"]
    links.new(color_output, bsdf.inputs["Base Color"])

    roughness = nodes.new("ShaderNodeMapRange")
    roughness.location = (-160, -85)
    roughness.clamp = True
    set_input(roughness, "From Min", 0.0)
    set_input(roughness, "From Max", 1.0)
    set_input(roughness, "To Min", roughness_range[0])
    set_input(roughness, "To Max", roughness_range[1])
    links.new(noise.outputs["Fac"], roughness.inputs["Value"])
    links.new(roughness.outputs["Result"], bsdf.inputs["Roughness"])

    bump = nodes.new("ShaderNodeBump")
    bump.location = (-130, -250)
    set_input(bump, "Strength", bump_strength)
    set_input(bump, "Distance", bump_distance)
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def build_library():
    library = {}
    for index, color in enumerate(WALL_COLORS, start=1):
        material, bsdf = new_principled_material(
            f"House_v37_Plaster_{index:02d}",
            color,
            0.82,
            0.22,
        )
        add_noise_surface(
            material,
            bsdf,
            color,
            31.0,
            (0.76, 0.88),
            0.055,
            0.010,
            ground_gradient=True,
        )
        library[("wall", index)] = material

    for index, color in enumerate(ROOF_COLORS, start=1):
        material, bsdf = new_principled_material(
            f"House_v37_Roof_Tile_{index:02d}",
            color,
            0.72,
            0.24,
        )
        add_noise_surface(
            material,
            bsdf,
            color,
            42.0,
            (0.64, 0.80),
            0.10,
            0.008,
        )
        library[("roof", index)] = material

    shared_specs = {
        "timber": ((0.105, 0.050, 0.023, 1.0), 0.70, 0.23, 24.0, (0.64, 0.78), 0.075, 0.007),
        "door": ((0.135, 0.062, 0.028, 1.0), 0.68, 0.24, 22.0, (0.62, 0.76), 0.07, 0.007),
        "stone": ((0.54, 0.49, 0.40, 1.0), 0.82, 0.22, 47.0, (0.76, 0.88), 0.06, 0.009),
        "frame": ((0.070, 0.036, 0.018, 1.0), 0.66, 0.23, 26.0, (0.60, 0.74), 0.055, 0.006),
    }
    for key, values in shared_specs.items():
        color, base_roughness, specular, scale, roughness_range, strength, distance = values
        material, bsdf = new_principled_material(
            f"House_v37_{key.title()}",
            color,
            base_roughness,
            specular,
        )
        add_noise_surface(
            material,
            bsdf,
            color,
            scale,
            roughness_range,
            strength,
            distance,
        )
        library[(key, 0)] = material

    iron, iron_bsdf = new_principled_material(
        "House_v37_Iron",
        (0.025, 0.023, 0.021, 1.0),
        0.52,
        0.28,
        metallic=0.72,
    )
    set_input(iron_bsdf, "Diffuse Roughness", 0.18)
    library[("iron", 0)] = iron

    glass_dark, glass_dark_bsdf = new_principled_material(
        "House_v37_Window_Dark",
        (0.022, 0.043, 0.054, 1.0),
        0.28,
        0.36,
        coat=0.055,
    )
    set_input(glass_dark_bsdf, "Diffuse Roughness", 0.08)
    library[("glass_dark", 0)] = glass_dark

    glass_warm, glass_warm_bsdf = new_principled_material(
        "House_v37_Window_Warm",
        (0.19, 0.095, 0.034, 1.0),
        0.31,
        0.34,
        coat=0.045,
    )
    set_input(glass_warm_bsdf, "Diffuse Roughness", 0.10)
    set_input(glass_warm_bsdf, "Emission Color", (0.11, 0.038, 0.008, 1.0))
    set_input(glass_warm_bsdf, "Emission Strength", 0.07)
    library[("glass_warm", 0)] = glass_warm
    return library


def normalized_name(name):
    return re.sub(r"\.\d{3}$", "", name)


def material_key(name):
    name = normalized_name(name)
    match = re.fullmatch(r"Wall_([1-6])", name)
    if match:
        return "wall", int(match.group(1))
    match = re.fullmatch(r"Roof_Tile_([1-6])", name)
    if match:
        return "roof", int(match.group(1))
    if re.fullmatch(r"Dark_Timber_[1-6]", name):
        return "timber", 0
    if re.fullmatch(r"Door_Wood_[1-6]", name):
        return "door", 0
    if re.fullmatch(r"Stone_Trim_[1-6]", name):
        return "stone", 0
    if re.fullmatch(r"Window_Frame_[1-6]", name):
        return "frame", 0
    if re.fullmatch(r"Iron_[1-6]", name):
        return "iron", 0
    match = re.fullmatch(r"Window_Glass_([1-6])", name)
    if match:
        return ("glass_warm", 0) if int(match.group(1)) in {3, 6} else ("glass_dark", 0)
    return None


def main():
    args = parse_args()
    args.output_blend = args.output_blend.resolve()
    args.report = args.report.resolve()
    args.output_blend.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    library = build_library()
    house_objects = [
        obj
        for obj in bpy.data.objects
        if obj.name.startswith(HOUSE_PREFIXES)
    ]
    category_counts = Counter()
    source_materials = set()
    assignment_count = 0
    for obj in house_objects:
        for slot in obj.material_slots:
            if slot.material is None:
                continue
            key = material_key(slot.material.name)
            if key is None:
                continue
            source_materials.add(slot.material.name)
            slot.material = library[key]
            category_counts[key[0]] += 1
            assignment_count += 1

    if assignment_count == 0:
        raise RuntimeError("No medieval house material slots were reassigned")

    scene = bpy.context.scene
    scene["v37_house_materials"] = (
        "Matte lime plaster, weathered timber, varied roof tile, stone, and restrained glazing"
    )
    source_blend = bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(
        filepath=str(args.output_blend),
        compress=True,
    )
    report = {
        "version": "v37",
        "source_blend": source_blend,
        "output_blend": str(args.output_blend),
        "house_object_count": len(house_objects),
        "source_material_count": len(source_materials),
        "shared_material_count": len({material.name for material in library.values()}),
        "assignment_count": assignment_count,
        "category_assignments": dict(sorted(category_counts.items())),
        "shared_materials": sorted({material.name for material in library.values()}),
        "art_direction": {
            "walls": "muted lime plaster with subtle mottling and ground dampening",
            "timber": "lifted dark brown with low specular response",
            "roof": "six weathered terracotta palettes with rough tile variation",
            "stone": "matte warm limestone",
            "windows": "non-metallic dark or restrained warm glazing",
        },
    }
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
