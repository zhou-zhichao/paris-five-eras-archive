import argparse
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cathedral_local(x, y):
    center_x, center_y, rotation = 0.15, 0.25, -0.55
    delta_x = x - center_x
    delta_y = y - center_y
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    return (
        delta_x * cos_r + delta_y * sin_r,
        -delta_x * sin_r + delta_y * cos_r,
    )


def main():
    args = parse_args()
    blender_dir = Path(__file__).resolve().parent
    v17 = load_module(blender_dir / "rebuild_medieval_urbanism_v17.py", "cite_v17")
    bs, roman_helpers = v17.base.project_modules()
    streets = v17.base.medieval_streets(bs, roman_helpers)
    placements, footprint_index = v17.base.generate_placements(
        bs,
        streets,
        "cite",
        v17.base.CITE_BUILDING_COUNT,
        16202,
    )

    rows = []
    kinds = Counter()
    quadrants = Counter()
    for placement in placements:
        local_x, local_y = cathedral_local(placement["x"], placement["y"])
        kind = streets[placement["street_index"]]["kind"]
        if abs(local_x) < 2.8 and abs(local_y) < 1.8:
            kinds[kind] += 1
            quadrants[("east" if local_x >= 0 else "west") + "_" + ("north" if local_y >= 0 else "south")] += 1
            rows.append(
                {
                    "local": [local_x, local_y],
                    "size": [placement["width"], placement["depth"], placement["height"]],
                    "street_kind": kind,
                    "street_index": placement["street_index"],
                    "band": placement["band"],
                }
            )

    manual_candidates = []
    manual_rejections = []
    rejection_reasons = Counter()
    polygon = v17.base.zone_polygon(bs, "cite")
    for local_y in (-0.62, -0.4, -0.18, 0.04, 0.26, 0.48, 0.7):
        for local_x in (1.3, 1.5, 1.7, 1.9, 2.1, 2.3):
            x, y = v17.rotated_point(0.15, 0.25, -0.55, local_x, local_y)
            candidate = {
                "x": x,
                "y": y,
                "width": 0.16,
                "depth": 0.135,
                "height": 0.4,
                "rotation": -0.55,
                "plan_style": "standard",
                "zone": "cite",
            }
            half_width, half_depth = bs.house_half_extents(0.16, 0.135, "standard")
            radius = math.hypot(half_width, half_depth)
            footprint = (x, y, half_width, half_depth, -0.55)
            if not v17.base.zone_contains(bs, "cite", x, y):
                rejection_reasons["outside"] += 1
                manual_rejections.append([local_x, local_y, "outside"])
                continue
            if bs.polygon_edge_distance(x, y, polygon) < radius + 0.035:
                rejection_reasons["edge"] += 1
                manual_rejections.append([local_x, local_y, "edge"])
                continue
            if not v17.base.clear_of_streets(bs, candidate, streets, extra=0.006):
                rejection_reasons["street"] += 1
                manual_rejections.append([local_x, local_y, "street"])
                continue
            if not footprint_index.can_add(footprint):
                rejection_reasons["building"] += 1
                manual_rejections.append([local_x, local_y, "building"])
                continue
            footprint_index.add(footprint)
            manual_candidates.append([local_x, local_y])

    report = {
        "total": len(placements),
        "near_cathedral": len(rows),
        "kinds": dict(kinds),
        "quadrants": dict(quadrants),
        "manual_search": {
            "accepted": manual_candidates,
            "rejections": dict(rejection_reasons),
            "rejection_map": manual_rejections,
        },
        "east_streets": [
            {
                "index": index,
                "kind": street["kind"],
                "start": list(cathedral_local(*street["start"])),
                "end": list(cathedral_local(*street["end"])),
                "width": street["width"],
            }
            for index, street in enumerate(streets)
            if street["zone"] == "cite"
            and max(
                cathedral_local(*street["start"])[0],
                cathedral_local(*street["end"])[0],
            )
            > 0.8
        ],
        "island_polygon_local": [
            list(cathedral_local(x, y))
            for x, y in v17.base.zone_polygon(bs, "cite")
        ],
        "placements": sorted(rows, key=lambda row: (row["local"][1], row["local"][0])),
    }
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"placements", "island_polygon_local", "east_streets"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
