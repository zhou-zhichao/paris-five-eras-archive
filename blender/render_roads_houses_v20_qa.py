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
    return parser.parse_args(argv)


def point_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def make_camera(scene, name, location, target, ortho_scale):
    camera_data = bpy.data.cameras.new(f"{name}_Data")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = ortho_scale
    camera = bpy.data.objects.new(name, camera_data)
    scene.collection.objects.link(camera)
    camera.location = location
    point_camera(camera, target)
    return camera


def render(scene, camera, frame, path):
    scene.frame_set(frame)
    scene.camera = camera
    scene.render.filepath = str(path.resolve())
    bpy.ops.render.render(write_still=True)
    return str(path.resolve())


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

    timeline_camera = scene.camera
    island_camera = make_camera(
        scene,
        "Road_House_QA_Island",
        (-14.0, -17.0, 13.5),
        (-2.4, 1.8, 0.12),
        13.0,
    )
    south_camera = make_camera(
        scene,
        "Road_House_QA_South",
        (-8.0, -13.5, 7.2),
        (-2.2, -4.0, 0.18),
        5.4,
    )
    gate_camera = make_camera(
        scene,
        "Road_House_QA_Gate",
        (-10.0, -8.0, 6.5),
        (-5.0, 3.0, 0.2),
        4.8,
    )

    outputs = []
    for era, frame in (("roman", 700), ("medieval", 1450)):
        outputs.append(
            render(
                scene,
                timeline_camera,
                frame,
                output_dir / f"{era}_timeline_f{frame:04d}.png",
            )
        )
        outputs.append(
            render(
                scene,
                island_camera,
                frame,
                output_dir / f"{era}_island_f{frame:04d}.png",
            )
        )
        outputs.append(
            render(
                scene,
                south_camera,
                frame,
                output_dir / f"{era}_houses_f{frame:04d}.png",
            )
        )
    outputs.append(
        render(
            scene,
            gate_camera,
            1450,
            output_dir / "medieval_gate_f1450.png",
        )
    )
    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
