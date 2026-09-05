import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


LANDMARKS = [
    ("Landmark_Notre_Dame_GLB", 980, 3.8),
    ("Landmark_Louvre_GLB", 1620, 6.2),
    ("Landmark_Arc_de_Triomphe_GLB", 2280, 2.4),
    ("Landmark_Palais_Garnier_GLB", 2430, 4.0),
    ("Landmark_Gare_du_Nord_GLB", 2960, 7.2),
    ("Landmark_Eiffel_Tower_GLB", 2980, 9.2),
]


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--close-only", action="store_true")
    return parser.parse_args(args)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_png(path, width, height):
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path.resolve())
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    camera = scene.camera
    camera_data = camera.data
    original_frame = scene.frame_current
    original_camera_type = camera_data.type
    original_resolution = (scene.render.resolution_x, scene.render.resolution_y)
    rendered = []

    if not args.close_only:
        for frame in (980, 1620, 2430, 2980, 3300):
            scene.frame_set(frame)
            camera_data.type = original_camera_type
            output = args.output_dir / f"global_{frame:04d}.png"
            render_png(output, 960, 540)
            rendered.append(str(output.resolve()))

    close_camera_data = bpy.data.cameras.new("Landmark_QA_Close_Camera")
    close_camera_data.type = "ORTHO"
    close_camera = bpy.data.objects.new("Landmark_QA_Close_Camera", close_camera_data)
    bpy.context.collection.objects.link(close_camera)
    scene.camera = close_camera
    for name, frame, scale in LANDMARKS:
        root = bpy.data.objects.get(name)
        if root is None:
            raise RuntimeError(f"Missing landmark root: {name}")
        scene.frame_set(frame)
        target = Vector((root.location.x, root.location.y, root.location.z + scale * 0.24))
        close_camera.location = (
            root.location.x - scale * 0.72,
            root.location.y - scale * 0.95,
            root.location.z + scale * 0.92,
        )
        look_at(close_camera, target)
        close_camera_data.ortho_scale = scale
        output = args.output_dir / f"close_{name}_{frame:04d}.png"
        render_png(output, 960, 720)
        rendered.append(str(output.resolve()))

    scene.frame_set(original_frame)
    scene.camera = camera
    camera_data.type = original_camera_type
    scene.render.resolution_x, scene.render.resolution_y = original_resolution
    bpy.data.objects.remove(close_camera, do_unlink=True)
    bpy.data.cameras.remove(close_camera_data, do_unlink=True)
    args.report.write_text(json.dumps({"renders": rendered}, indent=2), encoding="utf-8")
    print(json.dumps({"renders": rendered}, indent=2))


if __name__ == "__main__":
    main()
