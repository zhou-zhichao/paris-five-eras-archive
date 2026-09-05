import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
PLACEMENT_SCRIPT = Path(__file__).with_name("place_medieval_trellis_landmarks_v38.py")
ROOT_NAME = "Landmark_Tour_du_Temple_Trellis"
MODEL_NAME = f"{ROOT_NAME}_Model"
CONTEXT_NAME = "Temple_Enclos_v44"
TARGET_DIMENSIONS = Vector((0.42, 0.48, 0.58))
PRECINCT_CENTER = Vector((-0.55, -0.35))
PRECINCT_DIMENSIONS = Vector((2.10, 1.75))
FULL_STATE_FRAMES = {1: 1450, 2: 2100}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def load_placement_module():
    spec = importlib.util.spec_from_file_location("trellis_placement_v44", PLACEMENT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def descendants(root):
    result = []
    stack = list(root.children)
    while stack:
        child = stack.pop()
        result.append(child)
        stack.extend(child.children)
    return result


def remove_tree(name):
    root = bpy.data.objects.get(name)
    if root is None:
        return
    for obj in reversed(descendants(root)):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)


def material(name, fallback=None):
    value = bpy.data.materials.get(name)
    if value is None and fallback is not None:
        value = bpy.data.materials.get(fallback)
    if value is None:
        raise RuntimeError(f"Missing material: {name}")
    return value


def make_principled_material(name, color, roughness=0.86):
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    principled = next(node for node in value.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = (*color, 1.0)
    principled.inputs["Roughness"].default_value = roughness
    principled.inputs["Metallic"].default_value = 0.0
    specular = principled.inputs.get("Specular IOR Level")
    if specular is not None:
        specular.default_value = 0.22
    return value


def link_material(obj, value):
    if value is not None:
        obj.data.materials.append(value)


def add_cube(name, location, dimensions, value, parent, rotation=0.0):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    obj.dimensions = dimensions
    obj.rotation_euler.z = rotation
    link_material(obj, value)
    return obj


def add_cylinder(name, location, radius, height, value, parent, segments=24):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=height,
    )
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    link_material(obj, value)
    return obj


def add_cone(name, location, radius, height, value, parent, segments=24):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=0.015,
        depth=height,
    )
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    link_material(obj, value)
    return obj


def add_gable_roof(name, location, width, depth, height, value, parent, rotation=0.0):
    half_width = width * 0.5
    half_depth = depth * 0.5
    vertices = [
        (-half_width, -half_depth, 0.0),
        (half_width, -half_depth, 0.0),
        (half_width, half_depth, 0.0),
        (-half_width, half_depth, 0.0),
        (0.0, -half_depth, height),
        (0.0, half_depth, height),
    ]
    faces = [
        (0, 1, 4),
        (3, 5, 2),
        (0, 4, 5, 3),
        (1, 2, 5, 4),
        (0, 3, 2, 1),
    ]
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    obj.rotation_euler.z = rotation
    link_material(obj, value)
    return obj


def add_rect_building(
    name,
    location,
    width,
    depth,
    height,
    wall_material,
    roof_material,
    window_material,
    door_material,
    parent,
    rotation=0.0,
):
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.parent = parent
    root.location = location
    root.rotation_euler.z = rotation
    add_cube(
        f"{name}_Walls",
        (0.0, 0.0, height * 0.5),
        (width, depth, height),
        wall_material,
        root,
    )
    roof_height = min(0.09, depth * 0.42)
    add_gable_roof(
        f"{name}_Roof",
        (0.0, 0.0, height),
        width + 0.035,
        depth + 0.035,
        roof_height,
        roof_material,
        root,
    )
    window_count = max(2, int(width / 0.15))
    for index in range(window_count):
        x = -width * 0.38 + width * 0.76 * index / max(1, window_count - 1)
        for side in (-1.0, 1.0):
            add_cube(
                f"{name}_Window_{index:02d}_{int(side):+d}",
                (x, side * (depth * 0.5 + 0.004), height * 0.60),
                (0.028, 0.008, 0.052),
                window_material,
                root,
            )
    add_cube(
        f"{name}_Door",
        (0.0, -(depth * 0.5 + 0.005), height * 0.23),
        (0.040, 0.010, height * 0.42),
        door_material,
        root,
    )
    return root


def add_road_segment(name, start, end, width, value, parent):
    start = Vector(start)
    end = Vector(end)
    delta = end - start
    length = delta.length
    center = (start + end) * 0.5
    return add_cube(
        name,
        (center.x, center.y, 0.014),
        (length + 0.03, width, 0.012),
        value,
        parent,
        rotation=math.atan2(delta.y, delta.x),
    )


def add_wall_segment(name, start, end, stone, parent):
    start = Vector(start)
    end = Vector(end)
    delta = end - start
    length = delta.length
    center = (start + end) * 0.5
    rotation = math.atan2(delta.y, delta.x)
    wall = add_cube(
        name,
        (center.x, center.y, 0.060),
        (length, 0.050, 0.120),
        stone,
        parent,
        rotation=rotation,
    )
    crenel_count = max(1, int(length / 0.10))
    direction = delta.normalized()
    for index in range(crenel_count + 1):
        progress = index / max(1, crenel_count)
        point = start.lerp(end, progress)
        add_cube(
            f"{name}_Crenel_{index:02d}",
            (point.x, point.y, 0.145),
            (0.050, 0.060, 0.050),
            stone,
            parent,
            rotation=rotation,
        )
    return wall


def add_gate_towers(prefix, first, second, stone, slate, parent):
    for index, point in enumerate((first, second)):
        add_cylinder(
            f"{prefix}_Tower_{index}",
            (point[0], point[1], 0.095),
            0.070,
            0.190,
            stone,
            parent,
            segments=16,
        )
        add_cone(
            f"{prefix}_Roof_{index}",
            (point[0], point[1], 0.225),
            0.082,
            0.070,
            slate,
            parent,
            segments=16,
        )


def split_horizontal_wall(prefix, minimum_x, maximum_x, y, gap_center, gap_width, stone, parent):
    left_end = gap_center - gap_width * 0.5
    right_start = gap_center + gap_width * 0.5
    add_wall_segment(f"{prefix}_Left", (minimum_x, y), (left_end, y), stone, parent)
    add_wall_segment(f"{prefix}_Right", (right_start, y), (maximum_x, y), stone, parent)
    add_gate_towers(
        f"{prefix}_Gate",
        (left_end, y),
        (right_start, y),
        stone,
        material("Roof_Slate"),
        parent,
    )


def split_vertical_wall(prefix, x, minimum_y, maximum_y, gap_center, gap_width, stone, parent):
    lower_end = gap_center - gap_width * 0.5
    upper_start = gap_center + gap_width * 0.5
    add_wall_segment(f"{prefix}_Lower", (x, minimum_y), (x, lower_end), stone, parent)
    add_wall_segment(f"{prefix}_Upper", (x, upper_start), (x, maximum_y), stone, parent)
    add_gate_towers(
        f"{prefix}_Gate",
        (x, lower_end),
        (x, upper_start),
        stone,
        material("Roof_Slate"),
        parent,
    )


def rescale_keep(root):
    model = bpy.data.objects.get(MODEL_NAME)
    if model is None:
        raise RuntimeError(f"Missing model root: {MODEL_NAME}")
    current_dimensions = Vector(root.get("target_dimensions", (1.05, 1.18, 1.12)))
    ratios = Vector(
        tuple(TARGET_DIMENSIONS[index] / max(1e-6, current_dimensions[index]) for index in range(3))
    )
    model.scale = tuple(model.scale[index] * ratios[index] for index in range(3))
    model.location = tuple(model.location[index] * ratios[index] for index in range(3))
    root["target_dimensions"] = tuple(TARGET_DIMENSIONS)
    root["historical_height_m"] = 45.0
    root["scene_scale_note"] = "1 unit = 100 m; keep resized to a 42 x 48 x 58 m visual envelope"
    return {
        "previous_dimensions": list(current_dimensions),
        "target_dimensions": list(TARGET_DIMENSIONS),
        "ratios": list(ratios),
    }


def create_enclosure(root):
    remove_tree(CONTEXT_NAME)
    context = bpy.data.objects.new(CONTEXT_NAME, None)
    bpy.context.collection.objects.link(context)
    context.parent = root
    context["historical_identity"] = "Enclos du Temple, fortified Templar commandery"
    context["historical_area_ha"] = 6.0
    context["layout_note"] = "Stylized precinct: keep, round church, convent, stable, gardens and two road gates"

    stone = material("Cite_Tower_Stone_Matte_v36", "Landmark_Stone")
    wall = material("House_v37_Stone", "Wall_Stone")
    roof = material("House_v37_Roof_Tile_02", "Roof_Terracotta")
    slate = material("Roof_Slate")
    window = material("House_v37_Window_Dark", "Building_Window_Dark")
    door = material("Door_Wood_1", "VICVS_Dark_Wood")
    road = material("Road_Material")
    ground = make_principled_material("Temple_Enclos_Ground_v44", (0.29, 0.36, 0.19), roughness=0.92)
    garden = make_principled_material("Temple_Enclos_Garden_v44", (0.20, 0.31, 0.13), roughness=0.94)

    minimum_x = PRECINCT_CENTER.x - PRECINCT_DIMENSIONS.x * 0.5
    maximum_x = PRECINCT_CENTER.x + PRECINCT_DIMENSIONS.x * 0.5
    minimum_y = PRECINCT_CENTER.y - PRECINCT_DIMENSIONS.y * 0.5
    maximum_y = PRECINCT_CENTER.y + PRECINCT_DIMENSIONS.y * 0.5
    add_cube(
        "Temple_Enclos_Ground_v44",
        (PRECINCT_CENTER.x, PRECINCT_CENTER.y, 0.005),
        (PRECINCT_DIMENSIONS.x - 0.06, PRECINCT_DIMENSIONS.y - 0.06, 0.010),
        ground,
        context,
    )
    add_cube(
        "Temple_Enclos_Garden_v44",
        (-0.62, -0.53, 0.012),
        (0.58, 0.42, 0.010),
        garden,
        context,
    )

    west_gate_y = -0.47
    east_gate_y = -0.83
    gate_width = 0.22
    add_wall_segment("Temple_Enclos_North_Wall_v44", (minimum_x, maximum_y), (maximum_x, maximum_y), stone, context)
    add_wall_segment("Temple_Enclos_South_Wall_v44", (minimum_x, minimum_y), (maximum_x, minimum_y), stone, context)
    split_vertical_wall(
        "Temple_Enclos_West_Wall_v44",
        minimum_x,
        minimum_y,
        maximum_y,
        west_gate_y,
        gate_width,
        stone,
        context,
    )
    split_vertical_wall(
        "Temple_Enclos_East_Wall_v44",
        maximum_x,
        minimum_y,
        maximum_y,
        east_gate_y,
        gate_width,
        stone,
        context,
    )

    road_points = [
        (minimum_x - 0.10, west_gate_y),
        (-1.10, 0.43),
        (0.064, -0.476),
        (maximum_x + 0.10, east_gate_y),
    ]
    for index, (start, end) in enumerate(zip(road_points, road_points[1:])):
        add_road_segment(f"Temple_Enclos_Road_v44_{index:02d}", start, end, 0.13, road, context)

    add_rect_building(
        "Temple_Enclos_Convent_v44",
        (-0.62, -1.02, 0.0),
        0.72,
        0.20,
        0.17,
        wall,
        roof,
        window,
        door,
        context,
    )
    add_rect_building(
        "Temple_Enclos_Stable_v44",
        (-1.38, 0.13, 0.0),
        0.50,
        0.18,
        0.13,
        wall,
        roof,
        window,
        door,
        context,
        rotation=math.radians(90.0),
    )
    add_rect_building(
        "Temple_Enclos_Guesthouse_v44",
        (-0.32, 0.36, 0.0),
        0.48,
        0.18,
        0.15,
        wall,
        roof,
        window,
        door,
        context,
    )

    church_root = bpy.data.objects.new("Temple_Round_Church_v44", None)
    bpy.context.collection.objects.link(church_root)
    church_root.parent = context
    church_root.location = (-1.02, -0.58, 0.0)
    add_cylinder("Temple_Round_Church_Rotunda_v44", (0.0, 0.0, 0.10), 0.19, 0.20, stone, church_root, segments=24)
    add_cone("Temple_Round_Church_Roof_v44", (0.0, 0.0, 0.255), 0.215, 0.11, slate, church_root, segments=24)
    add_rect_building(
        "Temple_Round_Church_Choir_v44",
        (0.25, 0.0, 0.0),
        0.34,
        0.24,
        0.16,
        stone,
        slate,
        window,
        door,
        church_root,
    )
    for index, angle in enumerate((0.0, math.pi * 0.5, math.pi, math.pi * 1.5)):
        add_cube(
            f"Temple_Round_Church_Window_v44_{index:02d}",
            (math.cos(angle) * 0.192, math.sin(angle) * 0.192, 0.115),
            (0.026, 0.012, 0.055),
            window,
            church_root,
            rotation=angle,
        )

    for index, point in enumerate(((-0.78, -0.52), (-0.55, -0.48), (-0.47, -0.68), (-0.72, -0.71))):
        add_cylinder(
            f"Temple_Enclos_Garden_Tree_Trunk_v44_{index:02d}",
            (point[0], point[1], 0.035),
            0.013,
            0.070,
            door,
            context,
            segments=10,
        )
        add_cone(
            f"Temple_Enclos_Garden_Tree_Crown_v44_{index:02d}",
            (point[0], point[1], 0.115),
            0.065,
            0.13,
            garden,
            context,
            segments=12,
        )
    return context


def world_precinct_spec(root):
    cosine = math.cos(root.rotation_euler.z)
    sine = math.sin(root.rotation_euler.z)
    center_x = root.location.x + PRECINCT_CENTER.x * cosine - PRECINCT_CENTER.y * sine
    center_y = root.location.y + PRECINCT_CENTER.x * sine + PRECINCT_CENTER.y * cosine
    return {
        "name": "Temple_Enclos_v44_Clearance",
        "location": (center_x, center_y, root.location.z),
        "rotation": root.rotation_euler.z,
        "dimensions": (PRECINCT_DIMENSIONS.x, PRECINCT_DIMENSIONS.y, 0.20),
        "active_eras": [1, 2],
        "clearance": 0.075,
    }


def clear_precinct(root, placement):
    site_spec = world_precinct_spec(root)
    report = {}
    for era, frame in FULL_STATE_FRAMES.items():
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        buildings = []
        for obj in list(bpy.data.objects):
            if obj.type != "MESH" or not obj.name.startswith(placement.BUILDING_PREFIXES[era]):
                continue
            result = placement.clear_procedural_buildings_from_object(obj, [site_spec])
            if result is not None:
                buildings.append(result)
        forest = []
        forest_prefix = f"Forest_Cleared_{era}_Chunk_"
        for obj in list(bpy.data.objects):
            if obj.type != "MESH" or not obj.name.startswith(forest_prefix):
                continue
            result = placement.clear_spatial_clusters_from_object(obj, [site_spec], extra_margin=0.02)
            if result is not None:
                forest.append(result)
        report[str(era)] = {
            "buildings_removed": sum(item["removed_components"] for item in buildings),
            "building_faces_removed": sum(item["removed_faces"] for item in buildings),
            "forest_clusters_removed": sum(item["removed_components"] for item in forest),
            "forest_faces_removed": sum(item["removed_faces"] for item in forest),
            "building_details": buildings,
            "forest_details": forest,
        }
    return site_spec, report


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    placement = load_placement_module()
    root = bpy.data.objects.get(ROOT_NAME)
    if root is None:
        raise RuntimeError(f"Missing landmark root: {ROOT_NAME}")

    scale_report = rescale_keep(root)
    site_spec, clearance_report = clear_precinct(root, placement)
    context = create_enclosure(root)
    root["historical_context"] = "Northern periphery outside Philippe Augustus wall; represented as a fortified commandery"
    root["source_note"] = "Templars Route and Mercuri research summary: keep, ramparts, Caesar tower, round church and monastic buildings"

    bpy.context.scene.frame_set(1450)
    bpy.context.view_layer.update()
    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output),
        "scale": scale_report,
        "precinct_center_local": list(PRECINCT_CENTER),
        "precinct_dimensions": list(PRECINCT_DIMENSIONS),
        "clearance_spec": site_spec,
        "clearance": clearance_report,
        "context_root": context.name,
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
