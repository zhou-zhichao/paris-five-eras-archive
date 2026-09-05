import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--medieval-kit", type=Path, required=True)
    parser.add_argument("--output-blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--density-extra", type=int, default=6800)
    parser.add_argument("--version", default="v33")
    parser.add_argument("--cite-count", type=int, default=0)
    parser.add_argument("--saint-louis-count", type=int, default=0)
    parser.add_argument("--islands-only", action="store_true")
    return parser.parse_args(argv)


def load_upgrade():
    path = Path(__file__).resolve().parent / "upgrade_vicvs_osm_v21.py"
    specification = importlib.util.spec_from_file_location(
        "paris_v33_density_upgrade",
        path,
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def main():
    args = parse_args()
    upgrade = load_upgrade()
    build_scene, roman, medieval, house_upgrade = upgrade.load_project_modules()
    medieval_base = medieval.base
    upgrade.install_asymmetric_river(build_scene)
    streets, source_way_ids = upgrade.build_osm_streets(build_scene, "medieval")
    bridge_definitions, connector_streets = upgrade.load_bridge_definitions(
        build_scene,
        streets,
    )
    streets.extend(connector_streets)
    placements = {}
    placement_reports = {}
    if not args.islands_only:
        placements["main"], placement_reports["main"] = (
            upgrade.generate_aligned_placements(
                build_scene,
                streets,
                "medieval",
                "main",
                medieval_base.MAIN_BUILDING_COUNT,
                22100,
                density_extra=args.density_extra,
                fill_courtyards=True,
            )
        )
    for zone_index, (zone, target_count) in enumerate(
        (
            ("cite", args.cite_count),
            ("saint_louis", args.saint_louis_count),
        ),
        start=1,
    ):
        if target_count <= 0:
            continue
        placements[zone], placement_reports[zone] = (
            upgrade.generate_aligned_placements(
                build_scene,
                streets,
                "medieval",
                zone,
                target_count,
                22100 + zone_index,
                fill_courtyards=True,
            )
        )
    prototypes = [
        house_upgrade.import_prototype(path)
        for path in sorted(args.medieval_kit.resolve().glob("medieval_townhouse_*.glb"))
    ]
    if len(prototypes) != upgrade.MEDIEVAL_PROTOTYPE_COUNT:
        raise RuntimeError(
            f"Expected {upgrade.MEDIEVAL_PROTOTYPE_COUNT} medieval GLBs"
        )
    original_use_detail = house_upgrade.use_detail
    house_upgrade.use_detail = lambda _bs, _era, _placement: True
    building_reports = {}
    prefixes = upgrade.group_prefixes("medieval")
    timber_material = medieval_base.ensure_timber_material()
    for zone, zone_placements in placements.items():
        building_reports[zone] = house_upgrade.rebuild_group(
            build_scene,
            roman,
            medieval_base,
            "medieval",
            prefixes[zone],
            zone_placements,
            prototypes,
            [],
            timber_material=timber_material,
        )
    house_upgrade.use_detail = original_use_detail

    scene = bpy.context.scene
    scene[f"{args.version}_medieval_density"] = (
        "Dense OSM block interiors with roads, banks, and landmarks protected"
    )
    args.output_blend = args.output_blend.resolve()
    args.output_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output_blend), compress=True)
    report = {
        "version": args.version,
        "output_blend": str(args.output_blend),
        "source_way_count": len(source_way_ids),
        "bridge_count": len(bridge_definitions),
        "placements": placement_reports,
        "buildings": building_reports,
    }
    args.report = args.report.resolve()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
