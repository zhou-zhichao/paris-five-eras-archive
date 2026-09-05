import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def rounded(value):
    return round(float(value), 7)


def action_payload(action):
    if action is None:
        return []
    curves = []
    for curve in sorted(action.fcurves, key=lambda item: (item.data_path, item.array_index)):
        curves.append(
            {
                "data_path": curve.data_path,
                "array_index": curve.array_index,
                "keys": [
                    {
                        "co": [rounded(point.co.x), rounded(point.co.y)],
                        "handle_left": [
                            rounded(point.handle_left.x),
                            rounded(point.handle_left.y),
                        ],
                        "handle_right": [
                            rounded(point.handle_right.x),
                            rounded(point.handle_right.y),
                        ],
                        "interpolation": point.interpolation,
                        "easing": point.easing,
                    }
                    for point in curve.keyframe_points
                ],
            }
        )
    return curves


def digest(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main():
    args = parse_args()
    objects = {}
    for obj in sorted(bpy.data.objects, key=lambda item: item.name):
        if not obj.name.startswith("Roads_0_Chunk_"):
            continue
        object_action = obj.animation_data.action if obj.animation_data else None
        shape_keys = obj.data.shape_keys if obj.type == "MESH" else None
        shape_action = (
            shape_keys.animation_data.action
            if shape_keys and shape_keys.animation_data
            else None
        )
        objects[obj.name] = {
            "object_action_sha256": digest(action_payload(object_action)),
            "shape_action_sha256": digest(action_payload(shape_action)),
        }
    payload = {
        "blend": bpy.data.filepath,
        "object_count": len(objects),
        "overall_sha256": digest(objects),
        "objects": objects,
    }
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "objects"}, indent=2))


if __name__ == "__main__":
    main()
