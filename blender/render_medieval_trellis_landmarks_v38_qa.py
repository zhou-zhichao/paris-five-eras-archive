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
    parser.add_argument("--bridge-temple", action="store_true")
    parser.add_argument("--bridge-only", action="store_true")
    parser.add_argument("--saint-germain-only", action="store_true")
    parser.add_argument("--temple-context-only", action="store_true")
    parser.add_argument("--overview-only", action="store_true")
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
    scene.render.image_settings.color_mode = "RGB"
    scene.render.use_motion_blur = False
    scene.render.film_transparent = False

    cameras = {
        "overview": make_camera(
            scene,
            "V38_QA_Overview",
            (18.0, -26.0, 31.0),
            (-2.0, 6.0, 0.15),
            29.0,
        ),
        "cite": make_camera(
            scene,
            "V38_QA_Cite",
            (2.5, -5.7, 6.4),
            (-2.65, 1.75, 0.15),
            5.6,
        ),
        "bridge": make_camera(
            scene,
            "V38_QA_Bridge",
            (0.6, -3.8, 3.4),
            (-2.23, 0.33, 0.08),
            2.35,
        ),
        "bridge_overhead": make_camera(
            scene,
            "V42_QA_Bridge_Overhead",
            (-2.256, 0.120, 5.0),
            (-2.256, 0.120, 0.0),
            1.75,
        ),
        "bridge_island": make_camera(
            scene,
            "V42_QA_Bridge_Island",
            (-4.15, 2.55, 2.5),
            (-2.20, 0.36, 0.02),
            1.90,
        ),
        "chapelle": make_camera(
            scene,
            "V38_QA_Chapelle",
            (-0.9, -1.4, 3.5),
            (-3.59, 2.70, 0.25),
            2.35,
        ),
        "saint_germain": make_camera(
            scene,
            "V38_QA_Saint_Germain",
            (-8.3, -4.6, 4.7),
            (-12.15, 0.95, 0.25),
            3.55,
        ),
        "saint_germain_overhead": make_camera(
            scene,
            "V43_QA_Saint_Germain_Overhead",
            (-12.15, 0.95, 5.5),
            (-12.15, 0.95, 0.0),
            3.10,
        ),
        "temple": make_camera(
            scene,
            "V38_QA_Temple",
            (11.8, 7.0, 4.5),
            (8.20, 12.45, 0.28),
            3.35,
        ),
        "temple_overhead": make_camera(
            scene,
            "V44_QA_Temple_Overhead",
            (8.20, 12.45, 6.5),
            (8.20, 12.45, 0.0),
            3.25,
        ),
        "temple_city_context": make_camera(
            scene,
            "V44_QA_Temple_City_Context",
            (15.5, 0.5, 10.0),
            (5.0, 8.5, 0.10),
            10.5,
        ),
    }
    shots = (
        ("medieval_overview_f1450.png", "overview", 1450),
        ("medieval_cite_f1450.png", "cite", 1450),
        ("petit_pont_chatelet_f1450.png", "bridge", 1450),
        ("sainte_chapelle_f1450.png", "chapelle", 1450),
        ("saint_germain_des_pres_f1450.png", "saint_germain", 1450),
        ("tour_du_temple_f1450.png", "temple", 1450),
    )
    if args.quick:
        shots = (
            ("petit_pont_chatelet_f1450.png", "bridge", 1450),
            ("sainte_chapelle_f1450.png", "chapelle", 1450),
            ("saint_germain_des_pres_f1450.png", "saint_germain", 1450),
            ("tour_du_temple_f1450.png", "temple", 1450),
        )
    if args.bridge_temple:
        shots = (
            ("petit_pont_chatelet_f1450.png", "bridge", 1450),
            ("tour_du_temple_f1450.png", "temple", 1450),
        )
    if args.bridge_only:
        shots = (
            ("petit_pont_chatelet_oblique_f1450.png", "bridge", 1450),
            ("petit_pont_chatelet_overhead_f1450.png", "bridge_overhead", 1450),
            ("petit_pont_chatelet_island_f1450.png", "bridge_island", 1450),
        )
    if args.saint_germain_only:
        shots = (
            ("saint_germain_des_pres_oblique_f1450.png", "saint_germain", 1450),
            ("saint_germain_des_pres_overhead_f1450.png", "saint_germain_overhead", 1450),
        )
    if args.temple_context_only:
        shots = (
            ("tour_du_temple_enclosure_oblique_f1450.png", "temple", 1450),
            ("tour_du_temple_enclosure_overhead_f1450.png", "temple_overhead", 1450),
            ("tour_du_temple_city_context_f1450.png", "temple_city_context", 1450),
        )
    if args.overview_only:
        shots = (("medieval_overview_f1450.png", "overview", 1450),)
    outputs = [
        render(scene, cameras[camera_name], frame, output_dir / filename)
        for filename, camera_name, frame in shots
    ]
    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
