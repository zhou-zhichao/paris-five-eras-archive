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
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--overview-only", action="store_true")
    parser.add_argument("--medieval-only", action="store_true")
    parser.add_argument("--houses-only", action="store_true")
    parser.add_argument("--animation-frame", type=int)
    return parser.parse_args(argv)


def point_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def make_camera(scene, name, location, target, ortho_scale):
    data = bpy.data.cameras.new(f"{name}_Data")
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    camera = bpy.data.objects.new(name, data)
    scene.collection.objects.link(camera)
    camera.location = location
    point_camera(camera, target)
    return camera


def render(scene, camera, frame, output_path):
    scene.frame_set(frame)
    scene.camera = camera
    scene.render.filepath = str(output_path.resolve())
    bpy.ops.render.render(write_still=True)
    return str(output_path.resolve())


def main():
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.use_motion_blur = False
    scene.render.film_transparent = False
    if args.animation_frame is not None:
        scene.eevee.taa_render_samples = 16
        output = output_dir / f"animation_frame_f{args.animation_frame:04d}.png"
        render(scene, scene.camera, args.animation_frame, output)
        print(json.dumps({"outputs": [str(output.resolve())]}, indent=2))
        return

    cameras = {
        "overview": make_camera(
            scene,
            "V22_QA_Overview",
            (-38.0, -49.0, 67.0),
            (-0.5, 0.5, 0.0),
            27.0,
        ),
        "island": make_camera(
            scene,
            "V22_QA_Island",
            (-13.5, -16.5, 13.5),
            (-2.4, 1.8, 0.10),
            12.2,
        ),
        "houses": make_camera(
            scene,
            "V22_QA_Houses",
            (-7.5, -9.5, 5.6),
            (-3.7, -3.0, 0.22),
            4.2,
        ),
        "north_bridge": make_camera(
            scene,
            "V22_QA_North_Bridge",
            (-5.4, 0.7, 3.1),
            (-2.22, 4.12, 0.04),
            2.75,
        ),
        "south_bridge": make_camera(
            scene,
            "V22_QA_South_Bridge",
            (-5.0, -2.5, 2.85),
            (-2.16, 0.38, 0.04),
            2.45,
        ),
    }
    shots = (
        ("roman_overview_f0700.png", "overview", 700),
        ("roman_island_f0700.png", "island", 700),
        ("roman_houses_f0700.png", "houses", 700),
        ("roman_north_bridge_f0700.png", "north_bridge", 700),
        ("roman_south_bridge_f0700.png", "south_bridge", 700),
        ("medieval_island_f1450.png", "island", 1450),
        ("medieval_north_bridge_f1450.png", "north_bridge", 1450),
    )
    if args.quick:
        shots = (
            ("roman_overview_f0700.png", "overview", 700),
            ("roman_north_bridge_f0700.png", "north_bridge", 700),
            ("roman_south_bridge_f0700.png", "south_bridge", 700),
            ("medieval_island_f1450.png", "island", 1450),
        )
    if args.overview_only:
        shots = (("roman_overview_f0700.png", "overview", 700),)
    if args.medieval_only:
        shots = (("medieval_island_f1450.png", "island", 1450),)
    if args.houses_only:
        shots = (("medieval_houses_f1450.png", "houses", 1450),)
    outputs = [
        render(scene, cameras[camera_name], frame, output_dir / filename)
        for filename, camera_name, frame in shots
    ]
    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
