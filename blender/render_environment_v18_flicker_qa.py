import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--samples", type=int, default=16)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.use_motion_blur = False
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = args.samples

    outputs = []
    for frame in range(args.start, args.end + 1):
        scene.frame_set(frame)
        output = output_dir / f"f{frame:04d}.png"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        outputs.append(str(output))

    report = {
        "blend": bpy.data.filepath,
        "frame_range": [args.start, args.end],
        "frame_count": len(outputs),
        "resolution": [args.width, args.height],
        "samples": args.samples,
        "first_output": outputs[0],
        "last_output": outputs[-1],
    }
    print("ENVIRONMENT_V18_FLICKER_QA_BEGIN")
    print(json.dumps(report, indent=2))
    print("ENVIRONMENT_V18_FLICKER_QA_END")


if __name__ == "__main__":
    main()
