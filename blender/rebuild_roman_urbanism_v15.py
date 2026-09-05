import argparse
import importlib.util
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


WATER_Z = -0.13
RIVERBED_Z = -0.275
LAND_Z = -0.035
BANK_OUTER_WIDTH = 0.72
MAIN_FLOODPLAIN_SETBACK = 0.72
MAIN_BUILDING_COUNT = 1800
CITE_BUILDING_COUNT = 400
SAINT_LOUIS_BUILDING_COUNT = 160


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def load_build_scene_module():
    module_path = Path(__file__).with_name("build_scene.py")
    spec = importlib.util.spec_from_file_location("paris_build_scene_v15", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def ensure_material(name, base_color, roughness):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is None:
        principled = next(
            node
            for node in material.node_tree.nodes
            if node.type == "BSDF_PRINCIPLED"
        )
    principled.inputs["Base Color"].default_value = (*base_color, 1.0)
    principled.inputs["Roughness"].default_value = roughness
    return material


def replace_mesh(obj, vertices, faces, material_ids, materials, mesh_name=None):
    old_mesh = obj.data
    old_name = old_mesh.name
    mesh = bpy.data.meshes.new(mesh_name or f"{old_name}_v15")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for material in materials:
        if material is not None:
            mesh.materials.append(material)
    for polygon, material_id in zip(mesh.polygons, material_ids):
        polygon.material_index = min(material_id, max(0, len(mesh.materials) - 1))
        polygon.use_smooth = False
    obj.data = mesh
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    mesh.name = old_name
    return mesh


def polyline_segments(
    points,
    width,
    zone,
    frontage=True,
    sides=(-1, 1),
    kind="grid",
):
    return [
        {
            "start": tuple(start),
            "end": tuple(end),
            "width": width,
            "zone": zone,
            "frontage": frontage,
            "sides": sides,
            "kind": kind,
        }
        for start, end in zip(points, points[1:])
    ]


def grid_to_world(u, v, center=(0.0, -1.5), angle=math.radians(-4.0)):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (
        center[0] + u * cos_a - v * sin_a,
        center[1] + u * sin_a + v * cos_a,
    )


def island_axis_segments(polygon, zone, longitudinal_count, cross_count):
    if zone == "cite":
        axis_start = Vector((-7.35, 5.02))
        axis_end = Vector((1.68, -1.14))
        half_cross = 1.36
    else:
        axis_start = Vector((2.55, 0.36))
        axis_end = Vector((7.42, -3.55))
        half_cross = 0.86
    axis = (axis_end - axis_start).normalized()
    normal = Vector((-axis.y, axis.x))
    segments = []
    offsets = [
        (index - (longitudinal_count - 1) * 0.5) * 0.42
        for index in range(longitudinal_count)
    ]
    for offset in offsets:
        start = axis_start + normal * offset
        end = axis_end + normal * offset
        segments.extend(
            polyline_segments(
                [start, end],
                0.085 if abs(offset) > 0.05 else 0.11,
                zone,
                frontage=True,
            )
        )
    for index in range(cross_count):
        amount = (index + 1) / (cross_count + 1)
        center = axis_start.lerp(axis_end, amount)
        start = center - normal * half_cross
        end = center + normal * half_cross
        segments.extend(
            polyline_segments([start, end], 0.075, zone, frontage=False)
        )
    return segments


def clean_roman_streets(bs):
    segments = []
    grid_values = [-8.1, -6.75, -5.4, -4.05, -2.7, -1.35, 0.0, 1.35, 2.7, 4.05, 5.4, 6.75, 8.1]
    for value in grid_values:
        width = 0.12 if abs(value) < 0.1 or abs(abs(value) - 4.05) < 0.1 else 0.088
        segments.extend(
            polyline_segments(
                [grid_to_world(-9.2, value), grid_to_world(9.2, value)],
                width,
                "main",
            )
        )
        segments.extend(
            polyline_segments(
                [grid_to_world(value, -10.1), grid_to_world(value, 7.8)],
                width,
                "main",
            )
        )

    riverfront_xs = [-9.0, -7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0, 7.0, 9.0]
    for side in (-1.0, 1.0):
        points = [
            (
                x,
                bs.river_center(x)
                + side * (bs.river_half_width(x) + BANK_OUTER_WIDTH + 0.12),
            )
            for x in riverfront_xs
        ]
        segments.extend(
            polyline_segments(
                points,
                0.105,
                "main",
                frontage=True,
                sides=(side,),
                kind="riverfront",
            )
        )

    segments.extend(
        island_axis_segments(bs.load_geodata()["islands"]["ile_de_la_cite"], "cite", 3, 5)
    )
    segments.extend(
        island_axis_segments(
            bs.load_geodata()["islands"]["ile_saint_louis"],
            "saint_louis",
            2,
            3,
        )
    )
    return segments


def point_segment_distance(x, y, start, end):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-10:
        return math.hypot(x - x1, y - y1)
    amount = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length_sq))
    return math.hypot(x - (x1 + dx * amount), y - (y1 + dy * amount))


def segment_angle(segment):
    return math.atan2(
        segment["end"][1] - segment["start"][1],
        segment["end"][0] - segment["start"][0],
    )


def zone_contains(bs, zone, x, y):
    if zone == "main":
        return bs.city_contains(0, x, y) and not bs.point_on_island(x, y)
    polygon_key = "ile_de_la_cite" if zone == "cite" else "ile_saint_louis"
    return bs.point_in_polygon(x, y, bs.load_geodata()["islands"][polygon_key])


class FootprintIndex:
    def __init__(self, bs, cell_size=0.7):
        self.bs = bs
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
            self.bs.footprints_overlap(footprint, self.items[index], gap=0.003)
            for index in nearby
        )

    def add(self, footprint):
        index = len(self.items)
        self.items.append(footprint)
        for cell in self.cells(footprint):
            self.grid.setdefault(cell, []).append(index)


def clear_of_all_streets(placement, streets, extra=0.018):
    x = placement["x"]
    y = placement["y"]
    rotation = placement["rotation"]
    half_width = placement["width"] * 0.5
    half_depth = placement["depth"] * 0.5
    for street in streets:
        if street["zone"] != placement["zone"]:
            continue
        angle = segment_angle(street)
        extent = abs(math.sin(angle - rotation)) * half_width + abs(
            math.cos(angle - rotation)
        ) * half_depth
        if point_segment_distance(x, y, street["start"], street["end"]) < (
            street["width"] * 0.5 + extent + extra
        ):
            return False
    return True


def placement_candidates(streets, zone, seed, spacing, bands):
    rng = random.Random(seed)
    candidates = []
    for street_index, street in enumerate(streets):
        if street["zone"] != zone or not street["frontage"]:
            continue
        start = Vector(street["start"])
        end = Vector(street["end"])
        vector = end - start
        length = vector.length
        if length < 0.2:
            continue
        tangent = vector.normalized()
        normal = Vector((-tangent.y, tangent.x))
        angle = math.atan2(tangent.y, tangent.x)
        sample_count = max(1, math.floor((length - 0.24) / spacing))
        phase_offset = rng.uniform(-0.06, 0.06)
        for sample_index in range(sample_count):
            distance = 0.12 + (sample_index + 0.5) * (length - 0.24) / sample_count
            base = start + tangent * distance
            for side in street["sides"]:
                for band_index, band in enumerate(bands):
                    local_rng = random.Random(
                        seed * 1000003
                        + street_index * 1009
                        + sample_index * 37
                        + side * 13
                        + band_index * 7919
                    )
                    width = local_rng.uniform(0.125, 0.205)
                    depth = local_rng.uniform(0.105, 0.17)
                    height = local_rng.uniform(0.145, 0.285)
                    offset = street["width"] * 0.5 + depth * 0.5 + 0.032 + band
                    jitter_along = local_rng.uniform(-0.022, 0.022) + phase_offset
                    center = base + tangent * jitter_along + normal * side * offset
                    rotation = angle if side > 0 else angle + math.pi
                    rotation += local_rng.uniform(-0.008, 0.008)
                    candidates.append(
                        {
                            "x": center.x,
                            "y": center.y,
                            "width": width,
                            "depth": depth,
                            "height": height,
                            "rotation": rotation,
                            "street_angle": angle,
                            "zone": zone,
                            "priority": local_rng.random() + band_index * 0.16,
                            "seed": local_rng.randrange(1, 2**31 - 1),
                        }
                    )
    rng.shuffle(candidates)
    candidates.sort(key=lambda item: item["priority"])
    return candidates


def generate_placements(bs, streets, zone, target_count, seed):
    if zone == "main":
        spacing = 0.165
        bands = (0.0, 0.18, 0.36, 0.54)
        polygon = bs.CITY_POLYGONS[0]
    elif zone == "cite":
        spacing = 0.145
        bands = (0.0, 0.17, 0.34)
        polygon = bs.load_geodata()["islands"]["ile_de_la_cite"]
    else:
        spacing = 0.145
        bands = (0.0, 0.17, 0.34)
        polygon = bs.load_geodata()["islands"]["ile_saint_louis"]

    index = FootprintIndex(bs)
    if zone == "main":
        for reserved in (
            (6.4, 6.25, 1.55, 1.08, 0.0),
            (1.4, -8.5, 1.45, 1.02, 0.0),
        ):
            index.add(reserved)

    accepted = []

    def try_accept(candidate):
        x = candidate["x"]
        y = candidate["y"]
        half_width = candidate["width"] * 0.5
        half_depth = candidate["depth"] * 0.5
        footprint_radius = math.hypot(half_width, half_depth)
        if not zone_contains(bs, zone, x, y):
            return False
        if bs.polygon_edge_distance(x, y, polygon) < footprint_radius + (
            0.07 if zone == "main" else 0.1
        ):
            return False
        if zone == "main" and bs.river_clearance(x, y) < (
            MAIN_FLOODPLAIN_SETBACK + footprint_radius
        ):
            return False
        if not clear_of_all_streets(candidate, streets):
            return False
        footprint = (
            x,
            y,
            half_width,
            half_depth,
            candidate["rotation"],
        )
        if not index.can_add(footprint):
            return False
        index.add(footprint)
        accepted.append(candidate)
        return True

    candidates = placement_candidates(streets, zone, seed, spacing, bands)
    for candidate in candidates:
        try_accept(candidate)
        if len(accepted) >= target_count:
            break

    if len(accepted) < target_count:
        infill_rng = random.Random(seed + 91001)
        infill = []
        zone_streets = [street for street in streets if street["zone"] == zone]

        def nearest_angle(x, y):
            nearest = min(
                zone_streets,
                key=lambda street: point_segment_distance(
                    x, y, street["start"], street["end"]
                ),
            )
            return segment_angle(nearest)

        if zone == "main":
            u_values = [(-8.85 + index * 0.1) for index in range(178)]
            v_values = [(-9.7 + index * 0.1) for index in range(175)]
            points = [grid_to_world(u, v) for v in v_values for u in u_values]
        else:
            if zone == "cite":
                axis_start = Vector((-7.35, 5.02))
                axis_end = Vector((1.68, -1.14))
                cross_limit = 1.42
            else:
                axis_start = Vector((2.55, 0.36))
                axis_end = Vector((7.42, -3.55))
                cross_limit = 0.92
            axis_vector = axis_end - axis_start
            axis = axis_vector.normalized()
            normal = Vector((-axis.y, axis.x))
            points = []
            longitudinal_steps = math.ceil(axis_vector.length / 0.1)
            cross_steps = math.ceil(cross_limit * 2.0 / 0.1)
            for cross_index in range(cross_steps + 1):
                cross = -cross_limit + cross_index * (cross_limit * 2.0 / cross_steps)
                for longitudinal_index in range(longitudinal_steps + 1):
                    amount = longitudinal_index / longitudinal_steps
                    point = axis_start.lerp(axis_end, amount) + normal * cross
                    points.append(tuple(point))

        for point_index, (x, y) in enumerate(points):
            local_rng = random.Random(seed * 100003 + point_index * 97)
            angle = nearest_angle(x, y)
            width = local_rng.uniform(0.072, 0.105)
            depth = local_rng.uniform(0.07, 0.1)
            rotation = angle + local_rng.uniform(-0.006, 0.006)
            infill.append(
                {
                    "x": x,
                    "y": y,
                    "width": width,
                    "depth": depth,
                    "height": local_rng.uniform(0.12, 0.22),
                    "rotation": rotation,
                    "street_angle": angle,
                    "zone": zone,
                    "priority": infill_rng.random(),
                    "seed": local_rng.randrange(1, 2**31 - 1),
                }
            )
        infill.sort(key=lambda item: item["priority"])
        for candidate in infill:
            try_accept(candidate)
            if len(accepted) >= target_count:
                break

    if len(accepted) < target_count:
        raise RuntimeError(
            f"Only generated {len(accepted)}/{target_count} {zone} Roman buildings"
        )
    return accepted


def action_start_frame(obj):
    if "growth_start_frame" in obj:
        return float(obj["growth_start_frame"])
    action = obj.animation_data.action if obj.animation_data else None
    frames = []
    if action:
        for curve in action.fcurves:
            if curve.data_path in {"location", "scale", "hide_render"}:
                frames.extend(point.co.x for point in curve.keyframe_points)
    return min(frames) if frames else 0.0


def road_action_start_frame(obj):
    shape_keys = obj.data.shape_keys
    action = (
        shape_keys.animation_data.action
        if shape_keys and shape_keys.animation_data
        else None
    )
    frames = []
    if action:
        for curve in action.fcurves:
            frames.extend(point.co.x for point in curve.keyframe_points)
    return min(frames) if frames else action_start_frame(obj)


def evenly_partition(items, bucket_count):
    return [
        items[round(index * len(items) / bucket_count) : round((index + 1) * len(items) / bucket_count)]
        for index in range(bucket_count)
    ]


def placement_growth_key(bs, placement):
    if placement["zone"] == "main":
        progress = bs.growth_progress(
            placement["x"], placement["y"], 0, 0.5
        )
    else:
        progress = min(
            0.999,
            math.hypot(placement["x"], placement["y"]) / 13.5,
        )
    angle = math.atan2(placement["y"], placement["x"])
    return (round(progress * 26), angle, placement["x"], placement["y"])


def rebuild_building_group(bs, prefix, placements):
    objects = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith(prefix)),
        key=lambda obj: (action_start_frame(obj), obj.name),
    )
    if not objects:
        raise RuntimeError(f"No target objects for {prefix}")
    placements = sorted(placements, key=lambda item: placement_growth_key(bs, item))
    groups = evenly_partition(placements, len(objects))
    for obj, group in zip(objects, groups):
        materials = [slot.material for slot in obj.material_slots]
        vertices = []
        faces = []
        material_ids = []
        for placement in group:
            rng = random.Random(placement["seed"])
            roof_style = rng.choices(
                ["gable", "hip", "flat"], weights=[0.54, 0.38, 0.08], k=1
            )[0]
            wall_id, roof_id = bs.building_material_ids(rng, "roman")
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
                roof_style,
                "standard",
                "roman",
                rng,
            )
        replace_mesh(obj, vertices, faces, material_ids, materials)
    return len(objects)


def road_piece_geometry(start, end, width, z):
    start = Vector(start)
    end = Vector(end)
    vector = end - start
    length = vector.length
    tangent = vector.normalized()
    normal = Vector((-tangent.y, tangent.x))
    center = (start + end) * 0.5
    half_length = length * 0.525
    half_width = width * 0.5
    return [
        (center - tangent * half_length - normal * half_width).to_3d() + Vector((0, 0, z)),
        (center + tangent * half_length - normal * half_width).to_3d() + Vector((0, 0, z)),
        (center + tangent * half_length + normal * half_width).to_3d() + Vector((0, 0, z)),
        (center - tangent * half_length + normal * half_width).to_3d() + Vector((0, 0, z)),
    ]


def create_road_pieces(bs, streets):
    pieces = []
    for street in streets:
        start = Vector(street["start"])
        end = Vector(street["end"])
        vector = end - start
        length = vector.length
        piece_count = max(1, math.ceil(length / 0.42))
        polygon = None
        if street["zone"] == "cite":
            polygon = bs.load_geodata()["islands"]["ile_de_la_cite"]
        elif street["zone"] == "saint_louis":
            polygon = bs.load_geodata()["islands"]["ile_saint_louis"]
        for index in range(piece_count):
            piece_start = start.lerp(end, index / piece_count)
            piece_end = start.lerp(end, (index + 1) / piece_count)
            midpoint = (piece_start + piece_end) * 0.5
            if street["zone"] == "main":
                if not bs.city_contains(0, midpoint.x, midpoint.y):
                    continue
                if bs.point_on_island(midpoint.x, midpoint.y):
                    continue
                clearance = bs.river_clearance(midpoint.x, midpoint.y)
                minimum_clearance = (
                    BANK_OUTER_WIDTH - 0.07
                    if street["kind"] == "riverfront"
                    else BANK_OUTER_WIDTH + 0.025
                )
                if clearance < minimum_clearance:
                    continue
                z = -0.026
            else:
                if not bs.point_in_polygon(midpoint.x, midpoint.y, polygon):
                    continue
                z = 0.061
            pieces.append(
                {
                    "start": tuple(piece_start),
                    "end": tuple(piece_end),
                    "width": street["width"],
                    "z": z,
                    "progress": bs.road_growth_progress(
                        midpoint.x, midpoint.y, 0, 0.5
                    ),
                    "angle": math.atan2(midpoint.y, midpoint.x),
                }
            )
    return sorted(
        pieces,
        key=lambda item: (round(item["progress"] * 32), item["angle"]),
    )


def rebuild_roman_roads(bs, streets):
    objects = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith("Roads_0_Chunk_")),
        key=lambda obj: (road_action_start_frame(obj), obj.name),
    )
    pieces = create_road_pieces(bs, streets)
    groups = evenly_partition(pieces, len(objects))
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
                for vertex in road_piece_geometry(
                    piece["start"], piece["end"], piece["width"], piece["z"]
                )
            )
            faces.append((start, start + 1, start + 2, start + 3))
        mesh = bpy.data.meshes.new(f"{old_mesh_name}_v15")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        for material in old_materials:
            mesh.materials.append(material)
        obj.data = mesh
        basis = obj.shape_key_add(name="Basis")
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


def terrain_height(bs, x, y):
    clearance = bs.river_clearance(x, y)
    relief = 0.0045 * math.sin(x * 0.17) * math.cos(y * 0.13)
    relief += 0.0025 * math.sin((x + y) * 0.09)
    if clearance <= -0.38:
        return RIVERBED_Z + relief * 0.7
    if clearance < 0.0:
        amount = smoothstep((clearance + 0.38) / 0.38)
        return (RIVERBED_Z * (1.0 - amount)) + ((WATER_Z - 0.018) * amount)
    if clearance < BANK_OUTER_WIDTH:
        amount = smoothstep(clearance / BANK_OUTER_WIDTH)
        return (WATER_Z - 0.018) * (1.0 - amount) + (LAND_Z + relief) * amount
    return LAND_Z + relief


def rebuild_terrain(bs):
    land = bpy.data.objects["Land"]
    land_material = land.material_slots[0].material
    riverbed_material = ensure_material("Riverbed_Silt", (0.19, 0.22, 0.16), 0.93)
    step = 0.75
    minimum = -90.0
    maximum = 90.0
    count = round((maximum - minimum) / step) + 1
    vertices = []
    for y_index in range(count):
        y = minimum + y_index * step
        for x_index in range(count):
            x = minimum + x_index * step
            vertices.append((x, y, terrain_height(bs, x, y)))
    faces = []
    material_ids = []
    for y_index in range(count - 1):
        for x_index in range(count - 1):
            start = y_index * count + x_index
            faces.append((start, start + 1, start + count + 1, start + count))
            center_x = minimum + (x_index + 0.5) * step
            center_y = minimum + (y_index + 0.5) * step
            material_ids.append(
                1 if bs.river_clearance(center_x, center_y) < -0.22 else 0
            )
    land.location = (0.0, 0.0, 0.0)
    replace_mesh(
        land,
        vertices,
        faces,
        material_ids,
        [land_material, riverbed_material],
    )

    points = [
        (x, bs.river_center(x))
        for x in [(-92.0 + index * 0.5) for index in range(369)]
    ]

    seine = bpy.data.objects["Seine"]
    water_materials = [slot.material for slot in seine.material_slots]
    water_vertices = []
    for index, (x, y) in enumerate(points):
        previous = points[max(0, index - 1)]
        following = points[min(len(points) - 1, index + 1)]
        slope = (following[1] - previous[1]) / max(
            0.001, following[0] - previous[0]
        )
        normal = Vector((-slope, 1.0)).normalized()
        half_width = bs.river_half_width(x)
        water_vertices.append(
            (x + normal.x * half_width, y + normal.y * half_width, WATER_Z)
        )
        water_vertices.append(
            (x - normal.x * half_width, y - normal.y * half_width, WATER_Z)
        )
    water_faces = [
        (index * 2, index * 2 + 2, index * 2 + 3, index * 2 + 1)
        for index in range(len(points) - 1)
    ]
    replace_mesh(
        seine,
        water_vertices,
        water_faces,
        [0] * len(water_faces),
        water_materials,
    )

    silt_material = bpy.data.materials.get("Riverbank_Silt") or ensure_material(
        "Riverbank_Silt", (0.43, 0.36, 0.2), 0.9
    )
    sand_material = ensure_material("Riverbank_Sand", (0.7, 0.62, 0.4), 0.86)
    vertices = []
    for index, (x, y) in enumerate(points):
        previous = points[max(0, index - 1)]
        following = points[min(len(points) - 1, index + 1)]
        slope = (following[1] - previous[1]) / max(0.001, following[0] - previous[0])
        normal = Vector((-slope, 1.0)).normalized()
        half_width = bs.river_half_width(x)
        for side in (1.0, -1.0):
            for distance, z in (
                (half_width - 0.035, WATER_Z - 0.025),
                (half_width + 0.19, WATER_Z - 0.002),
                (half_width + BANK_OUTER_WIDTH, terrain_height(bs, x, y + side * (half_width + BANK_OUTER_WIDTH))),
            ):
                vertices.append((x + normal.x * side * distance, y + normal.y * side * distance, z))
    faces = []
    material_ids = []
    stride = 6
    for index in range(len(points) - 1):
        start = index * stride
        following = (index + 1) * stride
        for side_offset in (0, 3):
            faces.append((start + side_offset, following + side_offset, following + side_offset + 1, start + side_offset + 1))
            material_ids.append(0)
            faces.append((start + side_offset + 1, following + side_offset + 1, following + side_offset + 2, start + side_offset + 2))
            material_ids.append(1)
    riverbank = bpy.data.objects["Seine_Riverbank"]
    replace_mesh(
        riverbank,
        vertices,
        faces,
        material_ids,
        [silt_material, sand_material],
    )

    islands = bs.load_geodata()["islands"]
    for key, object_name in (
        ("ile_de_la_cite", "Ile_de_la_Cite_Margin"),
        ("ile_saint_louis", "Ile_Saint_Louis_Margin"),
    ):
        polygon = islands[key]
        center = Vector(
            (
                sum(point[0] for point in polygon) / len(polygon),
                sum(point[1] for point in polygon) / len(polygon),
            )
        )
        rings = []
        for expansion, z in ((1.0, 0.055), (1.08, -0.005), (1.19, WATER_Z - 0.01)):
            rings.append(
                [
                    tuple(center + (Vector(point) - center) * expansion) + (z,)
                    for point in polygon
                ]
            )
        vertices = [vertex for ring in rings for vertex in ring]
        faces = []
        material_ids = []
        ring_count = len(polygon)
        for ring_index in range(2):
            first = ring_index * ring_count
            second = (ring_index + 1) * ring_count
            for index in range(ring_count):
                following = (index + 1) % ring_count
                faces.append((first + index, first + following, second + following, second + index))
                material_ids.append(1 if ring_index == 0 else 0)
        replace_mesh(
            bpy.data.objects[object_name],
            vertices,
            faces,
            material_ids,
            [silt_material, sand_material],
        )

    probe = bpy.data.objects.get("Seine_Planar_Reflection_Probe")
    if probe:
        probe.location.z = WATER_Z + 0.025

    return {
        "land_vertices": len(bpy.data.objects["Land"].data.vertices),
        "land_faces": len(bpy.data.objects["Land"].data.polygons),
        "water_z": WATER_Z,
        "riverbed_z": RIVERBED_Z,
        "land_z": LAND_Z,
        "bank_outer_width": BANK_OUTER_WIDTH,
    }


def alignment_error(placement):
    delta = abs((placement["rotation"] - placement["street_angle"]) % math.pi)
    return min(delta, math.pi - delta)


def main():
    args = parse_args()
    bs = load_build_scene_module()
    streets = clean_roman_streets(bs)
    main_placements = generate_placements(
        bs, streets, "main", MAIN_BUILDING_COUNT, 15101
    )
    cite_placements = generate_placements(
        bs, streets, "cite", CITE_BUILDING_COUNT, 15102
    )
    saint_placements = generate_placements(
        bs, streets, "saint_louis", SAINT_LOUIS_BUILDING_COUNT, 15103
    )

    road_object_count, road_piece_count = rebuild_roman_roads(bs, streets)
    building_object_counts = {
        "main": rebuild_building_group(
            bs, "Buildings_Roman_State_Chunk_", main_placements
        ),
        "cite": rebuild_building_group(
            bs, "Island_Cite_0_State_Chunk_", cite_placements
        ),
        "saint_louis": rebuild_building_group(
            bs, "Island_Saint_Louis_0_State_Chunk_", saint_placements
        ),
    }
    terrain_report = rebuild_terrain(bs)

    all_placements = main_placements + cite_placements + saint_placements
    alignment_errors = [alignment_error(placement) for placement in all_placements]
    river_clearances = [
        bs.river_clearance(placement["x"], placement["y"])
        for placement in main_placements
    ]
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
        },
        "terrain": terrain_report,
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
