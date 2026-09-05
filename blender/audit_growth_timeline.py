import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import bpy


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    return Path(args[0]) if args else None


def keyframe_frames(obj, data_path):
    action = getattr(getattr(obj, "animation_data", None), "action", None)
    if action is None:
        return []
    frames = set()
    for curve in action.fcurves:
        if curve.data_path != data_path:
            continue
        frames.update(round(point.co.x) for point in curve.keyframe_points)
    return sorted(frames)


def is_building_chunk(obj):
    if obj.type != "MESH" or "_Chunk_" not in obj.name:
        return False
    return obj.name.startswith(("Buildings_", "Island_Cite_", "Island_Saint_Louis_"))


def main():
    output_path = parse_args()
    scene = bpy.context.scene
    starts = Counter()
    ends = Counter()
    durations = Counter()
    by_layer = defaultdict(lambda: {"count": 0, "first": None, "last": None})
    intervals = []

    for obj in bpy.data.objects:
        if not is_building_chunk(obj):
            continue
        frames = keyframe_frames(obj, "scale")
        if len(frames) < 2:
            continue
        start = frames[0]
        end = frames[2] if len(frames) >= 3 else frames[1]
        duration = end - start
        intervals.append((start, end, obj.name))
        starts[start] += 1
        ends[end] += 1
        durations[duration] += 1
        layer_name = obj.parent.name if obj.parent else obj.name.split("_Chunk_")[0]
        layer = by_layer[layer_name]
        layer["count"] += 1
        layer["first"] = start if layer["first"] is None else min(layer["first"], start)
        layer["last"] = end if layer["last"] is None else max(layer["last"], end)

    active_by_frame = {}
    for frame in range(scene.frame_start, scene.frame_end + 1):
        active_by_frame[frame] = sum(start <= frame < end for start, end, _ in intervals)

    active_frames = [frame for frame, count in active_by_frame.items() if count > 0]
    gaps = []
    if active_frames:
        previous = active_frames[0]
        for frame in active_frames[1:]:
            if frame > previous + 1:
                gaps.append((previous + 1, frame - 1))
            previous = frame

    per_second = []
    fps = scene.render.fps / scene.render.fps_base
    second_count = int(scene.frame_end / fps) + 1
    for second in range(second_count):
        first = int(second * fps) + 1
        last = min(scene.frame_end, int((second + 1) * fps))
        started = sum(count for frame, count in starts.items() if first <= frame <= last)
        peak_active = max((active_by_frame.get(frame, 0) for frame in range(first, last + 1)), default=0)
        per_second.append({"second": second, "started": started, "peak_active": peak_active})

    report = {
        "scene": bpy.data.filepath,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "fps": fps,
        "animated_chunks": len(intervals),
        "duration_histogram": dict(sorted(durations.items())),
        "global_first_start": min((start for start, _, _ in intervals), default=None),
        "global_last_end": max((end for _, end, _ in intervals), default=None),
        "longest_no_growth_gaps": sorted(
            (
                {"start": start, "end": end, "frames": end - start + 1}
                for start, end in gaps
            ),
            key=lambda item: item["frames"],
            reverse=True,
        )[:20],
        "layers": dict(sorted(by_layer.items())),
        "seconds_with_no_starts": [item["second"] for item in per_second if item["started"] == 0],
        "per_second": per_second,
    }

    payload = json.dumps(report, indent=2, sort_keys=True)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
