import argparse
import json
import math
from pathlib import Path
import random
import re
import sys

import bpy


PHASE_FRAMES = [150, 825, 1500, 2175, 2850]
REVEAL_FRAMES = [630, 630, 630, 630, 720]
BASE_GROW_FRAMES = [8, 9, 10, 11, 12]
BATCH_STRIDE_FRAMES = 10
BATCH_SPREAD_FRAMES = 7

MAIN_ERA_BY_NAME = {
    "Roman": 0,
    "Medieval": 1,
    "1700": 2,
    "1850": 3,
    "Modern": 4,
}
MAIN_PATTERN = re.compile(r"^Buildings_(Roman|Medieval|1700|1850|Modern)_State_Chunk_")
ISLAND_PATTERN = re.compile(r"^Island_(?:Cite|Saint_Louis)_([0-4])_State_Chunk_")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(argv)


def object_era(obj):
    main_match = MAIN_PATTERN.match(obj.name)
    if main_match:
        return MAIN_ERA_BY_NAME[main_match.group(1)]
    island_match = ISLAND_PATTERN.match(obj.name)
    if island_match:
        return int(island_match.group(1))
    return None


def action_curves(obj, data_path):
    if obj.animation_data is None or obj.animation_data.action is None:
        return []
    return [
        fcurve
        for fcurve in obj.animation_data.action.fcurves
        if fcurve.data_path == data_path
    ]


def curve_by_index(curves, index):
    return next((curve for curve in curves if curve.array_index == index), None)


def ordered_points(curve):
    return sorted(curve.keyframe_points, key=lambda point: point.co.x)


def growth_metadata(obj):
    scale_curves = action_curves(obj, "scale")
    location_curves = action_curves(obj, "location")
    scale_z = curve_by_index(scale_curves, 2)
    if scale_z is None or len(scale_z.keyframe_points) < 2:
        return None
    scale_z_points = ordered_points(scale_z)
    old_start = float(scale_z_points[0].co.x)
    old_end = float(scale_z_points[1].co.x)

    final_scale = []
    final_location = []
    for axis in range(3):
        scale_curve = curve_by_index(scale_curves, axis)
        location_curve = curve_by_index(location_curves, axis)
        if scale_curve is None or location_curve is None:
            return None
        final_scale.append(float(ordered_points(scale_curve)[1].co.y))
        final_location.append(float(ordered_points(location_curve)[1].co.y))
    return {
        "old_start": old_start,
        "old_end": old_end,
        "old_duration": old_end - old_start,
        "final_scale": tuple(final_scale),
        "final_location": tuple(final_location),
    }


def insert_key(curve, frame, value, interpolation, easing=None):
    point = curve.keyframe_points.insert(frame, value, options={"FAST"})
    point.interpolation = interpolation
    if easing is not None:
        point.easing = easing
    return point


def move_key(point, frame, value, interpolation, easing=None):
    point.co.x = frame
    point.co.y = value
    point.interpolation = interpolation
    if easing is not None:
        point.easing = easing


def rewrite_growth(obj, metadata, start_frame, duration):
    peak_frame = start_frame + max(3, duration - 2)
    final_scale = metadata["final_scale"]
    final_location = metadata["final_location"]

    scale_values = (
        (final_scale[0], final_scale[0], final_scale[0]),
        (final_scale[1], final_scale[1], final_scale[1]),
        (max(0.001, final_scale[2] * 0.012), final_scale[2] * 1.065, final_scale[2]),
    )
    location_values = (
        (final_location[0], final_location[0], final_location[0]),
        (final_location[1], final_location[1], final_location[1]),
        (final_location[2] - 0.14, final_location[2] + 0.012, final_location[2]),
    )

    for data_path, values_by_axis in (
        ("scale", scale_values),
        ("location", location_values),
    ):
        curves = action_curves(obj, data_path)
        for axis in range(3):
            curve = curve_by_index(curves, axis)
            points = ordered_points(curve)
            start_value, peak_value, end_value = values_by_axis[axis]
            move_key(points[0], start_frame, start_value, "QUAD", "EASE_OUT")
            move_key(points[1], peak_frame, peak_value, "QUAD", "EASE_OUT")
            insert_key(curve, start_frame + duration, end_value, "QUAD", "EASE_OUT")
            curve.update()

    visibility_curves = action_curves(obj, "hide_render")
    for curve in visibility_curves:
        points = ordered_points(curve)
        move_key(points[0], 1, 1.0, "CONSTANT")
        move_key(points[1], start_frame - 1, 1.0, "CONSTANT")
        move_key(points[2], start_frame, 0.0, "CONSTANT")
        curve.update()


def schedule_era(era_index, entries):
    entries.sort(key=lambda entry: (entry[1]["old_start"], entry[0].name))
    count = len(entries)
    reveal_frames = REVEAL_FRAMES[era_index]
    target_batch_count = max(1, math.ceil(reveal_frames / BATCH_STRIDE_FRAMES))
    batch_capacity = max(1, math.ceil(count / target_batch_count))
    batch_count = max(1, math.ceil(count / batch_capacity))
    duration_min = min(entry[1]["old_duration"] for entry in entries)
    duration_max = max(entry[1]["old_duration"] for entry in entries)
    rng = random.Random(7300 + era_index * 101)
    starts = []
    durations = []

    for active_index, (obj, metadata) in enumerate(entries):
        batch_index = min(batch_count - 1, active_index // batch_capacity)
        batch_first = batch_index * batch_capacity
        batch_size = min(batch_capacity, count - batch_first)
        within_batch = active_index - batch_first
        within_progress = within_batch / max(1, batch_size - 1)
        batch_progress = batch_index / max(1, batch_count - 1)
        batch_start = PHASE_FRAMES[era_index] + round(reveal_frames * batch_progress)
        start_frame = min(
            PHASE_FRAMES[era_index] + reveal_frames,
            max(
                PHASE_FRAMES[era_index],
                batch_start
                + round(BATCH_SPREAD_FRAMES * within_progress)
                + rng.choice([-1, 0, 0, 0, 1]),
            ),
        )

        if duration_max > duration_min:
            duration_progress = (
                metadata["old_duration"] - duration_min
            ) / (duration_max - duration_min)
        else:
            duration_progress = 0.5
        duration = round(BASE_GROW_FRAMES[era_index] + duration_progress * 3 + rng.choice([-1, 0, 0, 1]))
        duration = min(16, max(7, duration))
        rewrite_growth(obj, metadata, start_frame, duration)
        starts.append(start_frame)
        durations.append(duration)

    return {
        "era": era_index,
        "objects": count,
        "first_start": min(starts),
        "last_start": max(starts),
        "duration_min": min(durations),
        "duration_max": max(durations),
        "duration_average": sum(durations) / len(durations),
        "batch_count": batch_count,
    }


def main():
    args = parse_args()
    groups = {era: [] for era in range(5)}
    for obj in bpy.context.scene.objects:
        era = object_era(obj)
        if era is None:
            continue
        metadata = growth_metadata(obj)
        if metadata is not None:
            groups[era].append((obj, metadata))

    summaries = []
    for era_index, entries in groups.items():
        if not entries:
            raise RuntimeError(f"No building chunks found for era {era_index}")
        summaries.append(schedule_era(era_index, entries))

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 3600
    bpy.context.scene.frame_set(1)
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=True)
    print("SPROUT_RETIME_SUMMARY=" + json.dumps(summaries))


if __name__ == "__main__":
    main()
