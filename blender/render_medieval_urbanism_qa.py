import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def render(scene, output_path):
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.use_motion_blur = False
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 48

    outputs = []
    source_camera = scene.camera
    for frame in (810, 930, 1110, 1290, 1470):
        scene.frame_set(frame)
        output = output_dir / f"roman_medieval_growth_f{frame:04d}.png"
        render(scene, output)
        outputs.append(str(output))

    scene.frame_set(1470)
    close_data = source_camera.data.copy()
    close_data.animation_data_clear()
    close_data.type = "ORTHO"
    close_data.ortho_scale = 26.0
    close_camera = bpy.data.objects.new("Medieval_QA_Close_Camera", close_data)
    scene.collection.objects.link(close_camera)
    close_camera.matrix_world = source_camera.matrix_world.copy()
    scene.camera = close_camera
    output = output_dir / "medieval_v16_city_close_f1470.png"
    render(scene, output)
    outputs.append(str(output))

    island_data = source_camera.data.copy()
    island_data.animation_data_clear()
    island_data.type = "ORTHO"
    island_data.ortho_scale = 14.5
    island_camera = bpy.data.objects.new("Medieval_QA_Island_Camera", island_data)
    scene.collection.objects.link(island_camera)
    island_camera.matrix_world = source_camera.matrix_world.copy()
    scene.camera = island_camera
    output = output_dir / "medieval_v16_island_close_f1470.png"
    render(scene, output)
    outputs.append(str(output))

    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
