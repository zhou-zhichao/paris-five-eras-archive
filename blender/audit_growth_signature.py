import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy


GROWTH_PATTERN = re.compile(
    r"^(Buildings_(Roman|Medieval|1700|1850|Modern)_State|"
    r"Island_(Cite|Saint_Louis)_[0-4]_State)_Chunk_"
)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def rounded(value):
    return round(float(value), 7)


def object_animation_payload(obj):
    animation_data = obj.animation_data
    action = animation_data.action if animation_data else None
    if action is None:
        return []
    curves = []
    for curve in sorted(action.fcurves, key=lambda item: (item.data_path, item.array_index)):
        keys = []
        for point in curve.keyframe_points:
            keys.append(
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
            )
        curves.append(
            {
                "data_path": curve.data_path,
                "array_index": curve.array_index,
                "keys": keys,
            }
        )
    return curves


def digest(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    per_object = {}
    for obj in sorted(bpy.data.objects, key=lambda item: item.name):
        if not GROWTH_PATTERN.match(obj.name):
            continue
        payload = object_animation_payload(obj)
        per_object[obj.name] = {
            "action": obj.animation_data.action.name if obj.animation_data and obj.animation_data.action else None,
            "fcurve_count": len(payload),
            "keyframe_count": sum(len(curve["keys"]) for curve in payload),
            "sha256": digest(payload),
        }

    summary = {
        "blend": bpy.data.filepath,
        "object_count": len(per_object),
        "overall_sha256": digest(per_object),
        "objects": per_object,
    }
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "objects"}, indent=2))


if __name__ == "__main__":
    main()
