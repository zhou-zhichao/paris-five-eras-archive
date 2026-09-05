import json

import bpy


NAMES = [
    "OSM_Bridge_744835294",
    "OSM_Bridge_744835294_Deck_00",
    "Cite_Gate_v21_05_00_Tower_0",
    "Landmark_Medieval_Cite_Wall",
    "Buildings_Roman_State",
    "Buildings_Medieval_State",
    "Buildings_1700_State",
    "Buildings_1850_State",
    "Buildings_Modern_State",
    "Island_Cite_1_State",
    "Island_Cite_2_State",
]
FRAMES = [1, 149, 150, 824, 825, 900, 1450, 1500, 1680, 1920, 1921, 2175, 2395, 2850, 3070, 3599]


def main():
    report = {}
    for name in NAMES:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        entry = {"values": {}, "curves": []}
        for frame in FRAMES:
            bpy.context.scene.frame_set(frame)
            entry["values"][str(frame)] = {
                "hide_render": obj.hide_render,
                "world_location": list(obj.matrix_world.translation),
                "world_scale": list(obj.matrix_world.to_scale()),
            }
        action = getattr(getattr(obj, "animation_data", None), "action", None)
        if action is not None:
            for curve in action.fcurves:
                entry["curves"].append(
                    {
                        "data_path": curve.data_path,
                        "array_index": curve.array_index,
                        "keys": [list(point.co) for point in curve.keyframe_points],
                    }
                )
        report[name] = entry
    print("ANIM_JSON=" + json.dumps(report))


if __name__ == "__main__":
    main()
