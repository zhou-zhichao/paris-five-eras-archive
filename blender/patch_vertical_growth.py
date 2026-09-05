from pathlib import Path

import bpy


BLEND_PATH = Path(__file__).with_name("paris_5_eras.blend")

for obj in bpy.data.objects:
    if not obj.animation_data or not obj.animation_data.action:
        continue
    action = obj.animation_data.action
    scale_z = next(
        (
            curve
            for curve in action.fcurves
            if curve.data_path == "scale" and curve.array_index == 2
        ),
        None,
    )
    if scale_z is None:
        continue
    points = sorted(
        ((point.co.x, point.co.y) for point in scale_z.keyframe_points),
        key=lambda item: item[0],
    )
    for (start_frame, start_value), (end_frame, end_value) in zip(points, points[1:]):
        if start_value < 0.1 and end_value > 0.9:
            obj.location.z = -0.2
            obj.keyframe_insert(data_path="location", frame=start_frame)
            obj.location.z = 0.0
            obj.keyframe_insert(data_path="location", frame=end_frame)
        elif start_value > 0.9 and end_value < 0.1:
            obj.location.z = 0.0
            obj.keyframe_insert(data_path="location", frame=start_frame)
            obj.location.z = -0.2
            obj.keyframe_insert(data_path="location", frame=end_frame)
    action = obj.animation_data.action
    for curve in action.fcurves:
        if curve.data_path != "location":
            continue
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
            point.easing = "EASE_OUT"
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
