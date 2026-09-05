import argparse
import json
from pathlib import Path

import bpy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    argv = []
    if "--" in __import__("sys").argv:
        argv = __import__("sys").argv[__import__("sys").argv.index("--") + 1 :]
    return parser.parse_args(argv)


def unpacked_external_images():
    items = []
    for image in bpy.data.images:
        if image.source != "FILE" or image.packed_file is not None:
            continue
        absolute_path = Path(bpy.path.abspath(image.filepath))
        items.append(
            {
                "name": image.name,
                "path": str(absolute_path),
                "exists": absolute_path.exists(),
            }
        )
    return items


def main():
    args = parse_args()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    before = unpacked_external_images()
    missing = [item for item in before if not item["exists"]]
    if missing:
        raise RuntimeError(f"Missing external images: {missing}")

    bpy.ops.file.pack_all()

    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 3600
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 18
    scene.render.film_transparent = False
    scene.render.use_motion_blur = True

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=True)

    after = unpacked_external_images()
    summary = {
        "blender_version": bpy.app.version_string,
        "output": str(output_path),
        "output_bytes": output_path.stat().st_size,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "fps": scene.render.fps,
        "resolution": [
            scene.render.resolution_x,
            scene.render.resolution_y,
            scene.render.resolution_percentage,
        ],
        "engine": scene.render.engine,
        "external_images_before_pack": before,
        "external_images_after_pack": after,
        "libraries": [library.filepath for library in bpy.data.libraries],
    }
    print("MINERVA_BLEND_SUMMARY=" + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
