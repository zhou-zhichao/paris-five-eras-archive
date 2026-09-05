import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    sun = bpy.data.objects.get("Sun")
    fill = bpy.data.objects.get("Sky_Fill")
    if sun is None or sun.type != "LIGHT":
        raise RuntimeError("Missing Sun light")
    if fill is None or fill.type != "LIGHT":
        raise RuntimeError("Missing Sky_Fill light")

    # Keep the directional modeling, but replace the near-black shadows with
    # broad skylight. This better matches the softly lit miniature reference.
    sun.data.energy = 2.75
    sun.data.angle = 0.12
    fill.data.energy = 680.0
    fill.data.shape = "DISK"
    fill.data.size = 35.0

    if scene.world is None or not scene.world.use_nodes:
        raise RuntimeError("Scene world must use nodes")
    background = next(
        (node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND"),
        None,
    )
    if background is None:
        raise RuntimeError("Missing World Background node")
    background.inputs["Strength"].default_value = 0.82

    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output),
        "sun_energy": sun.data.energy,
        "sun_angle": sun.data.angle,
        "fill_energy": fill.data.energy,
        "fill_size": fill.data.size,
        "world_strength": background.inputs["Strength"].default_value,
        "exposure": scene.view_settings.exposure,
        "look": scene.view_settings.look,
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
