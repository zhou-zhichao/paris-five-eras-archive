import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frame", type=int, default=780)
    return parser.parse_args(argv)


def point_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, output_path):
    scene.camera = camera
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(args.frame)
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 64

    source_camera = scene.camera
    source_camera.data.lens = 50.0
    render(
        scene,
        source_camera,
        args.output_dir / f"roman_v15_overview_f{args.frame:04d}.png",
    )

    close_data = source_camera.data.copy()
    close_data.animation_data_clear()
    close_data.type = "ORTHO"
    close_data.ortho_scale = 18.5
    close_camera = bpy.data.objects.new("Roman_QA_Close_Camera", close_data)
    scene.collection.objects.link(close_camera)
    close_camera.matrix_world = source_camera.matrix_world.copy()
    render(
        scene,
        close_camera,
        args.output_dir / f"roman_v15_close_f{args.frame:04d}.png",
    )

    bank_data = source_camera.data.copy()
    bank_data.animation_data_clear()
    bank_data.type = "ORTHO"
    bank_data.ortho_scale = 19.5
    bank_camera = bpy.data.objects.new("Roman_QA_Riverbank_Camera", bank_data)
    scene.collection.objects.link(bank_camera)
    bank_camera.location = (-24.0, -29.0, 24.0)
    point_camera(bank_camera, (-1.5, 0.8, -0.03))
    render(
        scene,
        bank_camera,
        args.output_dir / f"roman_v15_riverbank_f{args.frame:04d}.png",
    )

    summary = {
        "frame": args.frame,
        "outputs": [
            str(args.output_dir / f"roman_v15_overview_f{args.frame:04d}.png"),
            str(args.output_dir / f"roman_v15_close_f{args.frame:04d}.png"),
            str(args.output_dir / f"roman_v15_riverbank_f{args.frame:04d}.png"),
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
