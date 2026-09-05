import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy


PROJECT_DIR = Path(__file__).resolve().parents[1]
PLACEMENT_SCRIPT = Path(__file__).with_name("place_medieval_trellis_landmarks_v38.py")
FULL_STATE_FRAMES = {1: 1450, 2: 2100}
CLEARANCE = 0.180


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def load_placement_module():
    spec = importlib.util.spec_from_file_location("trellis_placement_v43", PLACEMENT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize(entries):
    return {
        "objects_modified": len(entries),
        "buildings_removed": sum(entry["removed_components"] for entry in entries),
        "faces_removed": sum(entry["removed_faces"] for entry in entries),
        "vertices_removed": sum(entry["removed_vertices"] for entry in entries),
    }


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    placement = load_placement_module()

    landmark_spec = next(
        item
        for item in placement.LANDMARK_SPECS
        if item["name"] == "Landmark_Saint_Germain_des_Pres_Trellis"
    ).copy()
    landmark_spec["clearance"] = CLEARANCE

    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output),
        "landmark": landmark_spec["name"],
        "clearance": CLEARANCE,
        "eras": {},
    }
    scene = bpy.context.scene
    for era, frame in FULL_STATE_FRAMES.items():
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        building_entries = []
        for obj in list(bpy.data.objects):
            if obj.type != "MESH" or not obj.name.startswith(placement.BUILDING_PREFIXES[era]):
                continue
            result = placement.clear_procedural_buildings_from_object(obj, [landmark_spec])
            if result is not None:
                building_entries.append(result)

        forest_entries = []
        forest_prefix = f"Forest_Cleared_{era}_Chunk_"
        for obj in list(bpy.data.objects):
            if obj.type != "MESH" or not obj.name.startswith(forest_prefix):
                continue
            result = placement.clear_spatial_clusters_from_object(
                obj,
                [landmark_spec],
                extra_margin=0.02,
            )
            if result is not None:
                forest_entries.append(result)

        report["eras"][str(era)] = {
            "buildings": summarize(building_entries),
            "forest": summarize(forest_entries),
            "building_details": building_entries,
            "forest_details": forest_entries,
        }

    scene.frame_set(1450)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
