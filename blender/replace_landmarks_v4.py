import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "outputs" / "landmark_glb_v1"
ASSET_MODEL_DIR = PROJECT_DIR / "assets" / "models"
PHASE_FRAMES = [150, 825, 1500, 2175, 2850]


LANDMARK_SPECS = [
    {
        "name": "Landmark_Notre_Dame_GLB",
        "replace": "Landmark_Notre_Dame",
        "path": MODEL_DIR / "notre_dame.glb",
        "location": (0.15, 0.25, 0.055),
        "rotation": -0.55,
        "dimensions": (2.40, 1.45, 1.55),
        "start": PHASE_FRAMES[1] + 120,
        "duration": 24,
        "first_era": 1,
        "clearance": 0.12,
    },
    {
        "name": "Landmark_Louvre_GLB",
        "replace": "Landmark_Louvre",
        "path": MODEL_DIR / "louvre.glb",
        "location": (-10.8, 11.9, 0.055),
        "rotation": math.radians(90.0),
        "dimensions": (3.40, 4.00, 1.20),
        "start": PHASE_FRAMES[2] + 80,
        "duration": 28,
        "first_era": 2,
        "clearance": 0.16,
    },
    {
        "name": "Landmark_Arc_de_Triomphe_GLB",
        "replace": "Landmark_Arc_de_Triomphe",
        "path": MODEL_DIR / "arc_de_triomphe.glb",
        "location": (-40.2, 23.2, 0.055),
        "rotation": 0.0,
        "dimensions": (1.15, 0.82, 1.35),
        "start": PHASE_FRAMES[3] + 60,
        "duration": 22,
        "first_era": 3,
        "clearance": 0.18,
    },
    {
        "name": "Landmark_Palais_Garnier_GLB",
        "replace": None,
        "path": MODEL_DIR / "palais_garnier.glb",
        "location": (-13.6, 18.4, 0.055),
        "rotation": math.radians(-4.0),
        "dimensions": (2.30, 1.72, 1.25),
        "start": PHASE_FRAMES[3] + 200,
        "duration": 26,
        "first_era": 3,
        "clearance": 0.16,
    },
    {
        "name": "Landmark_Gare_du_Nord_GLB",
        "replace": None,
        "path": MODEL_DIR / "gare_du_nord.glb",
        "location": (6.5, 26.15, 0.055),
        "rotation": math.radians(173.0),
        "dimensions": (3.40, 4.60, 1.25),
        "start": PHASE_FRAMES[4] + 52,
        "duration": 28,
        "first_era": 4,
        "clearance": 0.18,
        "station": True,
    },
    {
        "name": "Landmark_Eiffel_Tower_GLB",
        "replace": "Landmark_Eiffel_Tower",
        "path": ASSET_MODEL_DIR / "eiffel_tower_low_poly.glb",
        "location": (-40.6, 6.0, 0.055),
        "rotation": 0.0,
        "dimensions": (2.75, 2.75, 7.30),
        "start": PHASE_FRAMES[4] + 80,
        "duration": 30,
        "first_era": 4,
        "clearance": 0.12,
    },
]


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(args)


def descendants(root):
    result = []
    stack = list(root.children)
    while stack:
        child = stack.pop()
        result.append(child)
        stack.extend(child.children)
    return result


def remove_tree(root):
    for obj in reversed(descendants(root)):
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    if root.name in bpy.data.objects:
        bpy.data.objects.remove(root, do_unlink=True)


def remove_named_tree(name):
    root = bpy.data.objects.get(name)
    if root is not None:
        remove_tree(root)


def set_constant_visibility_keys(obj):
    action = getattr(getattr(obj, "animation_data", None), "action", None)
    if action is None:
        return
    for curve in action.fcurves:
        if curve.data_path != "hide_render":
            continue
        for keyframe in curve.keyframe_points:
            keyframe.interpolation = "CONSTANT"


def set_sprout_easing(obj):
    action = getattr(getattr(obj, "animation_data", None), "action", None)
    if action is None:
        return
    for curve in action.fcurves:
        if curve.data_path not in {"location", "scale"}:
            continue
        for keyframe in curve.keyframe_points:
            keyframe.interpolation = "QUAD"
            keyframe.easing = "EASE_OUT"


def animate_sprout(root, start_frame, duration):
    targets = [root, *descendants(root)]
    for target in targets:
        target.hide_render = True
        target.keyframe_insert(data_path="hide_render", frame=1)
        target.keyframe_insert(data_path="hide_render", frame=start_frame - 1)
        target.hide_render = False
        target.keyframe_insert(data_path="hide_render", frame=start_frame)
        set_constant_visibility_keys(target)

    final_location = tuple(root.location)
    final_scale = tuple(root.scale)
    peak_frame = start_frame + max(3, duration - 2)
    root.location = (final_location[0], final_location[1], final_location[2] - 0.18)
    root.scale = (final_scale[0], final_scale[1], 0.012)
    root.keyframe_insert(data_path="location", frame=start_frame)
    root.keyframe_insert(data_path="scale", frame=start_frame)
    root.location = (final_location[0], final_location[1], final_location[2] + 0.012)
    root.scale = (final_scale[0], final_scale[1], 1.045)
    root.keyframe_insert(data_path="location", frame=peak_frame)
    root.keyframe_insert(data_path="scale", frame=peak_frame)
    root.location = final_location
    root.scale = final_scale
    root.keyframe_insert(data_path="location", frame=start_frame + duration)
    root.keyframe_insert(data_path="scale", frame=start_frame + duration)
    set_sprout_easing(root)


def mesh_world_bounds(meshes):
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector((min(point.x for point in corners), min(point.y for point in corners), min(point.z for point in corners)))
    maximum = Vector((max(point.x for point in corners), max(point.y for point in corners), max(point.z for point in corners)))
    return minimum, maximum


def import_landmark(spec):
    path = spec["path"]
    if not path.is_file():
        raise FileNotFoundError(path)

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh found in {path}")
    minimum, maximum = mesh_world_bounds(meshes)
    source_dimensions = maximum - minimum
    source_center = (minimum + maximum) * 0.5

    root = bpy.data.objects.new(spec["name"], None)
    root.empty_display_type = "PLAIN_AXES"
    bpy.context.collection.objects.link(root)
    root.location = spec["location"]
    root.rotation_euler[2] = spec["rotation"]

    model = bpy.data.objects.new(f"{spec['name']}_Model", None)
    model.empty_display_type = "CUBE"
    bpy.context.collection.objects.link(model)
    model.parent = root

    for obj in imported:
        if obj.parent is None:
            world_matrix = obj.matrix_world.copy()
            obj.parent = model
            obj.matrix_world = world_matrix

    target_dimensions = Vector(spec["dimensions"])
    scale = Vector(
        (
            target_dimensions.x / max(0.0001, source_dimensions.x),
            target_dimensions.y / max(0.0001, source_dimensions.y),
            target_dimensions.z / max(0.0001, source_dimensions.z),
        )
    )
    model.scale = scale
    model.location = (
        -source_center.x * scale.x,
        -source_center.y * scale.y,
        -minimum.z * scale.z,
    )

    for obj in meshes:
        obj.name = f"{spec['name']}_Mesh"
        obj["source_glb"] = str(path.resolve())
        for material in obj.data.materials:
            if material is not None and not material.name.startswith(spec["name"]):
                material.name = f"{spec['name']}_{material.name}"

    root["source_glb"] = str(path.resolve())
    root["target_dimensions"] = tuple(target_dimensions)
    root["first_era"] = spec["first_era"]
    animate_sprout(root, spec["start"], spec["duration"])
    return root, meshes, source_dimensions


def building_era(obj):
    parent_name = obj.parent.name if obj.parent else ""
    if parent_name.startswith("Buildings_Roman_State"):
        return 0
    if parent_name.startswith("Buildings_Medieval_State"):
        return 1
    if parent_name.startswith("Buildings_1700_State"):
        return 2
    if parent_name.startswith("Buildings_1850_State"):
        return 3
    if parent_name.startswith("Buildings_Modern_State"):
        return 4
    for era in range(5):
        if f"_{era}_State" in parent_name:
            return era
    return None


def point_in_rotated_box(x, y, center_x, center_y, half_x, half_y, rotation):
    dx = x - center_x
    dy = y - center_y
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    local_x = dx * cos_r + dy * sin_r
    local_y = -dx * sin_r + dy * cos_r
    return abs(local_x) <= half_x and abs(local_y) <= half_y


def chunk_intersects_spec(obj, spec):
    margin = spec["clearance"]
    half_x = spec["dimensions"][0] * 0.5 + margin
    half_y = spec["dimensions"][1] * 0.5 + margin
    center_x, center_y = spec["location"][:2]
    radius = math.hypot(half_x, half_y)
    bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_x = min(point.x for point in bounds)
    max_x = max(point.x for point in bounds)
    min_y = min(point.y for point in bounds)
    max_y = max(point.y for point in bounds)
    if max_x < center_x - radius or min_x > center_x + radius:
        return False
    if max_y < center_y - radius or min_y > center_y + radius:
        return False

    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        if point_in_rotated_box(
            point.x,
            point.y,
            center_x,
            center_y,
            half_x,
            half_y,
            spec["rotation"],
        ):
            return True
    return False


def clear_building_chunks(specs):
    bpy.context.scene.frame_set(1)
    candidates = [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and "_Chunk_" in obj.name
        and obj.name.startswith(("Buildings_", "Island_Cite_", "Island_Saint_Louis_"))
    ]
    removed = []
    for obj in candidates:
        era = building_era(obj)
        if era is None:
            continue
        if any(era >= spec["first_era"] and chunk_intersects_spec(obj, spec) for spec in specs):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def remove_gare_du_nord_shell():
    station = bpy.data.objects.get("Gare_du_Nord")
    if station is None:
        return
    for child in list(station.children):
        if "Platform" in child.name:
            continue
        remove_tree(child)


def placement_report(spec, root, meshes, source_dimensions):
    bpy.context.scene.frame_set(spec["start"] + spec["duration"] + 1)
    bpy.context.view_layer.update()
    minimum, maximum = mesh_world_bounds(meshes)
    dimensions = maximum - minimum
    return {
        "name": spec["name"],
        "source": str(spec["path"].resolve()),
        "source_dimensions": list(source_dimensions),
        "target_dimensions": list(spec["dimensions"]),
        "placed_bounds_min": list(minimum),
        "placed_bounds_max": list(maximum),
        "placed_dimensions": list(dimensions),
        "location": list(root.location),
        "rotation_degrees": math.degrees(root.rotation_euler[2]),
        "start_frame": spec["start"],
        "duration_frames": spec["duration"],
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "triangles": sum(len(obj.data.polygons) for obj in meshes),
    }


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    for spec in LANDMARK_SPECS:
        remove_named_tree(spec["name"])
        if spec["replace"]:
            remove_named_tree(spec["replace"])
    remove_gare_du_nord_shell()

    removed_chunks = clear_building_chunks(LANDMARK_SPECS)
    imported = []
    for spec in LANDMARK_SPECS:
        root, meshes, source_dimensions = import_landmark(spec)
        imported.append((spec, root, meshes, source_dimensions))

    bpy.context.scene.frame_set(bpy.context.scene.frame_end)
    bpy.context.view_layer.update()
    reports = [placement_report(*entry) for entry in imported]
    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output),
        "removed_building_chunks": len(removed_chunks),
        "removed_building_chunk_names": removed_chunks,
        "landmarks": reports,
    }

    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
