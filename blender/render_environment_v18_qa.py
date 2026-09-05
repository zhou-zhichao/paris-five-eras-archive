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
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--samples", type=int, default=32)
    return parser.parse_args(argv)


def point_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, output_path):
    scene.frame_set(frame)
    scene.camera = camera
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def duplicate_camera(source, name):
    data = source.data.copy()
    data.animation_data_clear()
    camera = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(camera)
    camera.matrix_world = source.matrix_world.copy()
    return camera


def main():
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.use_motion_blur = False
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = args.samples

    source_camera = scene.camera
    outputs = []
    for frame, label in ((780, "roman_overview"), (1470, "medieval_overview")):
        output = output_dir / f"v18_{label}_f{frame:04d}.png"
        render(scene, source_camera, frame, output)
        outputs.append(str(output))

    island_camera = duplicate_camera(source_camera, "Environment_V18_Island_QA_Camera")
    island_camera.data.type = "ORTHO"
    island_camera.data.ortho_scale = 15.5
    output = output_dir / "v18_island_shore_close_f1470.png"
    render(scene, island_camera, 1470, output)
    outputs.append(str(output))

    riverbank_camera = duplicate_camera(source_camera, "Environment_V18_Riverbank_QA_Camera")
    riverbank_camera.data.type = "ORTHO"
    riverbank_camera.data.ortho_scale = 14.0
    riverbank_camera.location = (-15.5, -20.0, 17.5)
    point_camera(riverbank_camera, (-1.5, 0.8, -0.03))
    output = output_dir / "v18_shore_profile_close_f1470.png"
    render(scene, riverbank_camera, 1470, output)
    outputs.append(str(output))

    summary = {
        "blend": bpy.data.filepath,
        "resolution": [args.width, args.height],
        "samples": args.samples,
        "outputs": outputs,
    }
    print("ENVIRONMENT_V18_QA_BEGIN")
    print(json.dumps(summary, indent=2))
    print("ENVIRONMENT_V18_QA_END")


if __name__ == "__main__":
    main()
