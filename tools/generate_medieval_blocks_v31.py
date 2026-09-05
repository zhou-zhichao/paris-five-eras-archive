import argparse
import ast
import json
import math
import random
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
VENDOR_DIR = PROJECT_DIR / "tools" / "python_vendor"
sys.path.insert(0, str(VENDOR_DIR))

from shapely import affinity  # noqa: E402
from shapely.geometry import LineString, Point, Polygon, box  # noqa: E402
from shapely.ops import polygonize, unary_union  # noqa: E402


ROAD_CLASSES = {
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "unclassified",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_DIR / "data" / "medieval_blocks_v31.json",
    )
    parser.add_argument(
        "--svg",
        type=Path,
        default=PROJECT_DIR / "reports" / "medieval_blocks_v31.svg",
    )
    return parser.parse_args()


def load_city_polygons():
    source_path = PROJECT_DIR / "blender" / "build_scene.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "CITY_POLYGONS"
            for target in node.targets
        ):
            continue
        return ast.literal_eval(node.value)
    raise RuntimeError("CITY_POLYGONS was not found")


def polygon_parts(geometry, minimum_area=0.012):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry] if geometry.area >= minimum_area else []
    return [
        item
        for item in geometry.geoms
        if item.geom_type == "Polygon" and item.area >= minimum_area
    ]


def courtyard_geometry(block):
    if block.area < 0.62:
        return []
    if block.area < 2.0:
        target_ratio = 0.12
    elif block.area < 8.0:
        target_ratio = 0.18
    else:
        target_ratio = 0.22
    target_area = block.area * target_ratio
    low = 0.0
    high = max(0.4, math.sqrt(block.area))
    while not block.buffer(-high).is_empty:
        high *= 1.7
    for _iteration in range(36):
        distance = (low + high) * 0.5
        inset = block.buffer(-distance, join_style="mitre")
        if inset.area > target_area:
            low = distance
        else:
            high = distance
    inset = block.buffer(-high, join_style="mitre").simplify(
        0.006,
        preserve_topology=True,
    )
    return polygon_parts(inset)


def rounded_ring(polygon):
    return [[round(x, 5), round(y, 5)] for x, y in polygon.exterior.coords[:-1]]


def dominant_angle(polygon):
    points = list(polygon.exterior.coords)
    longest = max(
        zip(points, points[1:]),
        key=lambda pair: math.dist(pair[0], pair[1]),
    )
    angle = math.atan2(
        longest[1][1] - longest[0][1],
        longest[1][0] - longest[0][0],
    )
    while angle > math.pi * 0.5:
        angle -= math.pi
    while angle <= -math.pi * 0.5:
        angle += math.pi
    return angle


def infill_candidates(block_id, polygon, courtyards, target_buildings):
    angle = dominant_angle(polygon)
    angle_degrees = math.degrees(angle)
    center = (polygon.centroid.x, polygon.centroid.y)
    buildable = polygon.buffer(-0.14, join_style="mitre")
    if buildable.is_empty:
        return []
    local_buildable = affinity.rotate(
        buildable,
        -angle_degrees,
        origin=center,
    )
    local_courtyards = [
        affinity.rotate(item, -angle_degrees, origin=center)
        for item in courtyards
    ]
    minimum_x, minimum_y, maximum_x, maximum_y = local_buildable.bounds
    pitch_x = 0.165
    pitch_y = 0.175
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    candidates = []
    seen = set()
    for pass_index, (offset_x, offset_y) in enumerate(((0.0, 0.0), (0.5, 0.5))):
        row = 0
        y = minimum_y + pitch_y * (0.5 + offset_y)
        while y <= maximum_y - pitch_y * 0.35:
            alley_shift = (row // 8) * 0.035
            x = minimum_x + pitch_x * (0.5 + offset_x) + alley_shift
            column = 0
            while x <= maximum_x - pitch_x * 0.35:
                seed = (
                    (block_id + 1) * 1000003
                    + pass_index * 100003
                    + row * 1009
                    + column * 9176
                )
                rng = random.Random(seed)
                width = rng.uniform(0.118, 0.158)
                depth = rng.uniform(0.108, 0.148)
                jitter_x = rng.uniform(-0.008, 0.008)
                jitter_y = rng.uniform(-0.007, 0.007)
                candidate_x = x + jitter_x
                candidate_y = y + jitter_y
                footprint = box(
                    candidate_x - width * 0.5 - 0.004,
                    candidate_y - depth * 0.5 - 0.004,
                    candidate_x + width * 0.5 + 0.004,
                    candidate_y + depth * 0.5 + 0.004,
                )
                if not local_buildable.covers(footprint):
                    x += pitch_x
                    column += 1
                    continue
                if any(courtyard.intersects(footprint) for courtyard in local_courtyards):
                    x += pitch_x
                    column += 1
                    continue
                delta_x = candidate_x - center[0]
                delta_y = candidate_y - center[1]
                world_x = center[0] + delta_x * cos_angle - delta_y * sin_angle
                world_y = center[1] + delta_x * sin_angle + delta_y * cos_angle
                key = (round(world_x / 0.018), round(world_y / 0.018))
                if key in seen:
                    x += pitch_x
                    column += 1
                    continue
                seen.add(key)
                boundary_distance = polygon.boundary.distance(Point(world_x, world_y))
                candidates.append(
                    {
                        "x": round(world_x, 5),
                        "y": round(world_y, 5),
                        "width": round(width, 5),
                        "depth": round(depth, 5),
                        "rotation": round(angle + rng.uniform(-0.012, 0.012), 7),
                        "seed": seed,
                        "priority": round(
                            boundary_distance + pass_index * 0.42 + rng.random() * 0.04,
                            6,
                        ),
                        "pass_index": pass_index,
                        "role": "rear_row" if row % 4 else "workshop_row",
                    }
                )
                x += pitch_x
                column += 1
            y += pitch_y + (0.035 if row % 8 == 7 else 0.0)
            row += 1
    candidates.sort(key=lambda item: (item["priority"], item["seed"]))
    return candidates


def build_blocks():
    city_polygon = Polygon(load_city_polygons()[1])
    geodata = json.loads(
        (PROJECT_DIR / "data" / "paris_geodata.json").read_text(encoding="utf-8")
    )
    islands = [Polygon(points) for points in geodata["islands"].values()]
    linework = [city_polygon.boundary]
    source_way_ids = set()
    source_segment_count = 0
    for road in geodata["roads"]:
        if road["bridge"] or road["class"] not in ROAD_CLASSES:
            continue
        for start, end in zip(road["points"], road["points"][1:]):
            midpoint = Point(
                (start[0] + end[0]) * 0.5,
                (start[1] + end[1]) * 0.5,
            )
            if not city_polygon.covers(midpoint):
                continue
            if any(island.covers(midpoint) for island in islands):
                continue
            segment = LineString((start, end)).intersection(city_polygon)
            if segment.is_empty:
                continue
            linework.append(segment)
            source_way_ids.add(int(road["id"]))
            source_segment_count += 1

    merged = unary_union(linework)
    candidates = []
    for polygon in polygonize(merged):
        representative = polygon.representative_point()
        if not city_polygon.covers(representative):
            continue
        if any(island.covers(representative) for island in islands):
            continue
        if not 0.12 <= polygon.area <= 40.0:
            continue
        candidates.append(polygon.simplify(0.006, preserve_topology=True))

    candidates.sort(
        key=lambda polygon: (
            round(polygon.centroid.y, 5),
            round(polygon.centroid.x, 5),
            round(polygon.area, 5),
        )
    )
    blocks = []
    for block_id, polygon in enumerate(candidates):
        courtyards = courtyard_geometry(polygon)
        target_buildings = max(
            3,
            round(polygon.area * 17.0 + polygon.length * 1.5),
        )
        blocks.append(
            {
                "id": block_id,
                "polygon": rounded_ring(polygon),
                "bbox": [round(value, 5) for value in polygon.bounds],
                "area": round(polygon.area, 5),
                "perimeter": round(polygon.length, 5),
                "target_buildings": target_buildings,
                "courtyards": [rounded_ring(item) for item in courtyards],
                "courtyard_area": round(sum(item.area for item in courtyards), 5),
                "infill_candidates": infill_candidates(
                    block_id,
                    polygon,
                    courtyards,
                    target_buildings,
                ),
            }
        )
    return {
        "version": "v31",
        "source": "OpenStreetMap road centerlines polygonized into medieval infill blocks",
        "attribution": geodata["attribution"],
        "source_way_count": len(source_way_ids),
        "source_segment_count": source_segment_count,
        "block_count": len(blocks),
        "target_building_count": sum(item["target_buildings"] for item in blocks),
        "infill_candidate_count": sum(
            len(item["infill_candidates"])
            for item in blocks
        ),
        "block_area": round(sum(item["area"] for item in blocks), 5),
        "courtyard_area": round(sum(item["courtyard_area"] for item in blocks), 5),
        "blocks": blocks,
    }


def svg_path(points, transform):
    coordinates = [transform(x, y) for x, y in points]
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in coordinates) + " Z"


def write_svg(data, path):
    width = 1200
    height = 900
    margin = 28
    all_points = [point for block in data["blocks"] for point in block["polygon"]]
    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    scale = min(
        (width - margin * 2) / max(1e-6, max_x - min_x),
        (height - margin * 2) / max(1e-6, max_y - min_y),
    )

    def transform(x, y):
        return (
            margin + (x - min_x) * scale,
            height - margin - (y - min_y) * scale,
        )

    block_paths = "\n".join(
        f'<path d="{svg_path(block["polygon"], transform)}" />'
        for block in data["blocks"]
    )
    courtyard_paths = "\n".join(
        f'<path d="{svg_path(courtyard, transform)}" />'
        for block in data["blocks"]
        for courtyard in block["courtyards"]
    )
    markup = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#d8ddbd" />
<g fill="#c8a77a" stroke="#6f6248" stroke-width="0.8">{block_paths}</g>
<g fill="#75865c" stroke="#566345" stroke-width="0.7">{courtyard_paths}</g>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markup, encoding="utf-8")


def main():
    args = parse_args()
    data = build_blocks()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    write_svg(data, args.svg)
    print(
        json.dumps(
            {
                key: value
                for key, value in data.items()
                if key != "blocks"
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
