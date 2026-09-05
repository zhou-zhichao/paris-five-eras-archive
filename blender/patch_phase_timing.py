import re

import bpy


def shift_point(point, delta):
    point.co.x += delta
    point.handle_left.x += delta
    point.handle_right.x += delta


def retime_chunk_root(root_name, base_frame, bucket_count, old_span, new_span, duration):
    root = bpy.data.objects[root_name]
    for child in root.children:
        match = re.search(r"_(\d+)$", child.name)
        if match is None or child.animation_data is None or child.animation_data.action is None:
            continue
        bucket_index = int(match.group(1))
        denominator = max(1, bucket_count - 1)
        old_start = base_frame + round(old_span * bucket_index / denominator)
        new_start = base_frame + round(new_span * bucket_index / denominator)
        delta = new_start - old_start
        if delta == 0:
            continue
        for fcurve in child.animation_data.action.fcurves:
            if fcurve.data_path in {"location", "scale"}:
                targets = (old_start, old_start + duration)
            elif fcurve.data_path == "hide_render":
                targets = (old_start - 1, old_start)
            else:
                continue
            for point in fcurve.keyframe_points:
                if any(abs(point.co.x - target) < 0.01 for target in targets):
                    shift_point(point, delta)


retime_chunk_root("Roads_0", 49, 50, 64, 47, 42)
retime_chunk_root("Buildings_Roman_State", 55, 90, 72, 55, 70)
retime_chunk_root("Island_Cite_0_State", 59, 60, 72, 55, 64)
retime_chunk_root("Island_Saint_Louis_0_State", 65, 44, 66, 49, 64)

retime_chunk_root("Roads_4", 610, 90, 76, 58, 42)
retime_chunk_root("Buildings_Modern_State", 610, 210, 84, 66, 70)
retime_chunk_root("Island_Cite_4_State", 614, 108, 84, 66, 64)
retime_chunk_root("Island_Saint_Louis_4_State", 620, 84, 78, 60, 64)

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
