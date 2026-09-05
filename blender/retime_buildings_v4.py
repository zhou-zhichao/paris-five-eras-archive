import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

import bpy


PHASE_FRAMES = [150, 825, 1500, 2175, 2850]
PHASE_REVEAL_FRAMES = [660, 660, 660, 660, 735]
BUILDING_GROW_FRAMES = [6, 6, 7, 7, 8]
BATCH_STRIDE_FRAMES = 45
BATCH_SPREAD_FRAMES = 24


LAYER_SPECS = [
    ("Buildings_Roman_State", 0, 0),
    ("Island_Cite_0_State", 0, 4),
    ("Island_Saint_Louis_0_State", 0, 10),
    ("Buildings_Medieval_State", 1, 0),
    ("Island_Cite_1_State", 1, 4),
    ("Island_Saint_Louis_1_State", 1, 10),
    ("Buildings_1700_State", 2, 0),
    ("Island_Cite_2_State", 2, 4),
    ("Island_Saint_Louis_2_State", 2, 10),
    ("Buildings_1850_State", 3, 0),
    ("Island_Cite_3_State", 3, 4),
    ("Island_Saint_Louis_3_State", 3, 10),
    ("Buildings_Modern_State", 4, 0),
    ("Island_Cite_4_State", 4, 4),
    ("Island_Saint_Louis_4_State", 4, 10),
]


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(args)


def set_constant_keyframes(obj, data_path):
    action = getattr(getattr(obj, "animation_data", None), "action", None)
    if action is None:
        return
    for curve in action.fcurves:
        if curve.data_path != data_path:
            continue
        for keyframe in curve.keyframe_points:
            keyframe.interpolation = "CONSTANT"


def key_visibility_start(obj, start_frame):
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=1)
    obj.keyframe_insert(data_path="hide_render", frame=start_frame - 1)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=start_frame)
    set_constant_keyframes(obj, "hide_render")


def set_motion_easing(obj):
    action = getattr(getattr(obj, "animation_data", None), "action", None)
    if action is None:
        return
    for curve in action.fcurves:
        if curve.data_path not in {"location", "scale"}:
            continue
        for keyframe in curve.keyframe_points:
            keyframe.interpolation = "QUAD"
            keyframe.easing = "EASE_OUT"


def batched_stagger_frame(item_index, item_count, start_frame, reveal_frames, timing_rng):
    if item_count <= 1:
        return start_frame
    usable_batch_span = max(0, reveal_frames - BATCH_SPREAD_FRAMES)
    target_batch_count = max(1, math.floor(usable_batch_span / BATCH_STRIDE_FRAMES) + 1)
    batch_capacity = max(1, math.ceil(item_count / target_batch_count))
    batch_count = max(1, math.ceil(item_count / batch_capacity))
    batch_index = min(batch_count - 1, item_index // batch_capacity)
    batch_first = batch_index * batch_capacity
    batch_size = min(batch_capacity, item_count - batch_first)
    within_batch = item_index - batch_first
    within_progress = within_batch / max(1, batch_size - 1)
    if batch_count <= 1:
        batch_start = start_frame
    else:
        batch_start = start_frame + round(
            usable_batch_span * batch_index / (batch_count - 1)
        )
    within_offset = round(BATCH_SPREAD_FRAMES * within_progress)
    jitter = timing_rng.choice([-1, 0, 0, 0, 1])
    return min(
        start_frame + reveal_frames,
        max(start_frame, batch_start + within_offset + jitter),
    )


def animate_sprout(obj, start_frame, duration):
    key_visibility_start(obj, start_frame)
    peak_frame = start_frame + max(3, duration - 2)
    obj.location = (0.0, 0.0, -0.14)
    obj.scale = (1.0, 1.0, 0.012)
    obj.keyframe_insert(data_path="location", frame=start_frame)
    obj.keyframe_insert(data_path="scale", frame=start_frame)
    obj.location = (0.0, 0.0, 0.012)
    obj.scale = (1.0, 1.0, 1.065)
    obj.keyframe_insert(data_path="location", frame=peak_frame)
    obj.keyframe_insert(data_path="scale", frame=peak_frame)
    obj.location = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.keyframe_insert(data_path="location", frame=start_frame + duration)
    obj.keyframe_insert(data_path="scale", frame=start_frame + duration)
    set_motion_easing(obj)


def animate_removal(obj, start_frame, duration):
    obj.location = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.keyframe_insert(data_path="location", frame=start_frame)
    obj.keyframe_insert(data_path="scale", frame=start_frame)
    obj.location = (0.0, 0.0, -0.2)
    obj.scale = (1.0, 1.0, 0.02)
    obj.keyframe_insert(data_path="location", frame=start_frame + duration)
    obj.keyframe_insert(data_path="scale", frame=start_frame + duration)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=start_frame + duration)
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=start_frame + duration + 1)
    set_constant_keyframes(obj, "hide_render")
    set_motion_easing(obj)


def reset_chunk(obj):
    obj.animation_data_clear()
    obj.location = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.hide_render = False


def chunk_duration(obj, era, timing_rng):
    max_height = max((vertex.co.z for vertex in obj.data.vertices), default=0.0)
    height_factor = min(0.12, max_height * 0.08)
    duration_factor = timing_rng.uniform(0.82, 1.08) + height_factor
    return min(9, max(5, round(BUILDING_GROW_FRAMES[era] * duration_factor)))


def retime_layer(root_name, era, start_offset):
    root = bpy.data.objects.get(root_name)
    if root is None:
        raise RuntimeError(f"Missing building layer: {root_name}")
    chunks = sorted(root.children, key=lambda child: child.name)
    timing_rng = random.Random(era * 100003 + len(chunks) * 43 + start_offset * 17)
    start_frame = PHASE_FRAMES[era] + start_offset
    reveal_frames = PHASE_REVEAL_FRAMES[era] - (6 if start_offset == 10 else 0)
    starts = []
    durations = []

    for index, chunk in enumerate(chunks):
        reset_chunk(chunk)
        chunk_start = batched_stagger_frame(
            index,
            len(chunks),
            start_frame,
            reveal_frames,
            timing_rng,
        )
        duration = chunk_duration(chunk, era, timing_rng)
        animate_sprout(chunk, chunk_start, duration)
        chunk["growth_start_frame"] = chunk_start
        chunk["growth_duration_frames"] = duration
        starts.append(chunk_start)
        durations.append(duration)

    if era < 4:
        removal_rng = random.Random(len(chunks) * 43 + (PHASE_FRAMES[era + 1] - 6) * 17)
        removal_start = PHASE_FRAMES[era + 1] - 6
        removal_reveal = max(120, PHASE_REVEAL_FRAMES[era + 1] - 18)
        for index, chunk in enumerate(chunks):
            chunk_start = batched_stagger_frame(
                index,
                len(chunks),
                removal_start,
                removal_reveal,
                removal_rng,
            )
            animate_removal(chunk, chunk_start, 8)

    return {
        "name": root_name,
        "era": era,
        "chunks": len(chunks),
        "first_start": min(starts, default=None),
        "last_start": max(starts, default=None),
        "last_end": max((start + duration for start, duration in zip(starts, durations)), default=None),
        "duration_histogram": dict(sorted(Counter(durations).items())),
    }


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.frame_set(1)

    reports = [retime_layer(*spec) for spec in LAYER_SPECS]
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output),
        "phase_reveal_frames": PHASE_REVEAL_FRAMES,
        "growth_frames": BUILDING_GROW_FRAMES,
        "batch_stride_frames": BATCH_STRIDE_FRAMES,
        "batch_spread_frames": BATCH_SPREAD_FRAMES,
        "layers": reports,
    }
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
