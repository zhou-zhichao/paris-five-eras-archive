import argparse
import json
import math
import statistics
from pathlib import Path


CENTER_LAT = 48.852968
CENTER_LON = 2.349902
UNITS_PER_KM = 10.0
KM_PER_DEG_LAT = 111.32
KM_PER_DEG_LON = KM_PER_DEG_LAT * math.cos(math.radians(CENTER_LAT))

ROAD_WIDTHS = {
    "motorway": 0.28,
    "trunk": 0.24,
    "primary": 0.18,
    "secondary": 0.14,
    "tertiary": 0.105,
    "residential": 0.058,
    "unclassified": 0.052,
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roads", type=Path, required=True)
    parser.add_argument("--river", type=Path, required=True)
    parser.add_argument("--cite", type=Path, required=True)
    parser.add_argument("--saint-louis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def to_local(lon, lat):
    x = (lon - CENTER_LON) * KM_PER_DEG_LON * UNITS_PER_KM
    y = (lat - CENTER_LAT) * KM_PER_DEG_LAT * UNITS_PER_KM
    return [round(x, 4), round(y, 4)]


def point_segment_distance(point, start, end):
    px, py = point
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length_sq))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def simplify(points, tolerance):
    if len(points) <= 2:
        return points
    first = points[0]
    last = points[-1]
    max_distance = -1.0
    split_index = 0
    for index, point in enumerate(points[1:-1], start=1):
        distance = point_segment_distance(point, first, last)
        if distance > max_distance:
            max_distance = distance
            split_index = index
    if max_distance <= tolerance:
        return [first, last]
    left = simplify(points[: split_index + 1], tolerance)
    right = simplify(points[split_index:], tolerance)
    return left[:-1] + right


def polyline_length(points):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def stable_fraction(osm_id):
    return ((osm_id * 2654435761) % 10000) / 10000.0


def assign_phase(osm_id, highway, points):
    center_x = sum(point[0] for point in points) / len(points)
    center_y = sum(point[1] for point in points) / len(points)
    radius = math.hypot(center_x * 0.9, center_y)
    value = stable_fraction(osm_id)

    if highway in {"motorway", "trunk"}:
        return 4
    if highway in {"primary", "secondary"}:
        if radius < 16.0 and value < 0.68:
            return 1
        if radius < 29.0 and value < 0.82:
            return 2
        if radius < 51.0 and value < 0.95:
            return 3
        return 4
    if highway == "tertiary":
        if radius < 16.0 and value < 0.48:
            return 1
        if radius < 29.0 and value < 0.72:
            return 2
        if radius < 49.0 and value < 0.9:
            return 3
        return 4
    if radius < 15.5 and value < 0.28:
        return 1
    if radius < 29.0 and value < 0.5:
        return 2
    if radius < 47.0 and value < 0.75:
        return 3
    return 4


def prepare_roads(path):
    source = json.loads(path.read_text(encoding="utf-8"))
    roads = []
    for element in source.get("elements", []):
        tags = element.get("tags", {})
        highway = tags.get("highway")
        geometry = element.get("geometry", [])
        if highway not in ROAD_WIDTHS or len(geometry) < 2:
            continue
        points = [to_local(point["lon"], point["lat"]) for point in geometry]
        points = [point for point in points if -92.0 <= point[0] <= 92.0 and -62.0 <= point[1] <= 62.0]
        if len(points) < 2:
            continue
        points = simplify(points, 0.045 if highway in {"primary", "secondary"} else 0.075)
        if polyline_length(points) < 0.14:
            continue
        osm_id = int(element["id"])
        roads.append(
            {
                "id": osm_id,
                "phase": assign_phase(osm_id, highway, points),
                "class": highway,
                "width": ROAD_WIDTHS[highway],
                "bridge": tags.get("bridge") not in {None, "no"},
                "points": points,
            }
        )
    roads.sort(key=lambda road: (road["phase"], road["class"], road["id"]))
    return roads


def prepare_river(path):
    source = json.loads(path.read_text(encoding="utf-8"))
    bins = {}
    for element in source.get("elements", []):
        name = element.get("tags", {}).get("name", "")
        if "Seine" not in name:
            continue
        for point in element.get("geometry", []):
            x, y = to_local(point["lon"], point["lat"])
            if -88.0 <= x <= 88.0 and -58.0 <= y <= 58.0:
                bins.setdefault(round(x), []).append(y)
    raw = [[float(x), statistics.median(values)] for x, values in sorted(bins.items())]
    if len(raw) < 20:
        raise RuntimeError("Unable to derive a continuous Seine centerline")
    smoothed = raw
    for radius in (5, 3):
        next_pass = []
        for index, (x, _) in enumerate(smoothed):
            window = smoothed[max(0, index - radius) : min(len(smoothed), index + radius + 1)]
            next_pass.append([x, round(statistics.mean(point[1] for point in window), 4)])
        smoothed = next_pass
    return simplify(smoothed, 0.08)


def prepare_island(path):
    source = json.loads(path.read_text(encoding="utf-8"))
    if not source:
        raise RuntimeError(f"No island geometry in {path}")
    geojson = source[0]["geojson"]
    coordinates = geojson["coordinates"]
    if geojson["type"] == "MultiPolygon":
        polygon = max(coordinates, key=lambda item: len(item[0]))[0]
    else:
        polygon = coordinates[0]
    points = [to_local(lon, lat) for lon, lat in polygon]
    if points[0] == points[-1]:
        points = points[:-1]
    return simplify(points, 0.035)


def main():
    args = parse_args()
    roads = prepare_roads(args.roads)
    river = prepare_river(args.river)
    islands = {
        "ile_de_la_cite": prepare_island(args.cite),
        "ile_saint_louis": prepare_island(args.saint_louis),
    }
    phase_counts = {phase: 0 for phase in range(1, 5)}
    for road in roads:
        phase_counts[road["phase"]] += 1
    payload = {
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        "coordinate_system": {
            "origin": [CENTER_LON, CENTER_LAT],
            "units_per_km": UNITS_PER_KM,
        },
        "roads": roads,
        "river": river,
        "islands": islands,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(
        json.dumps(
            {
                "roads": len(roads),
                "phase_counts": phase_counts,
                "river_points": len(river),
                "island_points": {name: len(points) for name, points in islands.items()},
                "output_bytes": args.output.stat().st_size,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
