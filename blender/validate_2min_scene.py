import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills" / "validation_2min"


def motion_category(name):
    if name.startswith(("Buildings_", "Island_Cite_", "Island_Saint_Louis_")):
        return "buildings"
    if name.startswith("Roads_"):
        return "roads"
    if name.startswith("Forest_Cleared_"):
        return "trees"
    if name.startswith("Bridge_"):
        return "bridges"
    if name.startswith("Modern_Railways"):
        return "railways"
    if name.startswith("Gare_"):
        return "stations"
    landmark_prefixes = (
        "Roman_",
        "Landmark_Notre_Dame",
        "Notre_Dame_",
        "Louvre_",
        "Arc_",
        "Eiffel_",
        "Defense_",
    )
    if name.startswith(landmark_prefixes):
        return "landmarks"
    return None


def animation_fcurves(animated_id):
    animation_data = animated_id.animation_data
    if animation_data is None or animation_data.action is None:
        return []
    action = animation_data.action
    slot = getattr(animation_data, "action_slot", None)
    if slot is not None and getattr(action, "layers", None):
        fcurves = []
        for layer in action.layers:
            for strip in layer.strips:
                channelbag = strip.channelbag(slot)
                if channelbag is not None:
                    fcurves.extend(channelbag.fcurves)
        return fcurves
    return list(action.fcurves)


def animation_intervals(animated_id):
    intervals = []
    for fcurve in animation_fcurves(animated_id):
        if fcurve.data_path == "hide_render":
            continue
        points = sorted(fcurve.keyframe_points, key=lambda point: point.co.x)
        for start, end in zip(points, points[1:]):
            if abs(start.co.y - end.co.y) < 1e-7:
                continue
            intervals.append((float(start.co.x), float(end.co.x)))
    return intervals


def audit_motion(scene):
    categories = {
        "buildings": [],
        "roads": [],
        "trees": [],
        "bridges": [],
        "railways": [],
        "stations": [],
        "landmarks": [],
    }
    for obj in scene.objects:
        category = motion_category(obj.name)
        if category is None:
            continue
        categories[category].extend(animation_intervals(obj))
        if obj.type == "MESH" and obj.data.shape_keys and obj.data.shape_keys.animation_data:
            categories[category].extend(animation_intervals(obj.data.shape_keys))

    seconds = []
    for second in range(0, math.ceil(scene.frame_end / scene.render.fps)):
        frame_start = second * scene.render.fps + 1
        frame_end = min(scene.frame_end, frame_start + scene.render.fps - 1)
        counts = {
            category: sum(
                interval_start <= frame_end and interval_end >= frame_start
                for interval_start, interval_end in intervals
            )
            for category, intervals in categories.items()
        }
        counts["total"] = sum(counts.values())
        seconds.append({"second": second, "frame_start": frame_start, "frame_end": frame_end, **counts})

    dead_seconds = [entry["second"] for entry in seconds[4:] if entry["total"] == 0]
    dead_runs = []
    for second in dead_seconds:
        if not dead_runs or second > dead_runs[-1][-1] + 1:
            dead_runs.append([second])
        else:
            dead_runs[-1].append(second)
    report = {
        "frame_end": scene.frame_end,
        "fps": scene.render.fps,
        "interval_counts": {category: len(intervals) for category, intervals in categories.items()},
        "dead_runs_after_focus": [
            {"start_second": run[0], "end_second": run[-1], "duration_seconds": len(run)}
            for run in dead_runs
        ],
        "seconds": seconds,
    }
    (OUTPUT_DIR / "motion_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("MOTION_AUDIT", json.dumps({key: report[key] for key in ("interval_counts", "dead_runs_after_focus")}))
    return report


def point_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_frame(scene, frame, filename, percentage=50, set_scene_frame=True):
    if set_scene_frame:
        scene.frame_set(frame)
    scene.render.resolution_percentage = percentage
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT_DIR / filename)
    bpy.ops.render.render(write_still=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    cathedral = bpy.data.objects["Notre_Dame_GLTF_Detailed"]
    scene.frame_set(1300)
    bpy.context.view_layer.update()
    world_corners = [cathedral.matrix_world @ Vector(corner) for corner in cathedral.bound_box]
    bounds_min = tuple(min(corner[axis] for corner in world_corners) for axis in range(3))
    bounds_max = tuple(max(corner[axis] for corner in world_corners) for axis in range(3))
    triangle_count = sum(len(polygon.vertices) - 2 for polygon in cathedral.data.polygons)
    print(
        "SCENE_AUDIT",
        f"objects={len(scene.objects)}",
        f"meshes={sum(obj.type == 'MESH' for obj in scene.objects)}",
        f"actions={len(bpy.data.actions)}",
        f"frame_end={scene.frame_end}",
    )
    print(
        "NOTRE_DAME_AUDIT",
        f"triangles={triangle_count}",
        f"bounds_min={tuple(round(value, 4) for value in bounds_min)}",
        f"bounds_max={tuple(round(value, 4) for value in bounds_max)}",
        f"materials={len(cathedral.data.materials)}",
    )
    audit_motion(scene)

    validation_frames = [
        (1, "01_opening_forest.png"),
        (90, "02_descent.png"),
        (120, "03_island_focus.png"),
        (180, "04_roman_roads_first.png"),
        (330, "05_roman_early_growth.png"),
        (600, "06_roman_late_growth.png"),
        (840, "07_medieval_handoff.png"),
        (1050, "08_medieval_growth.png"),
        (1575, "09_royal_growth.png"),
        (2250, "10_haussmann_growth.png"),
        (3000, "11_modern_rail_growth.png"),
        (3375, "12_modern_city_growth.png"),
        (3598, "13_modern_complete.png"),
    ]
    for frame, filename in validation_frames:
        render_frame(scene, frame, filename)

    camera = scene.camera
    original_location = camera.location.copy()
    original_rotation = camera.rotation_euler.copy()
    original_scale = camera.data.ortho_scale
    scene.frame_set(1300)
    camera.location = (-10.5, -13.5, 16.5)
    point_camera(camera, (0.15, 0.25, 0.45))
    camera.data.ortho_scale = 5.4
    render_frame(scene, 1300, "14_notre_dame_closeup.png", percentage=75, set_scene_frame=False)
    scene.frame_set(3300)
    camera.location = (-8.0, -10.0, 24.0)
    point_camera(camera, (6.5, 24.0, 0.2))
    camera.data.ortho_scale = 13.0
    render_frame(scene, 3300, "15_gare_du_nord_and_tracks.png", percentage=75, set_scene_frame=False)
    camera.location = original_location
    camera.rotation_euler = original_rotation
    camera.data.ortho_scale = original_scale


if __name__ == "__main__":
    main()
