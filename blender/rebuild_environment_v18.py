import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


BLENDER_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BLENDER_DIR.parent
BUILD_SCENE_PATH = BLENDER_DIR / "build_scene.py"

WATER_Z = -0.13
LAND_Z = -0.035

SHORE_COLORS = (
    (0.34, 0.46, 0.40, 1.0),
    (0.72, 0.75, 0.63, 1.0),
    (0.79, 0.79, 0.65, 1.0),
    (0.64, 0.62, 0.44, 1.0),
    (0.49, 0.51, 0.32, 1.0),
    (0.39, 0.45, 0.23, 1.0),
    (0.32, 0.39, 0.19, 1.0),
)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def load_build_scene():
    spec = importlib.util.spec_from_file_location("paris_build_scene_v18", BUILD_SCENE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_mesh(obj, vertices, faces, materials, colors=None, smooth=True):
    old_mesh = obj.data
    old_name = old_mesh.name
    mesh = bpy.data.meshes.new(f"{old_name}_v18")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    for material in materials:
        if material is not None:
            mesh.materials.append(material)
    if colors is not None:
        if len(colors) != len(vertices):
            raise ValueError(f"Color count mismatch for {obj.name}")
        attribute = mesh.color_attributes.new(
            name="shore_color",
            type="FLOAT_COLOR",
            domain="POINT",
        )
        for index, color in enumerate(colors):
            attribute.data[index].color = color
    for polygon in mesh.polygons:
        if polygon.normal.z < 0.0:
            polygon.flip()
        polygon.use_smooth = smooth
    mesh.update()
    obj.data = mesh
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    mesh.name = old_name
    return mesh


def set_input(node, name, value):
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def make_shore_material():
    material = bpy.data.materials.get("Shore_Gradient_Material")
    if material is None:
        material = bpy.data.materials.new("Shore_Gradient_Material")
    material.use_nodes = True
    material.diffuse_color = (0.68, 0.69, 0.50, 1.0)
    material.roughness = 0.84
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (420.0, 0.0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (120.0, 0.0)
    attribute = nodes.new("ShaderNodeVertexColor")
    attribute.layer_name = "shore_color"
    attribute.location = (-220.0, 30.0)
    set_input(bsdf, "Roughness", 0.84)
    set_input(bsdf, "Specular IOR Level", 0.28)
    set_input(bsdf, "Coat Weight", 0.035)
    set_input(bsdf, "Coat Roughness", 0.48)
    material.node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
    material.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return material


def smooth_values(values, passes=3):
    result = list(values)
    for _ in range(passes):
        padded = [result[0], result[0], *result, result[-1], result[-1]]
        result = [
            (
                padded[index]
                + 4.0 * padded[index + 1]
                + 6.0 * padded[index + 2]
                + 4.0 * padded[index + 3]
                + padded[index + 4]
            )
            / 16.0
            for index in range(len(result))
        ]
    return result


def terrain_height(bs, x, y):
    clearance = bs.river_clearance(x, y)
    relief = 0.0045 * math.sin(x * 0.17) * math.cos(y * 0.13)
    relief += 0.0025 * math.sin((x + y) * 0.09)
    if clearance <= -0.38:
        return -0.28 + relief * 0.7
    if clearance < 0.0:
        amount = max(0.0, min(1.0, (clearance + 0.38) / 0.38))
        amount = amount * amount * (3.0 - 2.0 * amount)
        return -0.28 * (1.0 - amount) + (WATER_Z - 0.018) * amount
    if clearance < 0.72:
        amount = max(0.0, min(1.0, clearance / 0.72))
        amount = amount * amount * (3.0 - 2.0 * amount)
        return (WATER_Z - 0.018) * (1.0 - amount) + (LAND_Z + relief) * amount
    return LAND_Z + relief


def rebuild_main_river(bs, shore_material):
    x_values = [-92.0 + index * 0.25 for index in range(737)]
    centers = smooth_values([bs.river_center(x) for x in x_values], passes=4)
    widths = smooth_values([bs.river_half_width(x) for x in x_values], passes=3)
    points = list(zip(x_values, centers, widths))

    water_vertices = []
    normals = []
    for index, (x, center, half_width) in enumerate(points):
        previous = points[max(0, index - 1)]
        following = points[min(len(points) - 1, index + 1)]
        tangent = Vector((following[0] - previous[0], following[1] - previous[1]))
        normal = Vector((-tangent.y, tangent.x)).normalized()
        normals.append(normal)
        water_width = half_width + 0.055
        water_vertices.extend(
            (
                (x + normal.x * water_width, center + normal.y * water_width, WATER_Z),
                (x - normal.x * water_width, center - normal.y * water_width, WATER_Z),
            )
        )
    water_faces = []
    for index in range(len(points) - 1):
        first = index * 2
        following = first + 2
        water_faces.append((first, first + 1, following + 1))
        water_faces.append((first, following + 1, following))
    seine = bpy.data.objects["Seine"]
    water_materials = [slot.material for slot in seine.material_slots]
    water_mesh = replace_mesh(
        seine,
        water_vertices,
        water_faces,
        water_materials,
        smooth=True,
    )

    offsets = (-0.10, -0.025, 0.055, 0.14, 0.27, 0.41, 0.56)
    fixed_heights = (
        WATER_Z + 0.010,
        WATER_Z + 0.015,
        WATER_Z + 0.030,
        WATER_Z + 0.052,
        WATER_Z + 0.073,
        WATER_Z + 0.089,
        None,
    )
    bank_vertices = []
    bank_colors = []
    for (x, center, half_width), normal in zip(points, normals):
        for side in (1.0, -1.0):
            for offset, fixed_height, color in zip(offsets, fixed_heights, SHORE_COLORS):
                distance = half_width + offset
                px = x + normal.x * side * distance
                py = center + normal.y * side * distance
                pz = (
                    fixed_height
                    if fixed_height is not None
                    else terrain_height(bs, px, py) + 0.004
                )
                bank_vertices.append((px, py, pz))
                bank_colors.append(color)

    bank_faces = []
    ring_count = len(offsets)
    stride = ring_count * 2
    for index in range(len(points) - 1):
        start = index * stride
        following = (index + 1) * stride
        for ring in range(ring_count - 1):
            bank_faces.append(
                (start + ring, following + ring, following + ring + 1, start + ring + 1)
            )
        south = ring_count
        for ring in range(ring_count - 1):
            bank_faces.append(
                (
                    start + south + ring,
                    start + south + ring + 1,
                    following + south + ring + 1,
                    following + south + ring,
                )
            )
    riverbank = bpy.data.objects["Seine_Riverbank"]
    bank_mesh = replace_mesh(
        riverbank,
        bank_vertices,
        bank_faces,
        [shore_material],
        colors=bank_colors,
        smooth=True,
    )

    return {
        "sample_count": len(points),
        "water_vertices": len(water_mesh.vertices),
        "water_triangles": len(water_mesh.polygons),
        "water_downward_faces": sum(face.normal.z <= 0.0 for face in water_mesh.polygons),
        "bank_rings_per_side": ring_count,
        "bank_vertices": len(bank_mesh.vertices),
        "bank_faces": len(bank_mesh.polygons),
        "bank_smooth_faces": sum(face.use_smooth for face in bank_mesh.polygons),
    }


def signed_area(points):
    return 0.5 * sum(
        first[0] * second[1] - second[0] * first[1]
        for first, second in zip(points, points[1:] + points[:1])
    )


def clean_polygon(points, minimum_distance=0.115):
    cleaned = []
    for point in points:
        point = (float(point[0]), float(point[1]))
        if not cleaned or math.dist(point, cleaned[-1]) >= minimum_distance:
            cleaned.append(point)
    if len(cleaned) > 2 and math.dist(cleaned[0], cleaned[-1]) < minimum_distance:
        cleaned.pop()
    if signed_area(cleaned) < 0.0:
        cleaned.reverse()
    return cleaned


def polygon_center(points):
    return (
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def chaikin(points, iterations=2):
    original_area = abs(signed_area(points))
    result = list(points)
    for _ in range(iterations):
        refined = []
        for first, second in zip(result, result[1:] + result[:1]):
            refined.append(
                (0.75 * first[0] + 0.25 * second[0], 0.75 * first[1] + 0.25 * second[1])
            )
            refined.append(
                (0.25 * first[0] + 0.75 * second[0], 0.25 * first[1] + 0.75 * second[1])
            )
        result = refined
    refined_area = abs(signed_area(result))
    if refined_area > 1e-8:
        scale = math.sqrt(original_area / refined_area)
        center = polygon_center(result)
        result = [
            (
                center[0] + (point[0] - center[0]) * scale,
                center[1] + (point[1] - center[1]) * scale,
            )
            for point in result
        ]
    return result


def resample_closed(points, spacing=0.105):
    segments = [
        math.dist(first, second)
        for first, second in zip(points, points[1:] + points[:1])
    ]
    perimeter = sum(segments)
    count = max(64, math.ceil(perimeter / spacing))
    samples = []
    segment_index = 0
    segment_start_distance = 0.0
    for sample_index in range(count):
        distance = perimeter * sample_index / count
        while distance > segment_start_distance + segments[segment_index]:
            segment_start_distance += segments[segment_index]
            segment_index = (segment_index + 1) % len(points)
        first = points[segment_index]
        second = points[(segment_index + 1) % len(points)]
        segment_length = max(1e-8, segments[segment_index])
        amount = (distance - segment_start_distance) / segment_length
        samples.append(
            (
                first[0] + (second[0] - first[0]) * amount,
                first[1] + (second[1] - first[1]) * amount,
            )
        )
    return samples


def rebuild_island_surface(obj, points, z=0.055):
    center = polygon_center(points)
    vertices = [(center[0], center[1], z)] + [(x, y, z) for x, y in points]
    faces = []
    for index in range(len(points)):
        following = (index + 1) % len(points)
        faces.append((0, index + 1, following + 1))
    materials = [slot.material for slot in obj.material_slots]
    return replace_mesh(obj, vertices, faces, materials, smooth=True)


def rebuild_island_margin(obj, points, shore_material):
    center = polygon_center(points)
    expansions = (0.995, 1.008, 1.025, 1.048, 1.078, 1.112, 1.145)
    heights = (
        0.057,
        0.048,
        0.018,
        -0.024,
        -0.064,
        WATER_Z + 0.020,
        WATER_Z + 0.010,
    )
    colors = tuple(reversed(SHORE_COLORS))
    vertices = []
    vertex_colors = []
    for expansion, height, color in zip(expansions, heights, colors):
        for point in points:
            vertices.append(
                (
                    center[0] + (point[0] - center[0]) * expansion,
                    center[1] + (point[1] - center[1]) * expansion,
                    height,
                )
            )
            vertex_colors.append(color)
    faces = []
    point_count = len(points)
    for ring_index in range(len(expansions) - 1):
        inner = ring_index * point_count
        outer = (ring_index + 1) * point_count
        for index in range(point_count):
            following = (index + 1) % point_count
            faces.append(
                (inner + index, outer + index, outer + following, inner + following)
            )
    mesh = replace_mesh(
        obj,
        vertices,
        faces,
        [shore_material],
        colors=vertex_colors,
        smooth=True,
    )
    return mesh, len(expansions)


def rebuild_islands(bs, shore_material):
    reports = {}
    specifications = (
        ("ile_de_la_cite", "Ile_de_la_Cite", "Ile_de_la_Cite_Margin"),
        ("ile_saint_louis", "Ile_Saint_Louis", "Ile_Saint_Louis_Margin"),
    )
    for key, land_name, margin_name in specifications:
        raw = bs.load_geodata()["islands"][key]
        cleaned = clean_polygon(raw)
        smoothed = resample_closed(chaikin(cleaned, iterations=2))
        land_mesh = rebuild_island_surface(bpy.data.objects[land_name], smoothed)
        margin_mesh, ring_count = rebuild_island_margin(
            bpy.data.objects[margin_name],
            smoothed,
            shore_material,
        )
        reports[key] = {
            "raw_points": len(raw),
            "cleaned_points": len(cleaned),
            "smoothed_points": len(smoothed),
            "shore_rings": ring_count,
            "land_triangles": len(land_mesh.polygons),
            "margin_faces": len(margin_mesh.polygons),
            "margin_smooth_faces": sum(face.use_smooth for face in margin_mesh.polygons),
        }
    return reports


def rebuild_land_material():
    material = bpy.data.materials["Land_Material"]
    material.use_nodes = True
    material.diffuse_color = (0.32, 0.39, 0.19, 1.0)
    material.roughness = 0.88
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (520.0, 0.0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (240.0, 0.0)
    texture_coordinate = nodes.new("ShaderNodeTexCoord")
    texture_coordinate.location = (-620.0, 0.0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "Land_Broad_Variation"
    noise.location = (-390.0, 0.0)
    set_input(noise, "Scale", 0.14)
    set_input(noise, "Detail", 2.4)
    set_input(noise, "Roughness", 0.46)
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.name = "Land_Olive_Palette"
    color_ramp.location = (-110.0, 0.0)
    color_ramp.color_ramp.interpolation = "EASE"
    first, last = color_ramp.color_ramp.elements
    first.position = 0.24
    first.color = (0.255, 0.325, 0.145, 1.0)
    middle = color_ramp.color_ramp.elements.new(0.53)
    middle.color = (0.315, 0.385, 0.18, 1.0)
    last.position = 0.79
    last.color = (0.385, 0.445, 0.225, 1.0)
    set_input(bsdf, "Roughness", 0.88)
    set_input(bsdf, "Specular IOR Level", 0.24)
    material.node_tree.links.new(texture_coordinate.outputs["Object"], noise.inputs["Vector"])
    material.node_tree.links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
    material.node_tree.links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    material.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    land = bpy.data.objects.get("Land")
    if land and land.type == "MESH":
        for polygon in land.data.polygons:
            polygon.use_smooth = True
    return {
        "base_color": list(material.diffuse_color),
        "roughness": material.roughness,
        "land_smooth_faces": sum(face.use_smooth for face in land.data.polygons) if land else 0,
    }


def tune_water_material():
    material = bpy.data.materials["Water_Material"]
    material.diffuse_color = (0.22, 0.39, 0.36, 1.0)
    nodes = material.node_tree.nodes
    color_ramp = next(node for node in nodes if node.type == "VALTORGB")
    color_ramp.color_ramp.interpolation = "EASE"
    elements = color_ramp.color_ramp.elements
    elements[0].position = 0.20
    elements[0].color = (0.18, 0.335, 0.315, 1.0)
    elements[-1].position = 0.80
    elements[-1].color = (0.30, 0.49, 0.45, 1.0)
    noise_nodes = sorted(
        (node for node in nodes if node.type == "TEX_NOISE"),
        key=lambda node: float(node.inputs["Scale"].default_value),
    )
    if noise_nodes:
        set_input(noise_nodes[0], "Scale", 0.72)
        set_input(noise_nodes[0], "Detail", 1.35)
        set_input(noise_nodes[0], "Roughness", 0.34)
    if len(noise_nodes) > 1:
        set_input(noise_nodes[-1], "Scale", 5.4)
        set_input(noise_nodes[-1], "Detail", 1.2)
        set_input(noise_nodes[-1], "Roughness", 0.34)
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    set_input(bsdf, "IOR", 1.333)
    set_input(bsdf, "Specular IOR Level", 0.48)
    set_input(bsdf, "Coat Weight", 0.16)
    set_input(bsdf, "Coat Roughness", 0.22)
    set_input(bsdf, "Transmission Weight", 0.0)
    roughness_map = next(
        (node for node in nodes if node.type == "MAP_RANGE" and node.name != "Water_Reflection_Amount"),
        None,
    )
    if roughness_map:
        set_input(roughness_map, "To Min", 0.22)
        set_input(roughness_map, "To Max", 0.31)
    bump = next((node for node in nodes if node.type == "BUMP"), None)
    if bump:
        set_input(bump, "Strength", 0.0032)
        set_input(bump, "Distance", 0.008)
    glossy = nodes.get("Water_Reflection_Glossy")
    if glossy:
        set_input(glossy, "Roughness", 0.22)
    reflection_amount = nodes.get("Water_Reflection_Amount")
    if reflection_amount:
        set_input(reflection_amount, "To Min", 0.055)
        set_input(reflection_amount, "To Max", 0.18)
    return {
        "dark_color": list(elements[0].color),
        "light_color": list(elements[-1].color),
        "bump_strength": bump.inputs["Strength"].default_value if bump else None,
        "roughness": [0.22, 0.31],
    }


def tune_forest_materials():
    palette = {
        "Forest_Dark": (0.068, 0.155, 0.046, 1.0),
        "Forest_Light": (0.118, 0.235, 0.076, 1.0),
        "Forest_Trunk": (0.185, 0.128, 0.071, 1.0),
        "Forest_Olive": (0.168, 0.252, 0.086, 1.0),
        "Forest_Deep": (0.043, 0.112, 0.036, 1.0),
    }
    for name, color in palette.items():
        material = bpy.data.materials.get(name)
        if material is None:
            continue
        material.diffuse_color = color
        bsdf = next(
            (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
            None,
        )
        if bsdf:
            set_input(bsdf, "Base Color", color)
            set_input(bsdf, "Roughness", 0.70 if name != "Forest_Trunk" else 0.86)
            set_input(bsdf, "Specular IOR Level", 0.32)
            set_input(bsdf, "Coat Weight", 0.035 if name != "Forest_Trunk" else 0.0)
            set_input(bsdf, "Coat Roughness", 0.44)
    return {name: list(color) for name, color in palette.items()}


def tune_lighting():
    scene = bpy.context.scene
    scene.view_settings.exposure = 0.34
    scene.view_settings.gamma = 1.0
    world = scene.world
    if world and world.use_nodes:
        background = next(
            (node for node in world.node_tree.nodes if node.type == "BACKGROUND"),
            None,
        )
        if background:
            background.inputs["Color"].default_value = (0.135, 0.155, 0.090, 1.0)
            background.inputs["Strength"].default_value = 0.95
    sun = bpy.data.objects.get("Sun")
    if sun and sun.type == "LIGHT":
        sun.data.energy = 2.35
        sun.data.angle = 0.19
        sun.data.color = (1.0, 0.91, 0.76)
    if hasattr(scene, "eevee"):
        scene.eevee.use_raytracing = True
        scene.eevee.ray_tracing_method = "PROBE"
        scene.eevee.ray_tracing_options.resolution_scale = "1"
    probe = bpy.data.objects.get("Seine_Planar_Reflection_Probe")
    if probe:
        probe.location.z = WATER_Z + 0.018
        probe.scale = (110.0, 80.0, 1.0)
        probe.data.clip_start = 0.05
        probe.data.influence_distance = 4.0
    return {
        "exposure": scene.view_settings.exposure,
        "world_color": [0.135, 0.155, 0.090, 1.0],
        "world_strength": 0.95,
        "sun_energy": sun.data.energy if sun else None,
        "sun_angle": sun.data.angle if sun else None,
        "sun_color": list(sun.data.color) if sun else None,
    }


def count_growth_objects():
    prefixes = (
        "Buildings_Roman_State_",
        "Buildings_Medieval_State_",
        "Island_Cite_",
        "Island_Saint_Louis_",
    )
    return sum(obj.name.startswith(prefixes) for obj in bpy.data.objects)


def main():
    args = parse_args()
    output_path = args.output.resolve()
    report_path = args.report.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    bs = load_build_scene()

    growth_object_count_before = count_growth_objects()
    shore_material = make_shore_material()
    main_river_report = rebuild_main_river(bs, shore_material)
    island_report = rebuild_islands(bs, shore_material)
    land_report = rebuild_land_material()
    water_report = tune_water_material()
    forest_report = tune_forest_materials()
    lighting_report = tune_lighting()
    growth_object_count_after = count_growth_objects()

    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(output_path),
        "main_river": main_river_report,
        "islands": island_report,
        "land": land_report,
        "water_material": water_report,
        "forest_materials": forest_report,
        "lighting": lighting_report,
        "growth_objects_before": growth_object_count_before,
        "growth_objects_after": growth_object_count_after,
        "growth_object_count_unchanged": growth_object_count_before == growth_object_count_after,
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("ENVIRONMENT_V18_REPORT_BEGIN")
    print(json.dumps(report, indent=2))
    print("ENVIRONMENT_V18_REPORT_END")


if __name__ == "__main__":
    main()
