import json
import math
import re

import bpy


BUILDING_PATTERN = re.compile(
    r"^(Buildings_(Roman|Medieval|1700|1850|Modern)_State|Island_(Cite|Saint_Louis)_[0-4]_State)_Chunk_"
)


def growth_interval(obj):
    if obj.animation_data is None or obj.animation_data.action is None:
        return None
    curve = next(
        (
            fcurve
            for fcurve in obj.animation_data.action.fcurves
            if fcurve.data_path == "scale" and fcurve.array_index == 2
        ),
        None,
    )
    if curve is None or len(curve.keyframe_points) < 2:
        return None
    points = sorted(curve.keyframe_points, key=lambda point: point.co.x)
    return float(points[0].co.x), float(points[1].co.x)


def main():
    fps = bpy.context.scene.render.fps
    intervals = []
    for obj in bpy.data.objects:
        if not BUILDING_PATTERN.match(obj.name):
            continue
        interval = growth_interval(obj)
        if interval is not None:
            intervals.append((obj.name, *interval))

    seconds = []
    for second in range(math.ceil(bpy.context.scene.frame_end / fps)):
        frame_start = second * fps + 1
        frame_end = min(bpy.context.scene.frame_end, frame_start + fps - 1)
        starts = sum(frame_start <= start <= frame_end for _, start, _ in intervals)
        active = sum(start <= frame_end and end >= frame_start for _, start, end in intervals)
        seconds.append({"second": second, "starts": starts, "active": active})

    dead_runs = []
    current = []
    for item in seconds:
        if item["second"] < 4 or item["starts"] or item["active"]:
            if current:
                dead_runs.append(current)
                current = []
            continue
        current.append(item["second"])
    if current:
        dead_runs.append(current)

    durations = [end - start for _, start, end in intervals]
    summary = {
        "objects": len(intervals),
        "duration_frames": {
            "min": min(durations) if durations else None,
            "max": max(durations) if durations else None,
            "average": sum(durations) / len(durations) if durations else None,
        },
        "dead_runs": [
            {
                "start_second": run[0],
                "end_second": run[-1],
                "duration_seconds": len(run),
            }
            for run in dead_runs
        ],
        "seconds": seconds,
    }
    print("BUILDING_GROWTH_AUDIT=" + json.dumps(summary))


if __name__ == "__main__":
    main()
