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
    return parser.parse_args(argv)


def load_upgrade():
    path = Path(__file__).resolve().parent / "upgrade_vicvs_osm_v21.py"
    specification = importlib.util.spec_from_file_location(
        "paris_v32_density_upgrade",
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
    placements, placement_report = upgrade.generate_aligned_placements(
        build_scene,
        streets,
        "medieval",
        "main",
        medieval_base.MAIN_BUILDING_COUNT,
        22100,
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
    building_report = house_upgrade.rebuild_group(
        build_scene,
        roman,
        medieval_base,
        "medieval",
        upgrade.group_prefixes("medieval")["main"],
        placements,
        prototypes,
        [],
        timber_material=medieval_base.ensure_timber_material(),
    )
    house_upgrade.use_detail = original_use_detail

    scene = bpy.context.scene
    scene["v32_medieval_density"] = (
        "Closed-block infill plus open-block deep frontage bands"
    )
    args.output_blend = args.output_blend.resolve()
    args.output_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output_blend), compress=True)
    report = {
        "version": "v32",
        "output_blend": str(args.output_blend),
        "source_way_count": len(source_way_ids),
        "bridge_count": len(bridge_definitions),
        "placements": placement_report,
        "buildings": building_report,
    }
    args.report = args.report.resolve()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
