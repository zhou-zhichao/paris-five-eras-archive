import time
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills" / "validation_2min"


def point_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def timed_render(scene, cathedral, visible, filename):
    cathedral.hide_render = not visible
    scene.render.filepath = str(OUTPUT_DIR / filename)
    started = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    return time.perf_counter() - started


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1500)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    cathedral = bpy.data.objects["Notre_Dame_GLTF_Detailed"]

    timed_render(scene, cathedral, False, "12_benchmark_nd_off_warmup.png")
    timed_render(scene, cathedral, True, "13_benchmark_nd_on_warmup.png")
    off_seconds = timed_render(scene, cathedral, False, "14_benchmark_nd_off.png")
    on_seconds = timed_render(scene, cathedral, True, "15_benchmark_nd_on.png")
    print(
        "NOTRE_DAME_BENCHMARK",
        f"off_seconds={off_seconds:.3f}",
        f"on_seconds={on_seconds:.3f}",
        f"delta_seconds={on_seconds - off_seconds:.3f}",
        f"delta_percent={(on_seconds / off_seconds - 1.0) * 100.0:.2f}",
    )

    camera = scene.camera
    camera.location = (-4.8, -6.5, 6.4)
    point_camera(camera, (0.15, 0.25, 0.55))
    camera.data.ortho_scale = 3.6
    scene.render.filepath = str(OUTPUT_DIR / "16_notre_dame_true_closeup.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
