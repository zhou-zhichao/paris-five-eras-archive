from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_DIR / "stills" / "validation_2min" / "17_notre_dame_detail_camera.png"


def main():
    scene = bpy.context.scene
    scene.frame_set(1500)
    camera_data = bpy.data.cameras.new("Notre_Dame_Detail_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.85
    camera = bpy.data.objects.new("Notre_Dame_Detail_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (-3.9, -5.1, 4.6)
    direction = Vector((0.15, 0.25, 0.55)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT_PATH)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
