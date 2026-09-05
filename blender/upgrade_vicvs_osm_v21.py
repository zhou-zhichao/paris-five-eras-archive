import argparse
import importlib.util
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


BRIDGE_SPECS = (
    {"osm_id": 1188170507, "era": "roman", "start_frame": 165},
    {"osm_id": 744835294, "era": "roman", "start_frame": 210},
    {"osm_id": 474063681, "era": "medieval", "start_frame": 870},
    {"osm_id": 20444537, "era": "medieval", "start_frame": 920},
)

ROMAN_PROTOTYPE_COUNT = 10
MEDIEVAL_PROTOTYPE_COUNT = 6
ROMAN_DOMUS_VARIANTS = (1, 5, 7)
ROMAN_INSULA_VARIANTS = (0, 2, 3, 4, 6, 8, 9)
ROAD_WIDTHS = {
    "primary": 0.145,
    "secondary": 0.115,
    "tertiary": 0.092,
    "residential": 0.074,
    "unclassified": 0.07,
}
ROAD_RANK = {
    "primary": 0,
    "secondary": 1,
    "tertiary": 2,
    "residential": 3,
    "unclassified": 4,
}

WATER_Z = -0.13
LAND_Z = -0.035
RIVERBED_Z = -0.275
RIVERBANK_WIDTH = 0.26
RIVER_BANK_CURVES = None
RIVER_BANK_SOURCE_IDS = None
MEDIEVAL_BLOCKS_FILENAME = "medieval_blocks_v31.json"
MEDIEVAL_BLOCKS_CACHE = None


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--roman-kit", type=Path)
    parser.add_argument("--medieval-kit", type=Path)
    parser.add_argument("--output-blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--terrain-only", action="store_true")
    return parser.parse_args(argv)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_modules():
    directory = Path(__file__).resolve().parent
    build_scene = load_module(directory / "build_scene.py", "paris_build_scene_v21")
    roman = load_module(
        directory / "rebuild_roman_urbanism_v15.py",
        "paris_roman_urbanism_v21",
    )
    medieval = load_module(
        directory / "rebuild_medieval_urbanism_v17.py",
        "paris_medieval_urbanism_v21",
    )
    upgrade = load_module(
        directory / "upgrade_roads_houses_v19.py",
        "paris_upgrade_roads_houses_v21",
    )
    return build_scene, roman, medieval, upgrade


def stable_fraction(value):
    return ((int(value) * 2654435761) % 1000003) / 1000003.0


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def normalize_bank_controls(controls):
    buckets = defaultdict(list)
    for x, y, osm_id in controls:
        buckets[round(x, 3)].append((x, y, osm_id))
    result = []
    for _key, values in sorted(buckets.items()):
        preferred = next(
            (item for item in values if item[2] in {1188170507, 744835294, 474063681, 20444537}),
            None,
        )
        if preferred:
            result.append(preferred)
        else:
            result.append(
                (
                    sum(item[0] for item in values) / len(values),
                    sum(item[1] for item in values) / len(values),
                    values[0][2],
                )
            )
    return result


def build_osm_bank_curves(build_scene):
    controls = {"upper": [], "lower": []}
    source_ids = set()
    for road in build_scene.load_geodata()["roads"]:
        if not road["bridge"] or len(road["points"]) < 2:
            continue
        endpoints = (road["points"][0], road["points"][-1])
        island_flags = [build_scene.point_on_island(*point) for point in endpoints]
        if island_flags[0] == island_flags[1]:
            continue
        bank = endpoints[1] if island_flags[0] else endpoints[0]
        x, y = bank
        if not -14.0 <= x <= 14.0:
            continue
        side = "upper" if y >= build_scene.river_center(x) else "lower"
        controls[side].append((float(x), float(y), int(road["id"])))
        source_ids.add(int(road["id"]))
    for x in (-92.0, -16.0, 16.0, 92.0):
        center = build_scene.river_center(x)
        controls["upper"].append((x, center + 0.82, -1))
        controls["lower"].append((x, center - 0.82, -1))
    return {
        side: normalize_bank_controls(values)
        for side, values in controls.items()
    }, source_ids


def interpolate_bank(controls, x):
    if x <= controls[0][0]:
        return controls[0][1]
    if x >= controls[-1][0]:
        return controls[-1][1]
    for start, end in zip(controls, controls[1:]):
        if start[0] <= x <= end[0]:
            span = end[0] - start[0]
            if abs(span) < 1e-9:
                return (start[1] + end[1]) * 0.5
            amount = (x - start[0]) / span
            return start[1] * (1.0 - amount) + end[1] * amount
    return controls[-1][1]


def river_banks_at_x(build_scene, x):
    if RIVER_BANK_CURVES is None:
        center = build_scene.river_center(x)
        return center + 0.82, center - 0.82
    return (
        interpolate_bank(RIVER_BANK_CURVES["upper"], x),
        interpolate_bank(RIVER_BANK_CURVES["lower"], x),
    )


def asymmetric_river_widths(build_scene, x):
    center = build_scene.river_center(x)
    upper_bank, lower_bank = river_banks_at_x(build_scene, x)
    return max(0.25, upper_bank - center), max(0.25, center - lower_bank)


def install_asymmetric_river(build_scene):
    global RIVER_BANK_CURVES, RIVER_BANK_SOURCE_IDS
    RIVER_BANK_CURVES, RIVER_BANK_SOURCE_IDS = build_osm_bank_curves(build_scene)

    def river_clearance(x, y):
        upper_bank, lower_bank = river_banks_at_x(build_scene, x)
        if y > upper_bank:
            return y - upper_bank
        if y < lower_bank:
            return lower_bank - y
        return -min(upper_bank - y, y - lower_bank)

    def is_water(x, y, margin=0.0):
        if build_scene.point_on_island(x, y):
            return False
        return river_clearance(x, y) < margin

    build_scene.river_clearance = river_clearance
    build_scene.is_water = is_water
    build_scene.river_half_width = lambda x: max(asymmetric_river_widths(build_scene, x))


def terrain_height(build_scene, x, y):
    clearance = build_scene.river_clearance(x, y)
    relief = 0.0045 * math.sin(x * 0.17) * math.cos(y * 0.13)
    relief += 0.0025 * math.sin((x + y) * 0.09)
    if clearance <= -0.34:
        return RIVERBED_Z + relief * 0.7
    if clearance < 0.0:
        amount = smoothstep((clearance + 0.34) / 0.34)
        return RIVERBED_Z * (1.0 - amount) + (WATER_Z - 0.018) * amount
    if clearance < RIVERBANK_WIDTH:
        amount = smoothstep(clearance / RIVERBANK_WIDTH)
        return (WATER_Z - 0.018) * (1.0 - amount) + (LAND_Z + relief) * amount
    return LAND_Z + relief


def rebuild_asymmetric_terrain(build_scene, roman):
    land = bpy.data.objects["Land"]
    land_material = land.material_slots[0].material
    riverbed_material = roman.ensure_material("Riverbed_Silt", (0.19, 0.22, 0.16), 0.93)
    silt_material = bpy.data.materials.get("Riverbank_Silt") or roman.ensure_material(
        "Riverbank_Silt", (0.43, 0.36, 0.2), 0.9
    )
    sand_material = bpy.data.materials.get("Riverbank_Sand") or roman.ensure_material(
        "Riverbank_Sand", (0.7, 0.62, 0.4), 0.86
    )
    step = 0.25
    minimum = -90.0
    maximum = 90.0
    count = round((maximum - minimum) / step) + 1
    vertices = [
        (minimum + x_index * step, minimum + y_index * step, terrain_height(
            build_scene,
            minimum + x_index * step,
            minimum + y_index * step,
        ))
        for y_index in range(count)
        for x_index in range(count)
    ]
    faces = []
    material_ids = []
    for y_index in range(count - 1):
        for x_index in range(count - 1):
            start = y_index * count + x_index
            center_clearance = build_scene.river_clearance(
                minimum + (x_index + 0.5) * step,
                minimum + (y_index + 0.5) * step,
            )
            if -0.75 < center_clearance < 0.9:
                continue
            faces.append((start, start + 1, start + count + 1, start + count))
            if center_clearance < -0.08:
                material_ids.append(1)
            elif center_clearance < 0.07:
                material_ids.append(2)
            elif center_clearance < RIVERBANK_WIDTH:
                material_ids.append(3)
            else:
                material_ids.append(0)
    roman.replace_mesh(
        land,
        vertices,
        faces,
        material_ids,
        [land_material, riverbed_material, silt_material, sand_material],
    )
    land.location = (0.0, 0.0, 0.0)

    x_values = {-92.0 + index * 0.25 for index in range(737)}
    for controls in RIVER_BANK_CURVES.values():
        x_values.update(item[0] for item in controls)
    points = [
        (x, build_scene.river_center(x))
        for x in sorted(x_values)
    ]
    water_vertices = []
    bank_vertices = []
    bank_offsets = (-1.0, -0.34, -0.08, 0.0, 0.12, 0.32, 1.4)
    for index, (x, y) in enumerate(points):
        upper_bank, lower_bank = river_banks_at_x(build_scene, x)
        water_vertices.extend(
            (
                (x, upper_bank, WATER_Z),
                (x, lower_bank, WATER_Z),
            )
        )
        for side, bank_y in ((1.0, upper_bank), (-1.0, lower_bank)):
            for offset in bank_offsets:
                sample_y = bank_y + side * offset
                bank_vertices.append(
                    (
                        x,
                        sample_y,
                        terrain_height(build_scene, x, sample_y) + 0.004,
                    )
                )
    water_faces = [
        (index * 2, index * 2 + 2, index * 2 + 3, index * 2 + 1)
        for index in range(len(points) - 1)
    ]
    seine = bpy.data.objects["Seine"]
    water_materials = [slot.material for slot in seine.material_slots]
    roman.replace_mesh(seine, water_vertices, water_faces, [0] * len(water_faces), water_materials)

    bank_faces = []
    bank_material_ids = []
    side_stride = len(bank_offsets)
    stride = side_stride * 2
    band_materials = (0, 0, 0, 0, 1, 2)
    for index in range(len(points) - 1):
        start = index * stride
        following = (index + 1) * stride
        for side_offset in (0, side_stride):
            for band_index, material_id in enumerate(band_materials):
                bank_faces.append(
                    (
                        start + side_offset + band_index,
                        following + side_offset + band_index,
                        following + side_offset + band_index + 1,
                        start + side_offset + band_index + 1,
                    )
                )
                bank_material_ids.append(material_id)
    riverbank = bpy.data.objects["Seine_Riverbank"]
    roman.replace_mesh(
        riverbank,
        bank_vertices,
        bank_faces,
        bank_material_ids,
        [silt_material, sand_material, land_material],
    )
    riverbank.hide_render = False
    riverbank.hide_viewport = False
    probe = bpy.data.objects.get("Seine_Planar_Reflection_Probe")
    if probe:
        probe.location.z = WATER_Z + 0.025
    return {
        "mode": "Shoreline-conforming bank mesh over a clipped continuous terrain grid",
        "land_vertices": len(vertices),
        "land_faces": len(faces),
        "water_vertices": len(water_vertices),
        "bank_width": RIVERBANK_WIDTH,
        "control_bridge_ids": sorted(RIVER_BANK_SOURCE_IDS),
        "upper_control_count": len(RIVER_BANK_CURVES["upper"]),
        "lower_control_count": len(RIVER_BANK_CURVES["lower"]),
    }


def point_segment_projection(point, start, end):
    point = Vector(point)
    start = Vector(start)
    end = Vector(end)
    delta = end - start
    if delta.length_squared < 1e-10:
        return start.copy(), 0.0
    amount = max(0.0, min(1.0, (point - start).dot(delta) / delta.length_squared))
    return start + delta * amount, amount


def classify_zone(build_scene, midpoint, era_index):
    geodata = build_scene.load_geodata()
    x, y = midpoint
    if build_scene.point_in_polygon(x, y, geodata["islands"]["ile_de_la_cite"]):
        return "cite"
    if build_scene.point_in_polygon(x, y, geodata["islands"]["ile_saint_louis"]):
        return "saint_louis"
    if build_scene.city_contains(era_index, x, y) and not build_scene.point_on_island(x, y):
        return "main"
    return None


def include_roman_road(road, zone):
    if road["class"] in {"primary", "secondary", "tertiary"}:
        return True
    threshold = 1.0 if zone != "main" else 0.78
    return stable_fraction(road["id"]) < threshold


def quantized_segment_key(start, end, quantum=0.018):
    points = (
        (round(start[0] / quantum), round(start[1] / quantum)),
        (round(end[0] / quantum), round(end[1] / quantum)),
    )
    return tuple(sorted(points))


def build_osm_streets(build_scene, era):
    era_index = 0 if era == "roman" else 1
    candidates = {}
    source_way_ids = set()
    for road in build_scene.load_geodata()["roads"]:
        if road["bridge"]:
            continue
        road_class = road["class"]
        if road_class not in ROAD_WIDTHS:
            continue
        for segment_index, (start, end) in enumerate(zip(road["points"], road["points"][1:])):
            start = Vector(start)
            end = Vector(end)
            if (end - start).length < 0.035:
                continue
            midpoint = (start + end) * 0.5
            zone = classify_zone(build_scene, midpoint, era_index)
            if zone is None:
                continue
            if era == "roman" and not include_roman_road(road, zone):
                continue
            street = {
                "start": tuple(start),
                "end": tuple(end),
                "width": ROAD_WIDTHS[road_class],
                "zone": zone,
                "frontage": True,
                "sides": (-1, 1),
                "kind": "osm",
                "osm_id": int(road["id"]),
                "osm_segment": segment_index,
                "road_class": road_class,
                "source_phase": int(road["phase"]),
            }
            key = quantized_segment_key(start, end)
            previous = candidates.get(key)
            if previous is None or ROAD_RANK[road_class] < ROAD_RANK[previous["road_class"]]:
                candidates[key] = street
                source_way_ids.add(int(road["id"]))
    streets = sorted(
        candidates.values(),
        key=lambda item: (
            item["zone"],
            ROAD_RANK[item["road_class"]],
            item["osm_id"],
            item["osm_segment"],
        ),
    )
    return streets, source_way_ids


def road_tangent(street):
    delta = Vector(street["end"]) - Vector(street["start"])
    return delta.normalized()


def nearest_street(streets, zone, point):
    point = Vector(point)
    best = None
    for street in streets:
        if street["zone"] != zone or street["kind"] != "osm":
            continue
        nearest, amount = point_segment_projection(point, street["start"], street["end"])
        distance = (nearest - point).length
        rank = ROAD_RANK[street["road_class"]]
        score = distance + rank * 0.0001
        if best is None or score < best[0]:
            best = (score, distance, nearest, street, amount)
    if best is None:
        raise RuntimeError(f"No OSM street for {zone} near {tuple(point)}")
    return best[1:]


def cubic_bridgehead_points(start, end, start_tangent, end_tangent, samples=7):
    start = Vector(start)
    end = Vector(end)
    distance = (end - start).length
    if distance < 0.025:
        return [tuple(start), tuple(end)]
    handle = min(distance * 0.42, 0.34)
    p1 = start + Vector(start_tangent).normalized() * handle
    p2 = end - Vector(end_tangent).normalized() * handle
    points = []
    for index in range(samples):
        amount = index / (samples - 1)
        inverse = 1.0 - amount
        point = (
            start * (inverse**3)
            + p1 * (3.0 * inverse * inverse * amount)
            + p2 * (3.0 * inverse * amount * amount)
            + end * (amount**3)
        )
        points.append(tuple(point))
    return points


def load_bridge_definitions(build_scene, medieval_streets):
    roads_by_id = {int(road["id"]): road for road in build_scene.load_geodata()["roads"]}
    cite_polygon = build_scene.load_geodata()["islands"]["ile_de_la_cite"]
    definitions = []
    connector_streets = []
    for specification in BRIDGE_SPECS:
        road = roads_by_id.get(specification["osm_id"])
        if road is None or not road["bridge"]:
            raise RuntimeError(f"Missing OSM bridge way {specification['osm_id']}")
        points = [Vector(point) for point in road["points"]]
        endpoint_data = []
        for endpoint_index in (0, -1):
            endpoint = points[endpoint_index]
            on_island = build_scene.point_in_polygon(endpoint.x, endpoint.y, cite_polygon)
            zone = "cite" if on_island else "main"
            distance, target, street, amount = nearest_street(medieval_streets, zone, endpoint)
            bridge_out_tangent = (
                (points[0] - points[1]).normalized()
                if endpoint_index == 0
                else (points[-1] - points[-2]).normalized()
            )
            target_tangent = road_tangent(street)
            travel = target - endpoint
            if target_tangent.dot(travel) < 0.0:
                target_tangent.negate()
            curve_points = cubic_bridgehead_points(
                endpoint,
                target,
                bridge_out_tangent,
                target_tangent,
            )
            connector_name = (
                f"OSM_Bridgehead_{specification['osm_id']}_{'Island' if on_island else 'Mainland'}"
            )
            endpoint_data.append(
                {
                    "name": connector_name,
                    "zone": zone,
                    "bridge_endpoint": tuple(endpoint),
                    "road_target": tuple(target),
                    "road_osm_id": street["osm_id"],
                    "source_gap": distance,
                    "points": curve_points,
                    "road_width": street["width"],
                }
            )
            for segment_index, (start, end) in enumerate(zip(curve_points, curve_points[1:])):
                connector_streets.append(
                    {
                        "start": start,
                        "end": end,
                        "width": max(0.10, street["width"]),
                        "zone": zone,
                        "frontage": False,
                        "sides": (-1, 1),
                        "kind": "osm_bridgehead_transition",
                        "osm_id": int(specification["osm_id"]),
                        "osm_segment": segment_index,
                        "road_class": road["class"],
                        "source_phase": int(road["phase"]),
                    }
                )
        definitions.append(
            {
                **specification,
                "road_class": road["class"],
                "points": [tuple(point) for point in points],
                "endpoints": endpoint_data,
            }
        )
    return definitions, connector_streets


class SpatialFootprints:
    def __init__(self, build_scene, cell_size=0.55):
        self.build_scene = build_scene
        self.cell_size = cell_size
        self.items = []
        self.grid = defaultdict(list)

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

    def can_add(self, footprint, gap=0.006):
        nearby = set()
        for cell in self.cells(footprint):
            nearby.update(self.grid.get(cell, ()))
        return not any(
            self.build_scene.footprints_overlap(footprint, self.items[index], gap=gap)
            for index in nearby
        )

    def add(self, footprint):
        index = len(self.items)
        self.items.append(footprint)
        for cell in self.cells(footprint):
            self.grid[cell].append(index)


class SpatialRoads:
    def __init__(self, streets, cell_size=0.7):
        self.cell_size = cell_size
        self.streets = streets
        self.grid = defaultdict(list)
        for index, street in enumerate(streets):
            start = Vector(street["start"])
            end = Vector(street["end"])
            margin = 0.55
            min_x = min(start.x, end.x) - margin
            max_x = max(start.x, end.x) + margin
            min_y = min(start.y, end.y) - margin
            max_y = max(start.y, end.y) + margin
            for cell_x in range(math.floor(min_x / cell_size), math.floor(max_x / cell_size) + 1):
                for cell_y in range(math.floor(min_y / cell_size), math.floor(max_y / cell_size) + 1):
                    self.grid[(cell_x, cell_y)].append(index)

    def nearby(self, x, y):
        return (
            self.streets[index]
            for index in self.grid.get(
                (math.floor(x / self.cell_size), math.floor(y / self.cell_size)),
                (),
            )
        )


class MedievalBlockIndex:
    def __init__(self, blocks, cell_size=2.0):
        self.blocks = blocks
        self.cell_size = cell_size
        self.grid = defaultdict(list)
        for block_index, block in enumerate(blocks):
            min_x, min_y, max_x, max_y = block["bbox"]
            for cell_x in range(
                math.floor(min_x / cell_size),
                math.floor(max_x / cell_size) + 1,
            ):
                for cell_y in range(
                    math.floor(min_y / cell_size),
                    math.floor(max_y / cell_size) + 1,
                ):
                    self.grid[(cell_x, cell_y)].append(block_index)

    def locate(self, build_scene, x, y):
        cell = (
            math.floor(x / self.cell_size),
            math.floor(y / self.cell_size),
        )
        for block_index in self.grid.get(cell, ()):
            block = self.blocks[block_index]
            min_x, min_y, max_x, max_y = block["bbox"]
            if not min_x <= x <= max_x or not min_y <= y <= max_y:
                continue
            if build_scene.point_in_polygon(x, y, block["polygon"]):
                return block
        return None


def load_medieval_blocks(build_scene):
    global MEDIEVAL_BLOCKS_CACHE
    if MEDIEVAL_BLOCKS_CACHE is None:
        path = build_scene.PROJECT_DIR / "data" / MEDIEVAL_BLOCKS_FILENAME
        MEDIEVAL_BLOCKS_CACHE = json.loads(path.read_text(encoding="utf-8"))
    return MEDIEVAL_BLOCKS_CACHE


def rotated_point_extent(half_width, half_depth, rotation, normal_angle):
    return abs(math.cos(normal_angle - rotation)) * half_width + abs(
        math.sin(normal_angle - rotation)
    ) * half_depth


def clear_of_roads(placement, road_index, extra=0.012):
    center = Vector((placement["x"], placement["y"]))
    half_width = placement["width"] * 0.5
    half_depth = placement["depth"] * 0.5
    for street in road_index.nearby(center.x, center.y):
        nearest, _ = point_segment_projection(center, street["start"], street["end"])
        tangent_angle = math.atan2(
            street["end"][1] - street["start"][1],
            street["end"][0] - street["start"][0],
        )
        extent = rotated_point_extent(
            half_width,
            half_depth,
            placement["rotation"],
            tangent_angle + math.pi * 0.5,
        )
        if (nearest - center).length < street["width"] * 0.5 + extent + extra:
            return False
    return True


def reserved_footprints(era, zone):
    if era == "roman" and zone == "main":
        return (
            (6.4, 6.25, 1.62, 1.15, 0.0),
            (1.4, -8.5, 1.52, 1.09, 0.0),
        )
    if era == "medieval" and zone == "cite":
        return ((0.15, 0.25, 1.22, 0.745, -0.55),)
    return ()


def placement_style(rng, era, zone, band_index):
    if era == "roman":
        domus = band_index == 0 and rng.random() < 0.055
        if domus:
            width = rng.uniform(0.27, 0.35)
            depth = rng.uniform(0.24, 0.32)
            height = rng.uniform(0.17, 0.24)
            variant = rng.choice(ROMAN_DOMUS_VARIANTS)
        else:
            width = rng.uniform(0.155, 0.235)
            depth = rng.uniform(0.145, 0.215)
            height = rng.uniform(0.27, 0.48)
            variant = rng.choice(ROMAN_INSULA_VARIANTS)
        return width, depth, height, variant
    width = rng.uniform(0.145, 0.235)
    depth = rng.uniform(0.14, 0.225)
    height = rng.uniform(0.27, 0.55)
    if rng.random() < 0.07:
        height = rng.uniform(0.52, 0.66)
    return width, depth, height, rng.randrange(MEDIEVAL_PROTOTYPE_COUNT)


def medieval_infill_placement(candidate, block_id):
    seed = int(candidate["seed"])
    rng = random.Random(seed)
    variant = rng.randrange(MEDIEVAL_PROTOTYPE_COUNT)
    encoded_seed = seed - seed % MEDIEVAL_PROTOTYPE_COUNT + variant
    height = rng.uniform(0.25, 0.48)
    if candidate.get("role") == "workshop_row":
        height *= rng.uniform(0.78, 0.92)
    elif rng.random() < 0.055:
        height = rng.uniform(0.48, 0.61)
    return {
        "x": float(candidate["x"]),
        "y": float(candidate["y"]),
        "width": float(candidate["width"]),
        "depth": float(candidate["depth"]),
        "height": height,
        "rotation": float(candidate["rotation"]),
        "street_angle": float(candidate["rotation"]),
        "street_width": 0.06,
        "street_index": -1,
        "zone": "main",
        "band": 1.0 + float(candidate["priority"]),
        "band_index": 10,
        "priority": float(candidate["priority"]),
        "seed": max(1, encoded_seed),
        "prototype_variant": variant,
        "source_osm_id": -(block_id + 1),
        "block_id": block_id,
        "plan_style": "standard",
        "roof_style": rng.choices(
            ["gable", "hip", "pyramid", "mansard"],
            weights=[0.68, 0.24, 0.06, 0.02],
            k=1,
        )[0],
        "timber": rng.random() < 0.31,
        "chimney": rng.random() < 0.39,
        "infill_role": candidate.get("role", "rear_row"),
        "infill_pass": int(candidate.get("pass_index", 0)),
    }


def dominant_polygon_angle(points):
    longest_start, longest_end = max(
        zip(points, points[1:] + points[:1]),
        key=lambda pair: math.dist(pair[0], pair[1]),
    )
    angle = math.atan2(
        longest_end[1] - longest_start[1],
        longest_end[0] - longest_start[0],
    )
    while angle > math.pi * 0.5:
        angle -= math.pi
    while angle <= -math.pi * 0.5:
        angle += math.pi
    return angle


def medieval_courtyard_fill_candidates(build_scene, block):
    candidates = []
    for courtyard_index, courtyard in enumerate(block["courtyards"]):
        if len(courtyard) < 3:
            continue
        angle = dominant_polygon_angle(courtyard)
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        center_x = sum(point[0] for point in courtyard) / len(courtyard)
        center_y = sum(point[1] for point in courtyard) / len(courtyard)

        def to_local(point):
            delta_x = point[0] - center_x
            delta_y = point[1] - center_y
            return (
                delta_x * cos_angle + delta_y * sin_angle,
                -delta_x * sin_angle + delta_y * cos_angle,
            )

        local_points = [to_local(point) for point in courtyard]
        minimum_x = min(point[0] for point in local_points)
        maximum_x = max(point[0] for point in local_points)
        minimum_y = min(point[1] for point in local_points)
        maximum_y = max(point[1] for point in local_points)
        pitch_x = 0.152
        pitch_y = 0.158
        row = 0
        local_y = minimum_y + pitch_y * 0.52
        while local_y <= maximum_y - pitch_y * 0.42:
            local_x = minimum_x + pitch_x * (0.52 + (0.5 if row % 2 else 0.0))
            column = 0
            while local_x <= maximum_x - pitch_x * 0.42:
                seed = (
                    (block["id"] + 1) * 2000003
                    + (courtyard_index + 1) * 200003
                    + row * 1009
                    + column * 9176
                )
                rng = random.Random(seed)
                width = rng.uniform(0.108, 0.136)
                depth = rng.uniform(0.102, 0.131)
                jitter_x = rng.uniform(-0.005, 0.005)
                jitter_y = rng.uniform(-0.005, 0.005)
                sample_x = local_x + jitter_x
                sample_y = local_y + jitter_y
                world_x = (
                    center_x + sample_x * cos_angle - sample_y * sin_angle
                )
                world_y = (
                    center_y + sample_x * sin_angle + sample_y * cos_angle
                )
                rotation = angle + rng.uniform(-0.01, 0.01)
                half_width = width * 0.5 + 0.004
                half_depth = depth * 0.5 + 0.004
                cos_rotation = math.cos(rotation)
                sin_rotation = math.sin(rotation)
                corners = []
                for corner_x, corner_y in (
                    (-half_width, -half_depth),
                    (-half_width, half_depth),
                    (half_width, -half_depth),
                    (half_width, half_depth),
                ):
                    corners.append(
                        (
                            world_x
                            + corner_x * cos_rotation
                            - corner_y * sin_rotation,
                            world_y
                            + corner_x * sin_rotation
                            + corner_y * cos_rotation,
                        )
                    )
                if all(
                    build_scene.point_in_polygon(x, y, courtyard)
                    for x, y in corners
                ):
                    candidates.append(
                        {
                            "x": world_x,
                            "y": world_y,
                            "width": width,
                            "depth": depth,
                            "rotation": rotation,
                            "seed": seed,
                            "priority": row + column * 0.001 + rng.random() * 0.01,
                            "pass_index": 30 + courtyard_index,
                            "role": "courtyard_fill",
                        }
                    )
                local_x += pitch_x
                column += 1
            local_y += pitch_y
            row += 1
    candidates.sort(key=lambda item: (item["priority"], item["seed"]))
    return candidates


def zone_polygon(build_scene, era, zone):
    if zone == "main":
        return build_scene.CITY_POLYGONS[0 if era == "roman" else 1]
    key = "ile_de_la_cite" if zone == "cite" else "ile_saint_louis"
    return build_scene.load_geodata()["islands"][key]


def zone_contains(build_scene, era, zone, x, y):
    if zone == "main":
        era_index = 0 if era == "roman" else 1
        return build_scene.city_contains(era_index, x, y) and not build_scene.point_on_island(x, y)
    return build_scene.point_in_polygon(x, y, zone_polygon(build_scene, era, zone))


def generate_aligned_placements(
    build_scene,
    streets,
    era,
    zone,
    target_count,
    seed,
    density_extra=3000,
    fill_courtyards=False,
):
    zone_streets = [street for street in streets if street["zone"] == zone]
    road_index = SpatialRoads(zone_streets)
    footprint_index = SpatialFootprints(build_scene)
    for footprint in reserved_footprints(era, zone):
        footprint_index.add(footprint)
    if era == "roman":
        bands = (0.0, 0.20, 0.40, 0.60, 0.80)
    elif zone == "main":
        bands = tuple(round(index * 0.23, 5) for index in range(10))
    else:
        bands = (0.0, 0.23, 0.46, 0.69, 0.92)
    candidates = []
    for street_index, street in enumerate(zone_streets):
        if not street["frontage"]:
            continue
        start = Vector(street["start"])
        end = Vector(street["end"])
        vector = end - start
        length = vector.length
        if length < 0.22:
            continue
        tangent = vector.normalized()
        normal = Vector((-tangent.y, tangent.x))
        angle = math.atan2(tangent.y, tangent.x)
        for side in (-1, 1):
            for band_index, band in enumerate(bands):
                row_rng = random.Random(
                    seed * 1000003
                    + street["osm_id"] * 97
                    + street_index * 1009
                    + side * 17
                    + band_index * 7919
                )
                cursor = 0.045 + row_rng.uniform(0.0, 0.055)
                while cursor < length - 0.045:
                    candidate_seed = row_rng.randrange(1, 2**31 - 1)
                    local_rng = random.Random(candidate_seed)
                    width, depth, height, variant = placement_style(
                        local_rng,
                        era,
                        zone,
                        band_index,
                    )
                    gap = local_rng.uniform(0.008, 0.025)
                    center_distance = cursor + width * 0.5
                    if center_distance + width * 0.5 > length - 0.035:
                        break
                    base = start + tangent * center_distance
                    offset = street["width"] * 0.5 + depth * 0.5 + 0.022 + band
                    center = base + normal * side * offset
                    rotation = angle if side > 0 else angle + math.pi
                    rotation += local_rng.uniform(-0.006, 0.006)
                    modulus = ROMAN_PROTOTYPE_COUNT if era == "roman" else MEDIEVAL_PROTOTYPE_COUNT
                    encoded_seed = candidate_seed - candidate_seed % modulus + variant
                    placement = {
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
                        "band_index": band_index,
                        "priority": (
                            band_index * 1.75
                            + ROAD_RANK[street["road_class"]] * 0.08
                            + math.hypot(center.x, center.y) * 0.012
                            + local_rng.random() * 0.34
                        ),
                        "seed": max(1, encoded_seed),
                        "prototype_variant": variant,
                        "source_osm_id": street["osm_id"],
                    }
                    if era == "medieval":
                        placement.update(
                            {
                                "plan_style": "standard",
                                "roof_style": local_rng.choices(
                                    ["gable", "hip", "pyramid", "mansard"],
                                    weights=[0.62, 0.25, 0.09, 0.04],
                                    k=1,
                                )[0],
                                "timber": local_rng.random() < 0.28,
                                "chimney": local_rng.random() < 0.43,
                                "half_width": width * 0.5,
                                "half_depth": depth * 0.5,
                            }
                        )
                    candidates.append(placement)
                    cursor += width + gap

    candidates.sort(key=lambda item: item["priority"])
    polygon = zone_polygon(build_scene, era, zone)
    accepted = []
    rejection_counts = Counter()

    def try_accept(placement, block=None, protect_courtyard=False):
        x = placement["x"]
        y = placement["y"]
        half_width = placement["width"] * 0.5
        half_depth = placement["depth"] * 0.5
        footprint_radius = math.hypot(half_width, half_depth)
        if not zone_contains(build_scene, era, zone, x, y):
            rejection_counts["outside_zone"] += 1
            return False
        edge_margin = 0.075 if zone == "main" else 0.045
        if build_scene.polygon_edge_distance(x, y, polygon) < footprint_radius + edge_margin:
            rejection_counts["city_edge"] += 1
            return False
        bank_setback = 0.30 if era == "roman" else 0.22
        if zone == "main" and build_scene.river_clearance(x, y) < bank_setback + footprint_radius:
            rejection_counts["river_setback"] += 1
            return False
        if protect_courtyard and block is not None:
            if any(
                build_scene.point_in_polygon(x, y, courtyard)
                for courtyard in block["courtyards"]
            ):
                rejection_counts["courtyard"] += 1
                return False
        if not clear_of_roads(placement, road_index):
            rejection_counts["road_clearance"] += 1
            return False
        footprint = (x, y, half_width, half_depth, placement["rotation"])
        if not footprint_index.can_add(footprint):
            rejection_counts["building_collision"] += 1
            return False
        footprint_index.add(footprint)
        accepted.append(placement)
        return True

    if era != "medieval" or zone != "main":
        base_target = target_count
        if era == "medieval" and fill_courtyards:
            base_target = min(
                target_count,
                155 if zone == "cite" else 108,
            )
        for placement in candidates:
            if try_accept(placement) and len(accepted) >= base_target:
                break
        island_void_fill_accepted = 0
        if (
            era == "medieval"
            and fill_courtyards
            and zone in {"cite", "saint_louis"}
            and len(accepted) < target_count
        ):
            minimum_x = min(point[0] for point in polygon)
            maximum_x = max(point[0] for point in polygon)
            minimum_y = min(point[1] for point in polygon)
            maximum_y = max(point[1] for point in polygon)
            polygon_angle = dominant_polygon_angle(polygon)
            island_candidates = []
            pitch_x = 0.151
            pitch_y = 0.159
            row = 0
            y = minimum_y + pitch_y * 0.55
            while y <= maximum_y - pitch_y * 0.45:
                x = minimum_x + pitch_x * (
                    0.55 + (0.5 if row % 2 else 0.0)
                )
                column = 0
                while x <= maximum_x - pitch_x * 0.45:
                    void_seed = (
                        seed * 1000003
                        + row * 1009
                        + column * 9176
                        + (440044 if zone == "cite" else 550055)
                    ) % (2**31 - 1)
                    if void_seed <= 0:
                        void_seed = 1
                    rng = random.Random(void_seed)
                    sample_x = x + rng.uniform(-0.007, 0.007)
                    sample_y = y + rng.uniform(-0.007, 0.007)
                    nearby_streets = list(
                        road_index.nearby(sample_x, sample_y)
                    )
                    if nearby_streets:
                        point = Vector((sample_x, sample_y))
                        street = min(
                            nearby_streets,
                            key=lambda item: point_segment_projection(
                                point,
                                item["start"],
                                item["end"],
                            )[1],
                        )
                        rotation = math.atan2(
                            street["end"][1] - street["start"][1],
                            street["end"][0] - street["start"][0],
                        )
                        source_osm_id = street["osm_id"]
                    else:
                        rotation = polygon_angle
                        source_osm_id = -1
                    rotation += rng.uniform(-0.014, 0.014)
                    width = rng.uniform(0.112, 0.146)
                    depth = rng.uniform(0.102, 0.137)
                    variant = rng.randrange(MEDIEVAL_PROTOTYPE_COUNT)
                    encoded_seed = (
                        void_seed
                        - void_seed % MEDIEVAL_PROTOTYPE_COUNT
                        + variant
                    )
                    island_candidates.append(
                        {
                            "x": sample_x,
                            "y": sample_y,
                            "width": width,
                            "depth": depth,
                            "height": rng.uniform(0.25, 0.48),
                            "rotation": rotation,
                            "street_angle": rotation,
                            "street_width": 0.06,
                            "street_index": -1,
                            "zone": zone,
                            "band": 99.0,
                            "band_index": 12,
                            "priority": rng.random(),
                            "seed": encoded_seed,
                            "prototype_variant": variant,
                            "source_osm_id": source_osm_id,
                            "plan_style": "standard",
                            "roof_style": rng.choices(
                                ["gable", "hip", "pyramid", "mansard"],
                                weights=[0.68, 0.24, 0.06, 0.02],
                                k=1,
                            )[0],
                            "timber": rng.random() < 0.31,
                            "chimney": rng.random() < 0.39,
                            "infill_role": "island_void_fill",
                            "infill_pass": 41,
                        }
                    )
                    x += pitch_x
                    column += 1
                y += pitch_y
                row += 1
            island_candidates.sort(
                key=lambda item: (item["priority"], item["seed"])
            )
            for placement in island_candidates:
                if len(accepted) >= target_count:
                    break
                if try_accept(placement):
                    island_void_fill_accepted += 1
        return accepted, {
            "target": target_count,
            "accepted": len(accepted),
            "candidate_count": len(candidates),
            "frontage_osm_way_count": len({item["osm_id"] for item in zone_streets}),
            "base_layer_accepted": len(accepted) - island_void_fill_accepted,
            "island_void_fill_accepted": island_void_fill_accepted,
            "rejections": dict(rejection_counts),
        }

    block_data = load_medieval_blocks(build_scene)
    blocks = block_data["blocks"]
    block_index = MedievalBlockIndex(blocks)
    block_lookup = {block["id"]: block for block in blocks}
    block_candidates = defaultdict(list)
    block_accepted = Counter()

    base_layer_accepted = 0
    for placement in candidates:
        block = block_index.locate(build_scene, placement["x"], placement["y"])
        if block is not None:
            placement["block_id"] = block["id"]
        if not try_accept(placement):
            continue
        base_layer_accepted += 1
        if block is not None:
            block_accepted[block["id"]] += 1
        if base_layer_accepted >= target_count:
            break
    base_rejections = rejection_counts.copy()

    for block in blocks:
        block_candidates[block["id"]] = [
            medieval_infill_placement(candidate, block["id"])
            for candidate in block["infill_candidates"]
        ]
    for values in block_candidates.values():
        values.sort(key=lambda item: (item["band_index"], item["priority"]))

    cursors = {block["id"]: 0 for block in blocks}
    active = {
        block["id"]
        for block in blocks
        if block_accepted[block["id"]] < block["target_buildings"]
        and block_candidates.get(block["id"])
    }
    infill_accepted = 0
    while active:
        made_progress = False
        completed = []
        for block_id in sorted(active):
            block = block_lookup[block_id]
            values = block_candidates[block_id]
            cursor = cursors[block_id]
            placed = False
            while cursor < len(values):
                placement = values[cursor]
                cursor += 1
                if try_accept(placement, block=block, protect_courtyard=True):
                    block_accepted[block_id] += 1
                    infill_accepted += 1
                    made_progress = True
                    placed = True
                    break
            cursors[block_id] = cursor
            if (
                block_accepted[block_id] >= block["target_buildings"]
                or cursor >= len(values)
            ):
                completed.append(block_id)
            elif not placed:
                completed.append(block_id)
        active.difference_update(completed)
        if not made_progress:
            break

    requested_density_target = target_count + max(0, int(density_extra))
    density_target = (
        requested_density_target
        if fill_courtyards
        else min(
            int(block_data["target_building_count"]),
            requested_density_target,
        )
    )
    secondary_infill_accepted = 0
    for placement in candidates:
        if len(accepted) >= density_target:
            break
        if placement["band_index"] < 2:
            continue
        block = block_index.locate(build_scene, placement["x"], placement["y"])
        if block is not None:
            if block_accepted[block["id"]] >= block["target_buildings"]:
                continue
            placement["block_id"] = block["id"]
        if not try_accept(
            placement,
            block=block,
            protect_courtyard=block is not None,
        ):
            continue
        secondary_infill_accepted += 1
        if block is not None:
            block_accepted[block["id"]] += 1

    courtyard_grid_accepted = 0
    courtyard_band_accepted = 0
    if fill_courtyards and len(accepted) < density_target:
        courtyard_candidates = {
            block["id"]: [
                medieval_infill_placement(candidate, block["id"])
                for candidate in medieval_courtyard_fill_candidates(
                    build_scene,
                    block,
                )
            ]
            for block in blocks
        }
        courtyard_cursors = {block["id"]: 0 for block in blocks}
        active_courtyards = {
            block["id"]
            for block in blocks
            if courtyard_candidates[block["id"]]
        }
        while active_courtyards and len(accepted) < density_target:
            made_progress = False
            completed = []
            for block_id in sorted(active_courtyards):
                block = block_lookup[block_id]
                values = courtyard_candidates[block_id]
                cursor = courtyard_cursors[block_id]
                placed = False
                while cursor < len(values):
                    placement = values[cursor]
                    cursor += 1
                    if try_accept(
                        placement,
                        block=block,
                        protect_courtyard=False,
                    ):
                        block_accepted[block_id] += 1
                        courtyard_grid_accepted += 1
                        made_progress = True
                        placed = True
                        break
                courtyard_cursors[block_id] = cursor
                if cursor >= len(values) or not placed:
                    completed.append(block_id)
                if len(accepted) >= density_target:
                    break
            active_courtyards.difference_update(completed)
            if not made_progress:
                break

    if fill_courtyards and len(accepted) < density_target:
        for source_placement in candidates:
            if len(accepted) >= density_target:
                break
            if source_placement["band_index"] < 2:
                continue
            block = block_index.locate(
                build_scene,
                source_placement["x"],
                source_placement["y"],
            )
            if block is None:
                continue
            placement = dict(source_placement)
            placement["block_id"] = block["id"]
            placement["infill_role"] = "courtyard_fill"
            placement["infill_pass"] = 20 + placement["band_index"]
            if not try_accept(
                placement,
                block=block,
                protect_courtyard=False,
            ):
                continue
            courtyard_band_accepted += 1
            block_accepted[block["id"]] += 1

    courtyard_fill_accepted = (
        courtyard_grid_accepted + courtyard_band_accepted
    )
    global_void_fill_accepted = 0
    if fill_courtyards and len(accepted) < density_target:
        minimum_x = min(point[0] for point in polygon)
        maximum_x = max(point[0] for point in polygon)
        minimum_y = min(point[1] for point in polygon)
        maximum_y = max(point[1] for point in polygon)
        void_candidates = []
        pitch_x = 0.166
        pitch_y = 0.176
        void_seed_base = seed
        row = 0
        y = minimum_y + pitch_y * 0.55
        while y <= maximum_y - pitch_y * 0.45:
            x = minimum_x + pitch_x * (0.55 + (0.5 if row % 2 else 0.0))
            column = 0
            while x <= maximum_x - pitch_x * 0.45:
                void_seed = (
                    void_seed_base * 1000003
                    + row * 1009
                    + column * 9176
                    + 330033
                ) % (2**31 - 1)
                if void_seed <= 0:
                    void_seed = 1
                rng = random.Random(void_seed)
                sample_x = x + rng.uniform(-0.008, 0.008)
                sample_y = y + rng.uniform(-0.008, 0.008)
                nearby_streets = list(
                    road_index.nearby(sample_x, sample_y)
                )
                if nearby_streets:
                    point = Vector((sample_x, sample_y))
                    street = min(
                        nearby_streets,
                        key=lambda item: point_segment_projection(
                            point,
                            item["start"],
                            item["end"],
                        )[1],
                    )
                    rotation = math.atan2(
                        street["end"][1] - street["start"][1],
                        street["end"][0] - street["start"][0],
                    )
                    source_osm_id = street["osm_id"]
                else:
                    rotation = rng.choice((0.0, math.pi * 0.5))
                    source_osm_id = -1
                rotation += rng.uniform(-0.012, 0.012)
                width = rng.uniform(0.108, 0.139)
                depth = rng.uniform(0.102, 0.134)
                variant = rng.randrange(MEDIEVAL_PROTOTYPE_COUNT)
                encoded_seed = (
                    void_seed
                    - void_seed % MEDIEVAL_PROTOTYPE_COUNT
                    + variant
                )
                block = block_index.locate(build_scene, sample_x, sample_y)
                placement = {
                    "x": sample_x,
                    "y": sample_y,
                    "width": width,
                    "depth": depth,
                    "height": rng.uniform(0.24, 0.47),
                    "rotation": rotation,
                    "street_angle": rotation,
                    "street_width": 0.06,
                    "street_index": -1,
                    "zone": "main",
                    "band": 99.0,
                    "band_index": 11,
                    "priority": rng.random(),
                    "seed": encoded_seed,
                    "prototype_variant": variant,
                    "source_osm_id": source_osm_id,
                    "plan_style": "standard",
                    "roof_style": rng.choices(
                        ["gable", "hip", "pyramid", "mansard"],
                        weights=[0.68, 0.24, 0.06, 0.02],
                        k=1,
                    )[0],
                    "timber": rng.random() < 0.31,
                    "chimney": rng.random() < 0.39,
                    "infill_role": "global_void_fill",
                    "infill_pass": 40,
                }
                if block is not None:
                    placement["block_id"] = block["id"]
                void_candidates.append(placement)
                x += pitch_x
                column += 1
            y += pitch_y
            row += 1
        void_candidates.sort(
            key=lambda item: (item["priority"], item["seed"])
        )
        for placement in void_candidates:
            if len(accepted) >= density_target:
                break
            block = (
                block_lookup.get(placement.get("block_id"))
                if "block_id" in placement
                else None
            )
            if not try_accept(
                placement,
                block=block,
                protect_courtyard=False,
            ):
                continue
            global_void_fill_accepted += 1
            if block is not None:
                block_accepted[block["id"]] += 1

    accepted_by_band = Counter(item["band_index"] for item in accepted)
    accepted_infill_passes = Counter(
        item.get("infill_pass")
        for item in accepted
        if "infill_pass" in item
    )
    infill_rejections = rejection_counts.copy()
    infill_rejections.subtract(base_rejections)
    fulfilled_blocks = sum(
        block_accepted[block["id"]] >= block["target_buildings"]
        for block in blocks
    )
    return accepted, {
        "target": target_count,
        "accepted": len(accepted),
        "candidate_count": len(candidates),
        "frontage_osm_way_count": len({item["osm_id"] for item in zone_streets}),
        "selection_mode": (
            "OSM blocks with dense courtyard fill"
            if fill_courtyards
            else "OSM block quotas with protected courtyards"
        ),
        "base_layer_accepted": base_layer_accepted,
        "infill_accepted": infill_accepted,
        "secondary_infill_accepted": secondary_infill_accepted,
        "courtyard_fill_accepted": courtyard_fill_accepted,
        "courtyard_grid_accepted": courtyard_grid_accepted,
        "courtyard_band_accepted": courtyard_band_accepted,
        "global_void_fill_accepted": global_void_fill_accepted,
        "density_target": density_target,
        "density_extra": density_extra,
        "fill_courtyards": fill_courtyards,
        "accepted_by_band": dict(sorted(accepted_by_band.items())),
        "accepted_infill_passes": dict(sorted(accepted_infill_passes.items())),
        "block_count": len(blocks),
        "block_target_buildings": block_data["target_building_count"],
        "block_infill_candidates": block_data["infill_candidate_count"],
        "fulfilled_blocks": fulfilled_blocks,
        "courtyard_area": block_data["courtyard_area"],
        "base_rejections": dict(base_rejections),
        "infill_rejections": {
            key: value
            for key, value in infill_rejections.items()
            if value
        },
        "rejections": dict(rejection_counts),
    }


def brighten_vicvs_materials():
    adjusted = []
    for material in bpy.data.materials:
        if not material.name.startswith("VICVS_") or not material.use_nodes:
            continue
        principled = next(
            (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
            None,
        )
        if principled is None:
            continue
        name = material.name.lower()
        if "window" in name:
            roughness = 0.22
            coat = 0.32
        elif "marble" in name or "water" in name:
            roughness = 0.28
            coat = 0.24
        elif "terracotta" in name:
            roughness = 0.48
            coat = 0.12
        elif "plaster" in name:
            roughness = 0.56
            coat = 0.10
        else:
            roughness = 0.58
            coat = 0.08
        principled.inputs["Roughness"].default_value = roughness
        if "Coat Weight" in principled.inputs:
            principled.inputs["Coat Weight"].default_value = coat
        if "Coat Roughness" in principled.inputs:
            principled.inputs["Coat Roughness"].default_value = min(0.25, roughness * 0.45)
        adjusted.append(material.name)
    return sorted(adjusted)


def hide_permanently(obj):
    obj.animation_data_clear()
    obj.hide_render = True
    obj.hide_viewport = True


def descendants(obj):
    result = []
    stack = list(obj.children)
    while stack:
        child = stack.pop()
        result.append(child)
        stack.extend(child.children)
    return result


def hide_legacy_bridge_geometry():
    hidden = []
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Bridge_Approach_") or obj.name.startswith("OSM_Bridgehead_"):
            hide_permanently(obj)
            hidden.append(obj.name)
    root = bpy.data.objects.get("Bridges")
    if root:
        for child in list(root.children):
            if child.name.startswith("Bridge_ile_de_la_cite_") or child.name == "OSM_Bridges_v21":
                for target in [child, *descendants(child)]:
                    hide_permanently(target)
                    hidden.append(target.name)
    return hidden


def add_cutwater(build_scene, name, center, tangent, material, parent, start_frame):
    tangent = Vector(tangent).normalized()
    normal = Vector((-tangent.y, tangent.x))
    half_length = 0.22
    half_width = 0.13
    bottom = -0.16
    top = 0.095
    plan = (
        Vector(center) + tangent * half_length,
        Vector(center) - tangent * half_length + normal * half_width,
        Vector(center) - tangent * half_length - normal * half_width,
    )
    vertices = [(*point, z) for z in (bottom, top) for point in plan]
    faces = ((0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0))
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    build_scene.animate_layer(obj, start_frame, duration=40)
    return obj


def add_arch_fascia(
    build_scene,
    name,
    start,
    end,
    side,
    deck_width,
    material,
    parent,
    start_frame,
):
    start = Vector(start)
    end = Vector(end)
    tangent = (end - start).normalized()
    normal = Vector((-tangent.y, tangent.x))
    offset = normal * side * deck_width * 0.48
    sample_count = 12
    vertices = []
    for index in range(sample_count + 1):
        amount = index / sample_count
        point = start.lerp(end, amount) + offset
        arch_bottom = -0.015 + 0.105 * math.sin(math.pi * amount)
        vertices.extend(
            (
                (point.x, point.y, 0.125),
                (point.x, point.y, arch_bottom),
            )
        )
    faces = [
        (index * 2, index * 2 + 2, index * 2 + 3, index * 2 + 1)
        for index in range(sample_count)
    ]
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    build_scene.animate_layer(obj, start_frame, duration=36)
    return obj


def polyline_length(points):
    return sum((Vector(end) - Vector(start)).length for start, end in zip(points, points[1:]))


def point_along_polyline(points, amount):
    points = [Vector(point) for point in points]
    total = polyline_length(points)
    target = amount * total
    traversed = 0.0
    for start, end in zip(points, points[1:]):
        length = (end - start).length
        if traversed + length >= target:
            local = (target - traversed) / max(length, 1e-9)
            return start.lerp(end, local), (end - start).normalized()
        traversed += length
    return points[-1], (points[-1] - points[-2]).normalized()


def create_curved_approach(build_scene, endpoint, start_frame, material, parent):
    points = [Vector(point) for point in endpoint["points"]]
    if (points[-1] - points[0]).length < 0.012:
        return None
    top_start = 0.13
    top_end = 0.061 if endpoint["zone"] != "main" else -0.018
    start_width = 0.235
    end_width = max(0.09, endpoint["road_width"])
    thickness = 0.038
    vertices = []
    for index, point in enumerate(points):
        if index == 0:
            tangent = (points[1] - points[0]).normalized()
        elif index == len(points) - 1:
            tangent = (points[-1] - points[-2]).normalized()
        else:
            tangent = (points[index + 1] - points[index - 1]).normalized()
        normal = Vector((-tangent.y, tangent.x))
        amount = index / (len(points) - 1)
        width = start_width * (1.0 - amount) + end_width * amount
        top = top_start * (1.0 - amount) + top_end * amount
        left = point + normal * width * 0.5
        right = point - normal * width * 0.5
        vertices.extend(
            (
                (left.x, left.y, top),
                (right.x, right.y, top),
                (left.x, left.y, top - thickness),
                (right.x, right.y, top - thickness),
            )
        )
    faces = []
    for index in range(len(points) - 1):
        a = index * 4
        b = (index + 1) * 4
        faces.extend(
            (
                (a, a + 1, b + 1, b),
                (a + 2, b + 2, b + 3, a + 3),
                (a, b, b + 2, a + 2),
                (a + 1, a + 3, b + 3, b + 1),
            )
        )
    faces.extend(((0, 2, 3, 1), (len(vertices) - 4, len(vertices) - 3, len(vertices) - 1, len(vertices) - 2)))
    mesh = bpy.data.meshes.new(f"{endpoint['name']}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(endpoint["name"], mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj["topology_source"] = "OSM bridge endpoint to OSM road tangent transition"
    obj["road_osm_id"] = endpoint["road_osm_id"]
    obj.shape_key_add(name="Basis")
    collapsed = obj.shape_key_add(name="Road_Draw_Collapsed")
    for index in range(4, len(vertices)):
        collapsed.data[index].co = collapsed.data[index % 4].co
    build_scene.animate_road_draw(obj, collapsed, start_frame, 30)
    return obj


def build_osm_bridges(build_scene, definitions):
    parent = bpy.data.objects.get("Bridges")
    root = bpy.data.objects.new("OSM_Bridges_v21", None)
    root.empty_display_type = "PLAIN_AXES"
    bpy.context.collection.objects.link(root)
    if parent:
        root.parent = parent
    deck_material = bpy.data.materials.get("Road_Material")
    stone_material = bpy.data.materials.get("Bridge_Stone")
    if deck_material is None or stone_material is None:
        raise RuntimeError("Missing bridge materials")
    report = []
    for definition in definitions:
        bridge_root = bpy.data.objects.new(f"OSM_Bridge_{definition['osm_id']}", None)
        bridge_root.empty_display_type = "PLAIN_AXES"
        bpy.context.collection.objects.link(bridge_root)
        bridge_root.parent = root
        bridge_root["osm_way_id"] = int(definition["osm_id"])
        bridge_root["topology_source"] = "OpenStreetMap bridge centerline"
        points = [Vector(point) for point in definition["points"]]
        total_length = polyline_length(points)
        deck_width = max(0.235, ROAD_WIDTHS.get(definition["road_class"], 0.11) + 0.07)
        deck_piece_count = 0
        for segment_index, (start, end) in enumerate(zip(points, points[1:])):
            segment = end - start
            segment_length = segment.length
            subdivisions = max(2, math.ceil(segment_length / 0.27))
            tangent = segment.normalized()
            normal = Vector((-tangent.y, tangent.x))
            angle = math.atan2(segment.y, segment.x) - math.pi * 0.5
            for piece_index in range(subdivisions):
                amount_start = piece_index / subdivisions
                amount_end = (piece_index + 1) / subdivisions
                piece_start = start.lerp(end, amount_start)
                piece_end = start.lerp(end, amount_end)
                center = (piece_start + piece_end) * 0.5
                length = (piece_end - piece_start).length
                frame = definition["start_frame"] + 34 + round(
                    deck_piece_count * 58 / max(1, math.ceil(total_length / 0.27))
                )
                deck = build_scene.add_cube(
                    f"OSM_Bridge_{definition['osm_id']}_Deck_{deck_piece_count:02d}",
                    (center.x, center.y, 0.13),
                    (deck_width, length + 0.035, 0.068),
                    deck_material,
                    bridge_root,
                )
                deck.rotation_euler[2] = angle
                build_scene.animate_axis_growth(deck, frame, 28, axis="Y")
                for rail_side in (-1.0, 1.0):
                    rail_center = center + normal * rail_side * deck_width * 0.43
                    rail = build_scene.add_cube(
                        f"OSM_Bridge_{definition['osm_id']}_Rail_{deck_piece_count:02d}_{int(rail_side)}",
                        (rail_center.x, rail_center.y, 0.192),
                        (0.026, length + 0.038, 0.055),
                        stone_material,
                        bridge_root,
                    )
                    rail.rotation_euler[2] = angle
                    build_scene.animate_axis_growth(rail, frame + 12, 24, axis="Y")
                deck_piece_count += 1
        pier_count = max(1, min(3, round(total_length / 0.72)))
        for pier_index in range(1, pier_count + 1):
            center, tangent = point_along_polyline(points, pier_index / (pier_count + 1))
            pier_frame = definition["start_frame"] + (pier_index - 1) * 12
            pier = build_scene.add_cylinder(
                f"OSM_Bridge_{definition['osm_id']}_Pier_{pier_index:02d}",
                (center.x, center.y, -0.025),
                0.14,
                0.34,
                stone_material,
                bridge_root,
                vertices=12,
            )
            build_scene.animate_layer(pier, pier_frame, duration=46)
            cap = build_scene.add_cube(
                f"OSM_Bridge_{definition['osm_id']}_PierCap_{pier_index:02d}",
                (center.x, center.y, 0.09),
                (0.31, 0.22, 0.075),
                stone_material,
                bridge_root,
            )
            cap.rotation_euler[2] = math.atan2(tangent.y, tangent.x)
            build_scene.animate_layer(cap, pier_frame + 18, duration=32)
            add_cutwater(
                build_scene,
                f"OSM_Bridge_{definition['osm_id']}_Cutwater_{pier_index:02d}",
                center,
                tangent,
                stone_material,
                bridge_root,
                pier_frame + 8,
            )
        arch_count = 0
        for span_index in range(pier_count + 1):
            span_start, _ = point_along_polyline(points, span_index / (pier_count + 1))
            span_end, _ = point_along_polyline(points, (span_index + 1) / (pier_count + 1))
            for side in (-1.0, 1.0):
                add_arch_fascia(
                    build_scene,
                    f"OSM_Bridge_{definition['osm_id']}_Arch_{span_index:02d}_{int(side)}",
                    span_start,
                    span_end,
                    side,
                    deck_width,
                    stone_material,
                    bridge_root,
                    definition["start_frame"] + 32 + span_index * 9,
                )
                arch_count += 1
        approaches = []
        for endpoint_index, endpoint in enumerate(definition["endpoints"]):
            approach = create_curved_approach(
                build_scene,
                endpoint,
                definition["start_frame"] + 18 + endpoint_index * 7,
                deck_material,
                bridge_root,
            )
            if approach:
                approaches.append(approach.name)
        report.append(
            {
                "osm_way_id": definition["osm_id"],
                "era": definition["era"],
                "length": total_length,
                "deck_pieces": deck_piece_count,
                "piers": pier_count,
                "arch_fascias": arch_count,
                "approaches": approaches,
                "endpoints": [
                    {
                        "zone": item["zone"],
                        "source_gap": item["source_gap"],
                        "road_osm_id": item["road_osm_id"],
                        "terrain_river_clearance": build_scene.river_clearance(
                            *item["bridge_endpoint"]
                        ),
                        "bridge_endpoint_gap_after": 0.0,
                        "road_centerline_gap_after": 0.0,
                    }
                    for item in definition["endpoints"]
                ],
            }
        )
    return report


def copy_action(source, target):
    if source is None:
        return
    target.animation_data_create()
    target.animation_data.action = source


def rebuild_cite_wall(build_scene, bridge_definitions):
    root = bpy.data.objects.get("Landmark_Medieval_Cite_Wall")
    if root is None:
        return {"status": "missing"}
    old_objects = [
        obj
        for obj in descendants(root)
        if obj.type == "MESH" and (obj.name.startswith("Cite_Wall_") or obj.name.startswith("Cite_Gate_"))
    ]
    source_action = next(
        (
            obj.animation_data.action
            for obj in old_objects
            if obj.animation_data and obj.animation_data.action
        ),
        None,
    )
    wall_source = bpy.data.objects.get("Cite_Wall_00")
    roof_source = bpy.data.objects.get("Cite_Wall_Tower_Roof_00")
    material = (
        wall_source.material_slots[0].material
        if wall_source and wall_source.material_slots
        else bpy.data.materials.get("Bridge_Stone")
    )
    roof_material = (
        roof_source.material_slots[0].material
        if roof_source and roof_source.material_slots
        else material
    )
    for obj in old_objects:
        hide_permanently(obj)
    polygon = [Vector(point) for point in build_scene.load_geodata()["islands"]["ile_de_la_cite"]]
    gate_points = []
    for definition in bridge_definitions:
        for endpoint in definition["endpoints"]:
            if endpoint["zone"] == "cite":
                point = Vector(endpoint["bridge_endpoint"])
                nearest = None
                for edge_index, (start, end) in enumerate(zip(polygon, polygon[1:] + polygon[:1])):
                    projected, amount = point_segment_projection(point, start, end)
                    distance = (projected - point).length
                    if nearest is None or distance < nearest[0]:
                        nearest = (distance, edge_index, amount, projected)
                gate_points.append(nearest)
    by_edge = defaultdict(list)
    for distance, edge_index, amount, point in gate_points:
        by_edge[edge_index].append((amount, point, distance))
    created = []
    opening_half = 0.205
    for edge_index, (start, end) in enumerate(zip(polygon, polygon[1:] + polygon[:1])):
        vector = end - start
        length = vector.length
        tangent = vector.normalized()
        angle = math.atan2(vector.y, vector.x)
        intervals = [(0.0, 1.0)]
        for amount, _point, _distance in sorted(by_edge.get(edge_index, ())):
            half_amount = opening_half / max(length, 1e-6)
            gap_start = max(0.0, amount - half_amount)
            gap_end = min(1.0, amount + half_amount)
            next_intervals = []
            for interval_start, interval_end in intervals:
                if gap_end <= interval_start or gap_start >= interval_end:
                    next_intervals.append((interval_start, interval_end))
                    continue
                if gap_start > interval_start + 0.01:
                    next_intervals.append((interval_start, gap_start))
                if gap_end < interval_end - 0.01:
                    next_intervals.append((gap_end, interval_end))
            intervals = next_intervals
        for piece_index, (amount_start, amount_end) in enumerate(intervals):
            piece_start = start.lerp(end, amount_start)
            piece_end = start.lerp(end, amount_end)
            center = (piece_start + piece_end) * 0.5
            wall = build_scene.add_cube(
                f"Cite_Wall_v21_{edge_index:02d}_{piece_index:02d}",
                (center.x, center.y, 0.20),
                ((piece_end - piece_start).length + 0.018, 0.10, 0.29),
                material,
                root,
            )
            wall.rotation_euler[2] = angle
            if source_action:
                copy_action(source_action, wall)
            else:
                build_scene.animate_layer(wall, 780, duration=64)
            created.append(wall.name)
        for gate_index, (_amount, center, _distance) in enumerate(by_edge.get(edge_index, ())):
            for side_index, side in enumerate((-1.0, 1.0)):
                tower_center = center + tangent * side * (opening_half + 0.075)
                tower = build_scene.add_cylinder(
                    f"Cite_Gate_v21_{edge_index:02d}_{gate_index:02d}_Tower_{side_index}",
                    (tower_center.x, tower_center.y, 0.275),
                    0.112,
                    0.50,
                    material,
                    root,
                    vertices=12,
                )
                roof = build_scene.add_cone(
                    f"Cite_Gate_v21_{edge_index:02d}_{gate_index:02d}_Roof_{side_index}",
                    (tower_center.x, tower_center.y, 0.615),
                    0.145,
                    0.0,
                    0.18,
                    roof_material,
                    root,
                    vertices=12,
                )
                if source_action:
                    copy_action(source_action, tower)
                    copy_action(source_action, roof)
                else:
                    build_scene.animate_layer(tower, 790, duration=56)
                    build_scene.animate_layer(roof, 810, duration=42)
                created.extend((tower.name, roof.name))
            lintel = build_scene.add_cube(
                f"Cite_Gate_v21_{edge_index:02d}_{gate_index:02d}_Lintel",
                (center.x, center.y, 0.47),
                (opening_half * 2.0 + 0.15, 0.12, 0.12),
                material,
                root,
            )
            lintel.rotation_euler[2] = angle
            if source_action:
                copy_action(source_action, lintel)
            else:
                build_scene.animate_layer(lintel, 812, duration=42)
            created.append(lintel.name)
    return {
        "status": "rebuilt",
        "gate_count": len(gate_points),
        "created_objects": len(created),
        "maximum_source_endpoint_to_wall": max((item[0] for item in gate_points), default=0.0),
    }


def mark_road_chunks(prefix, streets):
    objects = [obj for obj in bpy.data.objects if obj.name.startswith(prefix)]
    source_ids = sorted({int(street["osm_id"]) for street in streets if street["kind"] == "osm"})
    for obj in objects:
        obj["topology_source"] = "OpenStreetMap centerlines"
        obj["osm_way_count"] = len(source_ids)
    return len(objects)


def group_prefixes(era):
    if era == "roman":
        return {
            "main": "Buildings_Roman_State_Chunk_",
            "cite": "Island_Cite_0_State_Chunk_",
            "saint_louis": "Island_Saint_Louis_0_State_Chunk_",
        }
    return {
        "main": "Buildings_Medieval_State_Chunk_",
        "cite": "Island_Cite_1_State_Chunk_",
        "saint_louis": "Island_Saint_Louis_1_State_Chunk_",
    }


def main():
    args = parse_args()
    build_scene, roman, medieval, upgrade = load_project_modules()
    medieval_base = medieval.base
    install_asymmetric_river(build_scene)
    roman.BANK_OUTER_WIDTH = RIVERBANK_WIDTH
    roman.MAIN_FLOODPLAIN_SETBACK = RIVERBANK_WIDTH
    medieval_base.BANK_OUTER_WIDTH = RIVERBANK_WIDTH
    medieval_base.FLOODPLAIN_SETBACK = RIVERBANK_WIDTH
    terrain_report = rebuild_asymmetric_terrain(build_scene, roman)
    if args.terrain_only:
        water_report = medieval.stabilize_water()
        scene = bpy.context.scene
        scene["v30_terrain"] = "Shoreline-conforming bank mesh with covered terrain joins"
        args.output_blend.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.output_blend.resolve()), compress=True)
        report = {
            "version": "v30",
            "mode": "terrain-only refinement from v29",
            "output_blend": str(args.output_blend.resolve()),
            "terrain": terrain_report,
            "water": water_report,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return

    if args.roman_kit is None or args.medieval_kit is None:
        raise RuntimeError("Full rebuild requires --roman-kit and --medieval-kit")

    roman_streets, roman_way_ids = build_osm_streets(build_scene, "roman")
    medieval_streets, medieval_way_ids = build_osm_streets(build_scene, "medieval")
    bridge_definitions, connector_streets = load_bridge_definitions(
        build_scene,
        medieval_streets,
    )
    roman_bridge_ids = {item["osm_id"] for item in bridge_definitions if item["era"] == "roman"}
    roman_connectors = [
        street for street in connector_streets if street["osm_id"] in roman_bridge_ids
    ]
    roman_streets.extend(roman_connectors)
    medieval_streets.extend(connector_streets)

    target_counts = {
        "roman": {
            "main": roman.MAIN_BUILDING_COUNT,
            "cite": roman.CITE_BUILDING_COUNT,
            "saint_louis": roman.SAINT_LOUIS_BUILDING_COUNT,
        },
        "medieval": {
            "main": medieval_base.MAIN_BUILDING_COUNT,
            "cite": medieval_base.CITE_BUILDING_COUNT,
            "saint_louis": medieval_base.SAINT_LOUIS_BUILDING_COUNT,
        },
    }
    placements = {"roman": {}, "medieval": {}}
    placement_reports = {"roman": {}, "medieval": {}}
    for era, streets, seed_base in (
        ("roman", roman_streets, 21100),
        ("medieval", medieval_streets, 22100),
    ):
        for zone_index, zone in enumerate(("main", "cite", "saint_louis")):
            placements[era][zone], placement_reports[era][zone] = generate_aligned_placements(
                build_scene,
                streets,
                era,
                zone,
                target_counts[era][zone],
                seed_base + zone_index,
            )

    roman_prototypes = [
        upgrade.import_prototype(path)
        for path in sorted(args.roman_kit.resolve().glob("roman_townhouse_*.glb"))
    ]
    medieval_prototypes = [
        upgrade.import_prototype(path)
        for path in sorted(args.medieval_kit.resolve().glob("medieval_townhouse_*.glb"))
    ]
    if len(roman_prototypes) != ROMAN_PROTOTYPE_COUNT:
        raise RuntimeError(f"Expected {ROMAN_PROTOTYPE_COUNT} VICVS Roman GLBs")
    if len(medieval_prototypes) != MEDIEVAL_PROTOTYPE_COUNT:
        raise RuntimeError(f"Expected {MEDIEVAL_PROTOTYPE_COUNT} medieval GLBs")
    adjusted_materials = brighten_vicvs_materials()

    original_use_detail = upgrade.use_detail
    upgrade.use_detail = lambda _bs, _era, _placement: True
    timber_material = medieval_base.ensure_timber_material()
    building_reports = {"roman": {}, "medieval": {}}
    for era, prototypes in (
        ("roman", roman_prototypes),
        ("medieval", medieval_prototypes),
    ):
        for zone, prefix in group_prefixes(era).items():
            building_reports[era][zone] = upgrade.rebuild_group(
                build_scene,
                roman,
                medieval_base,
                era,
                prefix,
                placements[era][zone],
                prototypes,
                [],
                timber_material=timber_material if era == "medieval" else None,
            )
    upgrade.use_detail = original_use_detail

    roman_road_chunks, roman_road_pieces = roman.rebuild_roman_roads(
        build_scene,
        roman_streets,
    )
    medieval_road_chunks, medieval_road_pieces = medieval_base.rebuild_medieval_roads(
        build_scene,
        roman,
        medieval_streets,
    )
    mark_road_chunks("Roads_0_Chunk_", roman_streets)
    mark_road_chunks("Roads_1_Chunk_", medieval_streets)

    hidden_legacy = hide_legacy_bridge_geometry()
    bridge_report = build_osm_bridges(build_scene, bridge_definitions)
    wall_report = rebuild_cite_wall(build_scene, bridge_definitions)

    scene = bpy.context.scene
    scene["v24_road_topology"] = "OpenStreetMap centerlines with tangent-continuous bridgeheads"
    scene["v24_roman_architecture"] = "VICVS ROMANVS historical Three.js source"
    scene["v24_osm_attribution"] = build_scene.load_geodata()["attribution"]
    scene["v31_medieval_infill"] = "OSM-polygonized blocks with protected compact courtyards"
    scene["v32_medieval_density"] = "Closed-block infill plus open-block deep frontage bands"
    args.output_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output_blend.resolve()), compress=True)

    report = {
        "version": "v32",
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output_blend.resolve()),
        "architecture": {
            "source": "VICVS ROMANVS procedural Three.js source recovered from Codex history",
            "roman_prototypes": len(roman_prototypes),
            "medieval_prototypes": len(medieval_prototypes),
            "adjusted_vicvs_materials": adjusted_materials,
            "all_visible_houses_detailed": True,
        },
        "roads": {
            "attribution": build_scene.load_geodata()["attribution"],
            "roman": {
                "source_way_count": len(roman_way_ids),
                "street_segments": len(roman_streets),
                "road_chunks": roman_road_chunks,
                "rendered_pieces": roman_road_pieces,
                "class_counts": dict(Counter(item["road_class"] for item in roman_streets)),
            },
            "medieval": {
                "source_way_count": len(medieval_way_ids),
                "street_segments": len(medieval_streets),
                "road_chunks": medieval_road_chunks,
                "rendered_pieces": medieval_road_pieces,
                "class_counts": dict(Counter(item["road_class"] for item in medieval_streets)),
            },
            "deduplication": "quantized exact centerline duplicates only; geometry remains OSM-derived",
        },
        "terrain": terrain_report,
        "placements": placement_reports,
        "buildings": building_reports,
        "bridges": bridge_report,
        "wall": wall_report,
        "legacy_bridge_objects_hidden": len(hidden_legacy),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
