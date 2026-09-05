from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills" / "station_closeups_v2"


STATIONS = [
    ("Gare_du_Nord", (6.5, 24.0), (7.4, 31.0)),
    ("Gare_Saint_Lazare", (-18.0, 18.0), (-26.0, 26.0)),
    ("Gare_de_Lyon", (14.0, -4.0), (23.0, -13.0)),
    ("Gare_Montparnasse", (-10.0, -16.0), (-18.0, -27.0)),
]


def point_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_shot(scene, camera, filename, location, target, ortho_scale):
    camera.location = location
    point_camera(camera, target)
    camera.data.ortho_scale = ortho_scale
    scene.render.filepath = str(OUTPUT_DIR / filename)
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("RENDERED", filename)


def station_camera_pose(location, next_track_point):
    station = Vector((location[0], location[1]))
    next_point = Vector((next_track_point[0], next_track_point[1]))
    along = (next_point - station).normalized()
    across = Vector((-along.y, along.x))
    focus = station + along * 2.35
    camera_xy = focus - along * 6.6 + across * 5.2
    camera_location = (camera_xy.x, camera_xy.y, 8.2)
    target = (focus.x, focus.y, 0.32)
    return camera_location, target


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(3598)
    camera_data = bpy.data.cameras.new("Station_Closeup_Camera_Data")
    camera_data.type = "ORTHO"
    camera_data.clip_start = 0.05
    camera_data.clip_end = 1000.0
    camera = bpy.data.objects.new("Station_Closeup_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"

    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 48
    scene.render.use_motion_blur = False
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    render_shot(
        scene,
        camera,
        "01_rail_network_overview.png",
        (-42.0, -54.0, 66.0),
        (0.0, 1.5, 0.0),
        62.0,
    )

    for index, (name, location, next_track_point) in enumerate(STATIONS, start=2):
        camera_location, target = station_camera_pose(location, next_track_point)
        render_shot(
            scene,
            camera,
            f"{index:02d}_{name.lower()}_closeup.png",
            camera_location,
            target,
            8.6,
        )

    north_start = Vector((7.4, 31.0))
    north_end = Vector((10.5, 42.0))
    along = (north_end - north_start).normalized()
    across = Vector((-along.y, along.x))
    focus = north_start.lerp(north_end, 0.42)
    camera_xy = focus - along * 5.5 + across * 4.8
    render_shot(
        scene,
        camera,
        "06_northern_tracks_detail.png",
        (camera_xy.x, camera_xy.y, 7.0),
        (focus.x, focus.y, 0.15),
        7.0,
    )


if __name__ == "__main__":
    main()
