import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--density-extra", type=int, default=3000)
    parser.add_argument("--fill-courtyards", action="store_true")
    parser.add_argument("--cite-count", type=int)
    parser.add_argument("--saint-louis-count", type=int)
    return parser.parse_args(argv)


def load_upgrade():
    path = Path(__file__).resolve().parent / "upgrade_vicvs_osm_v21.py"
    specification = importlib.util.spec_from_file_location(
        "paris_v31_block_upgrade",
        path,
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def main():
    args = parse_args()
    upgrade = load_upgrade()
    build_scene, roman, medieval, _house_upgrade = upgrade.load_project_modules()
    upgrade.install_asymmetric_river(build_scene)
    streets, source_way_ids = upgrade.build_osm_streets(build_scene, "medieval")
    bridge_definitions, connector_streets = upgrade.load_bridge_definitions(
        build_scene,
        streets,
    )
    streets.extend(connector_streets)
    placements, placement_report = upgrade.generate_aligned_placements(
        build_scene,
        streets,
        "medieval",
        "main",
        medieval.base.MAIN_BUILDING_COUNT,
        22100,
        density_extra=args.density_extra,
        fill_courtyards=args.fill_courtyards,
    )
    block_counts = Counter(
        placement.get("block_id", "unassigned")
        for placement in placements
    )
    report = {
        "placement_report": placement_report,
        "source_way_count": len(source_way_ids),
        "bridge_count": len(bridge_definitions),
        "placement_count": len(placements),
        "assigned_to_blocks": sum(
            count for block_id, count in block_counts.items() if block_id != "unassigned"
        ),
        "unassigned": block_counts.get("unassigned", 0),
        "occupied_block_count": sum(
            1 for block_id in block_counts if block_id != "unassigned"
        ),
        "block_counts": {
            str(block_id): count
            for block_id, count in sorted(
                block_counts.items(),
                key=lambda item: str(item[0]),
            )
        },
    }
    island_targets = {
        "cite": args.cite_count,
        "saint_louis": args.saint_louis_count,
    }
    island_reports = {}
    for zone_index, (zone, target) in enumerate(island_targets.items(), start=1):
        if target is None:
            continue
        island_placements, island_report = upgrade.generate_aligned_placements(
            build_scene,
            streets,
            "medieval",
            zone,
            target,
            22100 + zone_index,
            fill_courtyards=args.fill_courtyards,
        )
        island_reports[zone] = {
            "placement_count": len(island_placements),
            "placement_report": island_report,
        }
    if island_reports:
        report["islands"] = island_reports
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "block_counts"}, indent=2))


if __name__ == "__main__":
    main()
