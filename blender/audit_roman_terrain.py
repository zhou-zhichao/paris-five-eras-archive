import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def object_summary(obj):
    world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "name": obj.name,
        "type": obj.type,
        "location": [round(value, 6) for value in obj.location],
        "bounds_z": [
            round(min(point.z for point in world_corners), 6),
            round(max(point.z for point in world_corners), 6),
        ],
        "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
        "faces": len(obj.data.polygons) if obj.type == "MESH" else None,
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "action": (
            obj.animation_data.action.name
            if obj.animation_data and obj.animation_data.action
            else None
        ),
    }


def main():
    args = parse_args()
    prefixes = (
        "Buildings_Roman_State_Chunk_",
        "Island_Cite_0_State_Chunk_",
        "Island_Saint_Louis_0_State_Chunk_",
    )
    terrain_names = (
        "Land",
        "Seine",
        "Seine_Riverbank",
        "Ile_de_la_Cite",
        "Ile_de_la_Cite_Margin",
        "Ile_Saint_Louis",
        "Ile_Saint_Louis_Margin",
        "Seine_Planar_Reflection_Probe",
    )
    roman_objects = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith(prefixes)),
        key=lambda obj: obj.name,
    )
    roman_roads = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith("Roads_0_Chunk_")),
        key=lambda obj: obj.name,
    )
    payload = {
        "blend": bpy.data.filepath,
        "terrain": {
            name: object_summary(bpy.data.objects[name])
            for name in terrain_names
            if name in bpy.data.objects
        },
        "roman": {
            "object_count": len(roman_objects),
            "group_counts": {
                prefix: sum(obj.name.startswith(prefix) for obj in roman_objects)
                for prefix in prefixes
            },
            "vertex_count": sum(
                len(obj.data.vertices) for obj in roman_objects if obj.type == "MESH"
            ),
            "face_count": sum(
                len(obj.data.polygons) for obj in roman_objects if obj.type == "MESH"
            ),
            "sample_objects": [object_summary(obj) for obj in roman_objects[:6]],
        },
        "roman_roads": {
            "object_count": len(roman_roads),
            "vertex_count": sum(
                len(obj.data.vertices) for obj in roman_roads if obj.type == "MESH"
            ),
            "shape_key_actions": sum(
                bool(
                    obj.data.shape_keys
                    and obj.data.shape_keys.animation_data
                    and obj.data.shape_keys.animation_data.action
                )
                for obj in roman_roads
            ),
            "sample_objects": [object_summary(obj) for obj in roman_roads[:3]],
        },
    }
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
