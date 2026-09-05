import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


SHOTS = [
    {
        "name": "water_low_0980",
        "frame": 980,
        "target": (0.0, 0.0, 0.35),
        "offset": (-17.0, -24.0, 7.0),
        "scale": 22.0,
    },
    {
        "name": "water_island_0980",
        "frame": 980,
        "target": (0.0, 0.0, 0.3),
        "offset": (-17.0, -24.0, 18.0),
        "scale": 26.0,
    },
    {
        "name": "water_louvre_1620",
        "frame": 1620,
        "target": (-4.5, 5.0, 0.35),
        "offset": (-19.0, -27.0, 14.0),
        "scale": 23.0,
    },
    {
        "name": "eiffel_close_2980",
        "frame": 2980,
        "target": (-40.6, 6.0, 3.25),
        "offset": (-8.5, -12.0, 8.0),
        "scale": 10.2,
    },
]


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    args.output_dir = args.output_dir.resolve()
    args.report = args.report.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    original_camera = scene.camera
    original_frame = scene.frame_current
    original_resolution = (scene.render.resolution_x, scene.render.resolution_y)
    original_samples = scene.eevee.taa_render_samples

    camera_data = bpy.data.cameras.new("Water_Eiffel_QA_Camera_Data")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("Water_Eiffel_QA_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.eevee.taa_render_samples = 32

    outputs = []
    for shot in SHOTS:
        scene.frame_set(shot["frame"])
        target = Vector(shot["target"])
        camera.location = target + Vector(shot["offset"])
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera_data.ortho_scale = shot["scale"]
        output = args.output_dir / f'{shot["name"]}.png'
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        outputs.append(str(output))

    scene.camera = original_camera
    scene.frame_set(original_frame)
    scene.render.resolution_x, scene.render.resolution_y = original_resolution
    scene.eevee.taa_render_samples = original_samples
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data, do_unlink=True)
    args.report.write_text(json.dumps({"outputs": outputs}, indent=2), encoding="utf-8")
    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
