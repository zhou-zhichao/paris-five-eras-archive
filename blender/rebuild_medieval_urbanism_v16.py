import argparse
import importlib.util
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector


MAIN_BUILDING_COUNT = 5200
CITE_BUILDING_COUNT = 290
SAINT_LOUIS_BUILDING_COUNT = 180
FLOODPLAIN_SETBACK = 0.76
BANK_OUTER_WIDTH = 0.72
MEDIEVAL_ERA_INDEX = 1


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_modules():
    blender_dir = Path(__file__).resolve().parent
    build_scene = load_module(blender_dir / "build_scene.py", "paris_build_scene_v16")
    roman_v15 = load_module(
        blender_dir / "rebuild_roman_urbanism_v15.py",
        "paris_roman_urbanism_v15_helpers",
    )
    return build_scene, roman_v15


def river_parallel_points(bs, side, offset, xs, phase):
    points = []
    for x in xs:
        center = bs.river_center(x)
        half_width = bs.river_half_width(x)
        meander = side * 0.11 * math.sin(x * 0.31 + phase)
        points.append((x, center + side * (half_width + offset) + meander))
    return points


def medieval_streets(bs, roman_helpers):
    segments = []
    xs = [-17.5 + index * 1.25 for index in range(29)]
    offsets = [0.88, 2.1, 3.42, 4.82, 6.35, 8.05, 9.9, 11.85]
    for side in (-1.0, 1.0):
        for band_index, offset in enumerate(offsets):
            points = river_parallel_points(
                bs,
                side,
                offset,
                xs,
                phase=band_index * 0.71 + side * 0.4,
            )
            width = 0.12 if band_index == 0 else (0.095 if band_index in {2, 5} else 0.076)
            sides = (int(side),) if band_index == 0 else (-1, 1)
            segments.extend(
                roman_helpers.polyline_segments(
                    points,
                    width,
                    "main",
                    frontage=True,
                    sides=sides,
                    kind="riverfront" if band_index == 0 else "lane",
                )
            )

    cross_xs = [-15.6, -13.2, -10.8, -8.4, -6.0, -3.6, -1.2, 1.2, 3.6, 6.0, 8.4, 10.8, 13.2, 15.6]
    for side in (-1.0, 1.0):
        for index, x in enumerate(cross_xs):
            bank_y = bs.river_center(x) + side * (bs.river_half_width(x) + 0.84)
            outer_y = 13.8 if side > 0 else -14.4
            bend = 0.24 * math.sin(index * 1.71 + side)
            points = [
                (x, bank_y),
                (x + bend, bank_y + side * 3.2),
                (x - bend * 0.55, bank_y + side * 6.5),
                (x + bend * 0.8, outer_y),
            ]
            width = 0.132 if index in {4, 7, 10} else 0.082
            segments.extend(
                roman_helpers.polyline_segments(
                    points,
                    width,
                    "main",
                    frontage=True,
                    kind="radial" if width > 0.1 else "lane",
                )
            )

    gate_routes = [
        (-6.2, -14.8),
        (-2.4, -7.8),
        (1.2, 0.0),
        (4.8, 8.2),
        (7.4, 14.2),
    ]
    for side in (-1.0, 1.0):
        for route_index, (start_x, gate_x) in enumerate(gate_routes):
            bank_y = bs.river_center(start_x) + side * (bs.river_half_width(start_x) + 0.9)
            outer_y = 12.8 if side > 0 else -13.4
            points = [
                (start_x, bank_y),
                ((start_x * 2.0 + gate_x) / 3.0, bank_y + side * 3.8),
                ((start_x + gate_x * 2.0) / 3.0, bank_y + side * 7.6),
                (gate_x, outer_y),
            ]
            segments.extend(
                roman_helpers.polyline_segments(
                    points,
                    0.1 if route_index in {1, 3} else 0.086,
                    "main",
                    frontage=True,
                    kind="radial",
                )
            )

    islands = bs.load_geodata()["islands"]
    segments.extend(
        roman_helpers.island_axis_segments(
            islands["ile_de_la_cite"],
            "cite",
            longitudinal_count=3,
            cross_count=7,
        )
    )
    segments.extend(
        roman_helpers.island_axis_segments(
            islands["ile_saint_louis"],
            "saint_louis",
            longitudinal_count=2,
            cross_count=4,
        )
    )
    return segments


def zone_polygon(bs, zone):
    if zone == "main":
        return bs.CITY_POLYGONS[MEDIEVAL_ERA_INDEX]
    key = "ile_de_la_cite" if zone == "cite" else "ile_saint_louis"
    return bs.load_geodata()["islands"][key]


def zone_contains(bs, zone, x, y):
    if zone == "main":
        return bs.city_contains(MEDIEVAL_ERA_INDEX, x, y) and not bs.point_on_island(x, y)
    return bs.point_in_polygon(x, y, zone_polygon(bs, zone))


def style_for_candidate(rng, zone):
    if zone == "main":
        width = rng.uniform(0.14, 0.235)
        depth = rng.uniform(0.135, 0.225)
        height = rng.uniform(0.22, 0.49)
        if rng.random() < 0.075:
            height = rng.uniform(0.49, 0.62)
    elif zone == "cite":
        width = rng.uniform(0.082, 0.15)
        depth = rng.uniform(0.09, 0.165)
        height = rng.uniform(0.25, 0.55)
    else:
        width = rng.uniform(0.09, 0.16)
        depth = rng.uniform(0.095, 0.17)
        height = rng.uniform(0.21, 0.47)

    plan_values = ["standard", "annex", "courtyard", "tower", "chapel"]
    plan_weights = [0.79, 0.12, 0.035, 0.035, 0.02]
    if zone != "main":
        plan_weights = [0.93, 0.045, 0.01, 0.01, 0.005]
    plan_style = rng.choices(plan_values, weights=plan_weights, k=1)[0]
    roof_style = rng.choices(
        ["gable", "hip", "pyramid", "mansard", "flat"],
        weights=[0.59, 0.23, 0.08, 0.035, 0.065],
        k=1,
    )[0]
    if plan_style == "chapel":
        roof_style = "gable"
    return width, depth, height, plan_style, roof_style


def rowhouse_candidates(streets, zone, seed, bands, pass_index):
    candidates = []
    for street_index, street in enumerate(streets):
        if street["zone"] != zone or not street["frontage"]:
            continue
        start = Vector(street["start"])
        end = Vector(street["end"])
        vector = end - start
        length = vector.length
        if length < 0.26:
            continue
        tangent = vector.normalized()
        normal = Vector((-tangent.y, tangent.x))
        angle = math.atan2(tangent.y, tangent.x)
        for side in street["sides"]:
            for band_index, band in enumerate(bands):
                row_rng = random.Random(
                    seed * 1000003
                    + pass_index * 100003
                    + street_index * 1009
                    + side * 13
                    + band_index * 7919
                )
                cursor = 0.1 + row_rng.uniform(0.0, 0.08)
                while cursor < length - 0.1:
                    candidate_seed = row_rng.randrange(1, 2**31 - 1)
                    local_rng = random.Random(candidate_seed)
                    width, depth, height, plan_style, roof_style = style_for_candidate(
                        local_rng,
                        zone,
                    )
                    gap = local_rng.uniform(0.008, 0.025)
                    center_distance = cursor + width * 0.5
                    if center_distance + width * 0.5 > length - 0.08:
                        break
                    base = start + tangent * center_distance
                    offset = street["width"] * 0.5 + depth * 0.5 + 0.025 + band
                    center = base + normal * side * offset
                    rotation = angle if side > 0 else angle + math.pi
                    rotation += local_rng.uniform(-0.012, 0.012)
                    candidates.append(
                        {
                            "x": center.x,
                            "y": center.y,
                            "width": width,
                            "depth": depth,
                            "height": height,
                            "rotation": rotation,
                            "street_angle": angle,
                            "street_width": street["width"],
                            "street_index": street_index,
                            "zone": zone,
                            "band": band,
                            "priority": (
                                band_index * 2.0
                                + math.hypot(center.x, center.y) * 0.018
                                + local_rng.random() * 0.42
                                + pass_index * 0.12
                            ),
                            "seed": candidate_seed,
                            "plan_style": plan_style,
                            "roof_style": roof_style,
                            "timber": local_rng.random() < (0.31 if zone == "cite" else 0.23),
                            "chimney": local_rng.random() < 0.38,
                        }
                    )
                    cursor += width + gap
    return candidates


def clear_of_streets(bs, placement, streets, extra=0.012):
    half_width, half_depth = bs.house_half_extents(
        placement["width"],
        placement["depth"],
        placement["plan_style"],
    )
    for street in streets:
        if street["zone"] != placement["zone"]:
            continue
        angle = math.atan2(
            street["end"][1] - street["start"][1],
            street["end"][0] - street["start"][0],
        )
        extent = bs.projected_extent(
            half_width,
            half_depth,
            placement["rotation"],
            angle + math.pi * 0.5,
        )
        distance = bs.point_segment_distance(
            placement["x"],
            placement["y"],
            street["start"],
            street["end"],
        )[0]
        if distance < street["width"] * 0.5 + extent + extra:
            return False
    return True


def reserved_footprints(zone):
    if zone == "cite":
        return [(0.15, 0.25, 1.28, 0.82, -0.55)]
    return []


def generate_placements(bs, streets, zone, target_count, seed):
    polygon = zone_polygon(bs, zone)
    footprint_index = load_footprint_index(bs)
    for footprint in reserved_footprints(zone):
        footprint_index.add(footprint)

    candidates = []
    pass_bands = (
        (0.0,),
        (0.18 if zone != "main" else 0.22,),
        (0.34 if zone != "main" else 0.43,),
        (0.5 if zone != "main" else 0.64,),
    )
    for pass_index, bands in enumerate(pass_bands):
        candidates.extend(
            rowhouse_candidates(
                streets,
                zone,
                seed + pass_index * 1009,
                bands,
                pass_index,
            )
        )
    candidates.sort(key=lambda item: item["priority"])

    accepted = []
    for candidate in candidates:
        x = candidate["x"]
        y = candidate["y"]
        half_width, half_depth = bs.house_half_extents(
            candidate["width"],
            candidate["depth"],
            candidate["plan_style"],
        )
        footprint_radius = math.hypot(half_width, half_depth)
        if not zone_contains(bs, zone, x, y):
            continue
        edge_margin = 0.09 if zone == "main" else 0.08
        if bs.polygon_edge_distance(x, y, polygon) < footprint_radius + edge_margin:
            continue
        if zone == "main" and bs.river_clearance(x, y) < FLOODPLAIN_SETBACK + footprint_radius:
            continue
        if not clear_of_streets(bs, candidate, streets):
            continue
        footprint = (x, y, half_width, half_depth, candidate["rotation"])
        if not footprint_index.can_add(footprint):
            continue
        footprint_index.add(footprint)
        candidate["half_width"] = half_width
        candidate["half_depth"] = half_depth
        accepted.append(candidate)
        if len(accepted) >= target_count:
            break

    if len(accepted) < target_count:
        raise RuntimeError(
            f"Only generated {len(accepted)}/{target_count} {zone} medieval buildings"
        )
    return accepted, footprint_index


def load_footprint_index(bs):
    class SpatialFootprints:
        def __init__(self, cell_size=0.7):
            self.cell_size = cell_size
            self.items = []
            self.grid = {}

        def cells(self, footprint):
            x, y, half_width, half_depth, _rotation = footprint
            radius = math.hypot(half_width, half_depth)
            for cell_x in range(
                math.floor((x - radius) / self.cell_size),
                math.floor((x + radius) / self.cell_size) + 1,
            ):
                for cell_y in range(
                    math.floor((y - radius) / self.cell_size),
                    math.floor((y + radius) / self.cell_size) + 1,
                ):
                    yield cell_x, cell_y

        def can_add(self, footprint):
            nearby = set()
            for cell in self.cells(footprint):
                nearby.update(self.grid.get(cell, ()))
            return not any(
                bs.footprints_overlap(footprint, self.items[index], gap=0.004)
                for index in nearby
            )

        def add(self, footprint):
            index = len(self.items)
            self.items.append(footprint)
            for cell in self.cells(footprint):
                self.grid.setdefault(cell, []).append(index)

        def circle_overlaps(self, x, y, radius):
            query = (x, y, radius, radius, 0.0)
            nearby = set()
            for cell in self.cells(query):
                nearby.update(self.grid.get(cell, ()))
            return any(
                bs.circle_overlaps_footprint(
                    x,
                    y,
                    radius,
                    self.items[index],
                    gap=0.025,
                )
                for index in nearby
            )

    return SpatialFootprints()


def placement_growth_key(bs, placement):
    progress = bs.growth_progress(
        placement["x"],
        placement["y"],
        MEDIEVAL_ERA_INDEX,
        0.5,
    )
    angle = math.atan2(placement["y"], placement["x"])
    return (round(progress * 34), placement["band"], angle, placement["x"], placement["y"])


def add_prism_geometry(
    vertices,
    faces,
    material_ids,
    x,
    y,
    width,
    depth,
    bottom,
    top,
    rotation,
    material_id,
):
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    start = len(vertices)
    for z in (bottom, top):
        for local_x, local_y in (
            (-width * 0.5, -depth * 0.5),
            (width * 0.5, -depth * 0.5),
            (width * 0.5, depth * 0.5),
            (-width * 0.5, depth * 0.5),
        ):
            vertices.append(
                (
                    x + local_x * cos_r - local_y * sin_r,
                    y + local_x * sin_r + local_y * cos_r,
                    z,
                )
            )
    faces.extend(
        [
            (start, start + 1, start + 5, start + 4),
            (start + 1, start + 2, start + 6, start + 5),
            (start + 2, start + 3, start + 7, start + 6),
            (start + 3, start, start + 4, start + 7),
            (start + 4, start + 5, start + 6, start + 7),
        ]
    )
    material_ids.extend([material_id] * 5)


def add_timber_details(bs, vertices, faces, material_ids, placement, timber_id):
    x = placement["x"]
    y = placement["y"]
    width = placement["width"]
    depth = placement["depth"]
    height = placement["height"]
    rotation = placement["rotation"]
    panel_offset = 0.009
    for facade_side in (-1.0, 1.0):
        local_y = facade_side * (depth * 0.5 + panel_offset)
        for local_x in (-width * 0.34, 0.0, width * 0.34):
            bs.add_vertical_panel_geometry(
                vertices,
                faces,
                material_ids,
                x,
                y,
                height * 0.58,
                0.012,
                height * 0.68,
                rotation,
                local_x,
                local_y,
                "x",
                timber_id,
            )
        for z in (height * 0.34, height * 0.61, height * 0.82):
            bs.add_vertical_panel_geometry(
                vertices,
                faces,
                material_ids,
                x,
                y,
                z,
                width * 0.84,
                0.012,
                rotation,
                0.0,
                local_y,
                "x",
                timber_id,
            )


def ensure_timber_material():
    material = bpy.data.materials.get("Medieval_Dark_Timber")
    if material is None:
        material = bpy.data.materials.new("Medieval_Dark_Timber")
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF") or next(
        (
            node
            for node in material.node_tree.nodes
            if node.type == "BSDF_PRINCIPLED"
        ),
        None,
    )
    if principled is None:
        principled = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        output = next(
            (
                node
                for node in material.node_tree.nodes
                if node.type == "OUTPUT_MATERIAL"
            ),
            None,
        )
        if output is None:
            output = material.node_tree.nodes.new("ShaderNodeOutputMaterial")
        material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    principled.inputs["Base Color"].default_value = (0.11, 0.045, 0.018, 1.0)
    principled.inputs["Roughness"].default_value = 0.46
    if "Coat Weight" in principled.inputs:
        principled.inputs["Coat Weight"].default_value = 0.08
    return material


def rebuild_building_group(bs, roman_helpers, prefix, placements, timber_material):
    objects = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith(prefix)),
        key=lambda obj: (roman_helpers.action_start_frame(obj), obj.name),
    )
    if not objects:
        raise RuntimeError(f"No target objects for {prefix}")
    placements = sorted(placements, key=lambda item: placement_growth_key(bs, item))
    groups = roman_helpers.evenly_partition(placements, len(objects))
    for obj, group in zip(objects, groups):
        materials = [slot.material for slot in obj.material_slots]
        if timber_material not in materials:
            materials.append(timber_material)
        timber_id = materials.index(timber_material)
        vertices = []
        faces = []
        material_ids = []
        for placement in group:
            rng = random.Random(placement["seed"])
            wall_id, roof_id = bs.building_material_ids(rng, "medieval")
            bs.add_house_geometry(
                vertices,
                faces,
                material_ids,
                placement["x"],
                placement["y"],
                placement["width"],
                placement["depth"],
                placement["height"],
                placement["rotation"],
                wall_id,
                roof_id,
                placement["roof_style"],
                placement["plan_style"],
                "medieval",
                rng,
            )
            if placement["timber"] and placement["plan_style"] == "standard":
                add_timber_details(
                    bs,
                    vertices,
                    faces,
                    material_ids,
                    placement,
                    timber_id,
                )
            if placement["chimney"]:
                offset_x = rng.uniform(-placement["width"] * 0.27, placement["width"] * 0.27)
                offset_y = rng.uniform(-placement["depth"] * 0.18, placement["depth"] * 0.18)
                chimney_x, chimney_y = bs.rotated_offset(
                    placement["x"],
                    placement["y"],
                    placement["rotation"],
                    offset_x,
                    offset_y,
                )
                size = min(0.035, max(0.018, placement["width"] * 0.11))
                add_prism_geometry(
                    vertices,
                    faces,
                    material_ids,
                    chimney_x,
                    chimney_y,
                    size,
                    size * 0.9,
                    placement["height"] * 0.83,
                    placement["height"] + 0.12,
                    placement["rotation"],
                    6,
                )
        roman_helpers.replace_mesh(obj, vertices, faces, material_ids, materials)
    return len(objects)


def point_in_rotated_box(x, y, footprint, margin=0.0):
    center_x, center_y, half_width, half_depth, rotation = footprint
    delta_x = x - center_x
    delta_y = y - center_y
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    local_x = delta_x * cos_r + delta_y * sin_r
    local_y = -delta_x * sin_r + delta_y * cos_r
    return abs(local_x) <= half_width + margin and abs(local_y) <= half_depth + margin


def create_road_pieces(bs, roman_helpers, streets):
    pieces = []
    notre_footprint = reserved_footprints("cite")[0]
    for street in streets:
        start = Vector(street["start"])
        end = Vector(street["end"])
        vector = end - start
        length = vector.length
        if length < 0.04:
            continue
        piece_count = max(1, math.ceil(length / 0.38))
        polygon = zone_polygon(bs, street["zone"])
        for index in range(piece_count):
            piece_start = start.lerp(end, index / piece_count)
            piece_end = start.lerp(end, (index + 1) / piece_count)
            midpoint = (piece_start + piece_end) * 0.5
            if street["zone"] == "main":
                if not zone_contains(bs, "main", midpoint.x, midpoint.y):
                    continue
                clearance = bs.river_clearance(midpoint.x, midpoint.y)
                minimum = BANK_OUTER_WIDTH - 0.05 if street["kind"] == "riverfront" else BANK_OUTER_WIDTH + 0.02
                if clearance < minimum:
                    continue
                z = -0.026
            else:
                if not bs.point_in_polygon(midpoint.x, midpoint.y, polygon):
                    continue
                if street["zone"] == "cite" and point_in_rotated_box(
                    midpoint.x,
                    midpoint.y,
                    notre_footprint,
                    margin=street["width"] + 0.08,
                ):
                    continue
                z = 0.061
            pieces.append(
                {
                    "start": tuple(piece_start),
                    "end": tuple(piece_end),
                    "width": street["width"],
                    "z": z,
                    "progress": bs.road_growth_progress(
                        midpoint.x,
                        midpoint.y,
                        MEDIEVAL_ERA_INDEX,
                        0.5,
                    ),
                    "angle": math.atan2(midpoint.y, midpoint.x),
                }
            )
    return sorted(pieces, key=lambda item: (round(item["progress"] * 40), item["angle"]))


def rebuild_medieval_roads(bs, roman_helpers, streets):
    objects = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith("Roads_1_Chunk_")),
        key=lambda obj: (roman_helpers.road_action_start_frame(obj), obj.name),
    )
    pieces = create_road_pieces(bs, roman_helpers, streets)
    if len(pieces) < len(objects):
        raise RuntimeError(f"Only {len(pieces)} road pieces for {len(objects)} road chunks")
    groups = roman_helpers.evenly_partition(pieces, len(objects))
    for obj, group in zip(objects, groups):
        old_mesh = obj.data
        old_mesh_name = old_mesh.name
        old_materials = list(old_mesh.materials)
        old_shape_action = (
            old_mesh.shape_keys.animation_data.action
            if old_mesh.shape_keys and old_mesh.shape_keys.animation_data
            else None
        )
        vertices = []
        faces = []
        for piece in group:
            start = len(vertices)
            vertices.extend(
                tuple(vertex)
                for vertex in roman_helpers.road_piece_geometry(
                    piece["start"],
                    piece["end"],
                    piece["width"],
                    piece["z"],
                )
            )
            faces.append((start, start + 1, start + 2, start + 3))
        mesh = bpy.data.meshes.new(f"{old_mesh_name}_v16")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        for material in old_materials:
            mesh.materials.append(material)
        obj.data = mesh
        obj.shape_key_add(name="Basis")
        collapsed = obj.shape_key_add(name="Road_Draw_Collapsed")
        for start in range(0, len(vertices), 4):
            collapsed.data[start + 1].co = collapsed.data[start].co
            collapsed.data[start + 2].co = collapsed.data[start + 3].co
        if old_shape_action:
            mesh.shape_keys.animation_data_create()
            mesh.shape_keys.animation_data.action = old_shape_action
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
        mesh.name = old_mesh_name
    return len(objects), len(pieces)


def object_visible_start(obj):
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return None
    frames = sorted(
        {
            round(float(point.co.x), 6)
            for curve in action.fcurves
            for point in curve.keyframe_points
            if point.co.x > 1.5
        }
    )
    if not frames:
        return None
    return frames[1] if len(frames) > 1 else frames[0]


def shift_object_action(obj, delta):
    action = obj.animation_data.action if obj.animation_data else None
    if action is None or abs(delta) < 0.001:
        return
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            if point.co.x <= 1.5:
                continue
            point.co.x += delta
            point.handle_left.x += delta
            point.handle_right.x += delta
        curve.update()


def set_action_interpolation(obj):
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            if curve.data_path == "hide_render":
                point.interpolation = "CONSTANT"
            else:
                point.interpolation = "BEZIER"
                point.handle_left_type = "AUTO_CLAMPED"
                point.handle_right_type = "AUTO_CLAMPED"


def local_axis_extent(obj, axis_index):
    if obj.type != "MESH" or not obj.data.vertices:
        return 0.1
    coordinates = [vertex.co[axis_index] for vertex in obj.data.vertices]
    return max(coordinates) - min(coordinates)


def animate_anchored_axis(obj, start_frame, duration, axis_index, forward_world):
    final_location = Vector(obj.location)
    final_scale = Vector(obj.scale)
    axis_local = Vector((0.0, 0.0, 0.0))
    axis_local[axis_index] = 1.0
    axis_world = (obj.matrix_world.to_3x3() @ axis_local).normalized()
    if axis_world.dot(forward_world) < 0.0:
        axis_world.negate()
    if obj.parent:
        axis_parent = (obj.parent.matrix_world.inverted().to_3x3() @ axis_world).normalized()
    else:
        axis_parent = axis_world
    extent = local_axis_extent(obj, axis_index) * abs(final_scale[axis_index])
    initial_amount = 0.015
    initial_scale = final_scale.copy()
    initial_scale[axis_index] = max(0.001, final_scale[axis_index] * initial_amount)
    initial_location = final_location - axis_parent * extent * 0.5 * (1.0 - initial_amount)

    obj.animation_data_clear()
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=1)
    obj.keyframe_insert(data_path="hide_render", frame=start_frame - 1)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=start_frame)
    obj.location = initial_location
    obj.scale = initial_scale
    obj.keyframe_insert(data_path="location", frame=start_frame)
    obj.keyframe_insert(data_path="scale", frame=start_frame)
    obj.location = final_location
    obj.scale = final_scale
    obj.keyframe_insert(data_path="location", frame=start_frame + duration)
    obj.keyframe_insert(data_path="scale", frame=start_frame + duration)
    set_action_interpolation(obj)


def retime_medieval_bridge_supports():
    bridge_names = (
        "Bridge_ile_de_la_cite_-2.0_1",
        "Bridge_ile_de_la_cite_-5.4_-1",
        "Bridge_ile_de_la_cite_0.7_-1",
        "Bridge_ile_de_la_cite_1.0_1",
    )
    report = {}
    bpy.context.scene.frame_set(1200)
    for bridge_name in bridge_names:
        root = bpy.data.objects.get(bridge_name)
        if root is None:
            continue
        decks = sorted(
            (child for child in root.children_recursive if "_Deck_" in child.name),
            key=lambda child: int(child.name.rsplit("_", 1)[-1]),
        )
        piers = sorted(
            (
                child
                for child in root.children_recursive
                if "_Pier_" in child.name and "PierCap" not in child.name
            ),
            key=lambda child: int(child.name.rsplit("_", 1)[-1]),
        )
        caps = sorted(
            (child for child in root.children_recursive if "_PierCap_" in child.name),
            key=lambda child: int(child.name.rsplit("_", 1)[-1]),
        )
        rails = sorted(
            (child for child in root.children_recursive if "_Rail_" in child.name),
            key=lambda child: (
                int(child.name.split("_Rail_", 1)[1].split("_", 1)[0]),
                child.name,
            ),
        )
        original_start = min(object_visible_start(deck) for deck in decks)
        path_direction = (Vector(decks[-1].location) - Vector(decks[0].location)).normalized()
        deck_start_by_index = {}
        events = []
        for deck_index, deck in enumerate(decks):
            start_frame = round(original_start + deck_index * 6)
            deck_start_by_index[deck_index] = start_frame
            animate_anchored_axis(
                deck,
                start_frame,
                duration=8,
                axis_index=1,
                forward_world=path_direction,
            )
            events.append({"object": deck.name, "start": start_frame, "type": "deck"})
        for rail in rails:
            rail_index = int(rail.name.split("_Rail_", 1)[1].split("_", 1)[0])
            start_frame = deck_start_by_index[rail_index] + 2
            animate_anchored_axis(
                rail,
                start_frame,
                duration=7,
                axis_index=1,
                forward_world=path_direction,
            )
            events.append({"object": rail.name, "start": start_frame, "type": "rail"})
        for support in piers + caps:
            support_location = Vector(support.location)
            nearest_index = min(
                range(len(decks)),
                key=lambda index: (Vector(decks[index].location) - support_location).length,
            )
            start_frame = deck_start_by_index[nearest_index] + 4
            animate_anchored_axis(
                support,
                start_frame,
                duration=8,
                axis_index=2,
                forward_world=Vector((0.0, 0.0, 1.0)),
            )
            events.append(
                {
                    "object": support.name,
                    "start": start_frame,
                    "type": "pier_cap" if "PierCap" in support.name else "pier",
                }
            )
        report[bridge_name] = events
    bpy.context.scene.frame_set(1)
    return report


def combine_placement_index(bs, placement_groups):
    index = load_footprint_index(bs)
    for placements in placement_groups:
        for placement in placements:
            index.add(
                (
                    placement["x"],
                    placement["y"],
                    placement["half_width"],
                    placement["half_depth"],
                    placement["rotation"],
                )
            )
    return index


def clear_persistent_tree_intersections(roman_helpers, footprint_index):
    forest = bpy.data.objects.get("Forest_Persistent")
    if forest is None or forest.type != "MESH" or forest.data.shape_keys:
        return {"component_count": 0, "removed_components": 0}
    mesh = forest.data
    vertex_count = len(mesh.vertices)
    parent = list(range(vertex_count))

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(first, second):
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    for polygon in mesh.polygons:
        vertices = polygon.vertices
        for vertex_index in vertices[1:]:
            union(vertices[0], vertex_index)

    components = {}
    for vertex in mesh.vertices:
        components.setdefault(find(vertex.index), []).append(vertex.index)
    removed_roots = set()
    for root, indices in components.items():
        min_x = min(mesh.vertices[index].co.x for index in indices)
        max_x = max(mesh.vertices[index].co.x for index in indices)
        min_y = min(mesh.vertices[index].co.y for index in indices)
        max_y = max(mesh.vertices[index].co.y for index in indices)
        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5
        radius = max(0.05, math.hypot(max_x - min_x, max_y - min_y) * 0.5)
        if footprint_index.circle_overlaps(center_x, center_y, radius):
            removed_roots.add(root)

    keep_vertex = [find(index) not in removed_roots for index in range(vertex_count)]
    remap = {}
    vertices = []
    for vertex in mesh.vertices:
        if keep_vertex[vertex.index]:
            remap[vertex.index] = len(vertices)
            vertices.append(tuple(vertex.co))
    faces = []
    material_ids = []
    for polygon in mesh.polygons:
        if all(keep_vertex[index] for index in polygon.vertices):
            faces.append(tuple(remap[index] for index in polygon.vertices))
            material_ids.append(polygon.material_index)
    materials = list(mesh.materials)
    roman_helpers.replace_mesh(forest, vertices, faces, material_ids, materials)
    return {
        "component_count": len(components),
        "removed_components": len(removed_roots),
        "remaining_vertices": len(vertices),
    }


def alignment_error(placement):
    delta = abs((placement["rotation"] - placement["street_angle"]) % math.pi)
    return min(delta, math.pi - delta)


def main():
    args = parse_args()
    bs, roman_helpers = project_modules()
    streets = medieval_streets(bs, roman_helpers)
    main_placements, _ = generate_placements(
        bs,
        streets,
        "main",
        MAIN_BUILDING_COUNT,
        16201,
    )
    cite_placements, _ = generate_placements(
        bs,
        streets,
        "cite",
        CITE_BUILDING_COUNT,
        16202,
    )
    saint_placements, _ = generate_placements(
        bs,
        streets,
        "saint_louis",
        SAINT_LOUIS_BUILDING_COUNT,
        16203,
    )

    road_object_count, road_piece_count = rebuild_medieval_roads(
        bs,
        roman_helpers,
        streets,
    )
    bridge_retime_report = retime_medieval_bridge_supports()
    timber_material = ensure_timber_material()
    building_object_counts = {
        "main": rebuild_building_group(
            bs,
            roman_helpers,
            "Buildings_Medieval_State_Chunk_",
            main_placements,
            timber_material,
        ),
        "cite": rebuild_building_group(
            bs,
            roman_helpers,
            "Island_Cite_1_State_Chunk_",
            cite_placements,
            timber_material,
        ),
        "saint_louis": rebuild_building_group(
            bs,
            roman_helpers,
            "Island_Saint_Louis_1_State_Chunk_",
            saint_placements,
            timber_material,
        ),
    }

    all_placements = main_placements + cite_placements + saint_placements
    footprint_index = combine_placement_index(
        bs,
        (main_placements, cite_placements, saint_placements),
    )
    forest_report = clear_persistent_tree_intersections(
        roman_helpers,
        footprint_index,
    )

    alignment_errors = [alignment_error(placement) for placement in all_placements]
    river_clearances = [
        bs.river_clearance(placement["x"], placement["y"])
        for placement in main_placements
    ]
    plan_counts = Counter(placement["plan_style"] for placement in all_placements)
    roof_counts = Counter(placement["roof_style"] for placement in all_placements)
    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output_blend.resolve()),
        "streets": {
            "segment_count": len(streets),
            "road_object_count": road_object_count,
            "road_piece_count": road_piece_count,
        },
        "buildings": {
            "counts": {
                "main": len(main_placements),
                "cite": len(cite_placements),
                "saint_louis": len(saint_placements),
            },
            "object_counts": building_object_counts,
            "minimum_mainland_river_clearance": min(river_clearances),
            "mean_alignment_error_degrees": math.degrees(
                sum(alignment_errors) / len(alignment_errors)
            ),
            "maximum_alignment_error_degrees": math.degrees(max(alignment_errors)),
            "timber_facade_count": sum(placement["timber"] for placement in all_placements),
            "chimney_count": sum(placement["chimney"] for placement in all_placements),
            "plan_counts": dict(plan_counts),
            "roof_counts": dict(roof_counts),
        },
        "forest": forest_report,
        "bridge_support_retime": bridge_retime_report,
    }

    bpy.context.scene.frame_set(1)
    args.output_blend = args.output_blend.resolve()
    args.output_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output_blend))
    args.report = args.report.resolve()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
