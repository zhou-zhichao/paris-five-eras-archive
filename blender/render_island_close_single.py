import argparse
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1470)
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_motion_blur = False
    scene.eevee.taa_render_samples = 48

    source_camera = scene.camera
    camera_data = source_camera.data.copy()
    camera_data.animation_data_clear()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 14.5
    camera = bpy.data.objects.new("Island_Close_Single_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.matrix_world = source_camera.matrix_world.copy()
    scene.camera = camera
    scene.render.filepath = str(args.output)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
