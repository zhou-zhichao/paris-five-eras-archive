import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def object_summary(obj):
    return {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "location": [round(float(value), 6) for value in obj.location],
        "dimensions": [round(float(value), 6) for value in obj.dimensions],
        "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
        "polygons": len(obj.data.polygons) if obj.type == "MESH" else None,
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    }


def chunk_stats(prefix):
    objects = [obj for obj in bpy.data.objects if obj.name.startswith(prefix)]
    vertices = [len(obj.data.vertices) for obj in objects if obj.type == "MESH"]
    polygons = [len(obj.data.polygons) for obj in objects if obj.type == "MESH"]
    return {
        "count": len(objects),
        "vertices_total": sum(vertices),
        "vertices_min": min(vertices) if vertices else 0,
        "vertices_max": max(vertices) if vertices else 0,
        "vertices_mean": sum(vertices) / len(vertices) if vertices else 0.0,
        "polygons_total": sum(polygons),
        "polygons_min": min(polygons) if polygons else 0,
        "polygons_max": max(polygons) if polygons else 0,
        "polygons_mean": sum(polygons) / len(polygons) if polygons else 0.0,
        "first_materials": (
            [slot.material.name if slot.material else None for slot in objects[0].material_slots]
            if objects
            else []
        ),
    }


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.frame_set(1470)
    bridge_objects = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith("Bridge_")),
        key=lambda obj: obj.name,
    )
    wall_objects = sorted(
        (
            obj
            for obj in bpy.data.objects
            if any(token in obj.name.lower() for token in ("wall", "gate", "rampart"))
        ),
        key=lambda obj: obj.name,
    )
    report = {
        "blend": bpy.data.filepath,
        "bridge_objects": [object_summary(obj) for obj in bridge_objects],
        "wall_objects": [object_summary(obj) for obj in wall_objects],
        "road_chunks": {
            "roman": chunk_stats("Roads_0_Chunk_"),
            "medieval": chunk_stats("Roads_1_Chunk_"),
        },
        "building_chunks": {
            "roman_main": chunk_stats("Buildings_Roman_State_Chunk_"),
            "roman_cite": chunk_stats("Island_Cite_0_State_Chunk_"),
            "roman_saint_louis": chunk_stats("Island_Saint_Louis_0_State_Chunk_"),
            "medieval_main": chunk_stats("Buildings_Medieval_State_Chunk_"),
            "medieval_cite": chunk_stats("Island_Cite_1_State_Chunk_"),
            "medieval_saint_louis": chunk_stats("Island_Saint_Louis_1_State_Chunk_"),
        },
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("ROADS_HOUSES_V19_DIAGNOSTIC_BEGIN")
    print(json.dumps(report, indent=2))
    print("ROADS_HOUSES_V19_DIAGNOSTIC_END")


if __name__ == "__main__":
    main()
