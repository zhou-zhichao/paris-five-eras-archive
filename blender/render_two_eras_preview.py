import argparse
import json
import sys
import time
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1499)
    parser.add_argument("--samples", type=int, default=8)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_start = args.start
    scene.frame_end = args.end
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.use_motion_blur = False
    scene.render.film_transparent = False
    scene.render.filepath = str(output)
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = args.samples

    started = time.perf_counter()
    bpy.ops.render.render(animation=True)
    elapsed = time.perf_counter() - started
    print(
        "RENDER_SUMMARY "
        + json.dumps(
            {
                "output": str(output),
                "start": args.start,
                "end": args.end,
                "frames": args.end - args.start + 1,
                "fps": scene.render.fps,
                "samples": args.samples,
                "elapsed_seconds": round(elapsed, 3),
            }
        )
    )


if __name__ == "__main__":
    main()
