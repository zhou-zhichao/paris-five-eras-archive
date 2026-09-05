import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT_NAME = "Landmark_Tour_du_Temple_Trellis"
MODEL_NAME = f"{ROOT_NAME}_Model"
CONTEXT_NAME = "Temple_Enclos_v44"
TARGET_DIMENSIONS = Vector((0.42, 0.48, 0.58))


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def descendants(root):
    result = []
    stack = list(root.children)
    while stack:
        child = stack.pop()
        result.append(child)
        stack.extend(child.children)
    return result


def effectively_hidden(obj):
    current = obj
    while current is not None:
        if current.hide_render:
            return True
        current = current.parent
    return False


def dimensions_in_space(model_root, space_root):
    meshes = [obj for obj in descendants(model_root) if obj.type == "MESH"]
    inverse_space = space_root.matrix_world.inverted()
    points = [
        inverse_space @ (obj.matrix_world @ Vector(corner))
        for obj in meshes
        for corner in obj.bound_box
    ]
    minimum = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    maximum = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return maximum - minimum


def main():
    args = parse_args()
    args.report = args.report.resolve()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    root = bpy.data.objects.get(ROOT_NAME)
    model = bpy.data.objects.get(MODEL_NAME)
    context = bpy.data.objects.get(CONTEXT_NAME)
    if root is None or model is None or context is None:
        raise RuntimeError("Temple landmark context is incomplete")

    states = {}
    for frame in (1049, 1050, 1078, 1450, 2204):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        states[str(frame)] = {
            "root_hidden": effectively_hidden(root),
            "context_hidden": effectively_hidden(context),
            "root_scale": list(root.scale),
        }

    scene.frame_set(1450)
    bpy.context.view_layer.update()
    dimensions = dimensions_in_space(model, root)
    context_children = descendants(context)
    checks = [
        ("context hidden before landmark birth", states["1049"]["context_hidden"]),
        ("context visible at landmark birth", not states["1050"]["context_hidden"]),
        ("landmark starts collapsed", states["1050"]["root_scale"][2] <= 0.02),
        ("landmark and context fully grown", states["1078"]["root_scale"][2] >= 0.99),
        ("context visible in medieval state", not states["1450"]["context_hidden"]),
        ("context retires with landmark", states["2204"]["context_hidden"]),
        ("keep width matches corrected scale", abs(dimensions.x - TARGET_DIMENSIONS.x) <= 0.015),
        ("keep depth matches corrected scale", abs(dimensions.y - TARGET_DIMENSIONS.y) <= 0.015),
        ("keep height matches corrected scale", abs(dimensions.z - TARGET_DIMENSIONS.z) <= 0.015),
        ("precinct has contextual geometry", len(context_children) >= 60),
        ("round church exists", bpy.data.objects.get("Temple_Round_Church_v44") is not None),
        ("west road gate exists", bpy.data.objects.get("Temple_Enclos_West_Wall_v44_Gate_Tower_0") is not None),
        ("east road gate exists", bpy.data.objects.get("Temple_Enclos_East_Wall_v44_Gate_Tower_0") is not None),
    ]
    failures = [name for name, passed in checks if not passed]
    report = {
        "blend": bpy.data.filepath,
        "checks": [{"name": name, "passed": bool(passed)} for name, passed in checks],
        "failure_count": len(failures),
        "failures": failures,
        "keep_dimensions": list(dimensions),
        "context_descendant_count": len(context_children),
        "states": states,
    }
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise RuntimeError("Temple context audit failed: " + "; ".join(failures))


if __name__ == "__main__":
    main()
