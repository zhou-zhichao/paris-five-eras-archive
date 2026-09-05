from pathlib import Path

import bpy


PHASE_START = 2850.0
STRETCH = 630.0 / 510.0
TARGET_PREFIXES = (
    "Buildings_Modern_State",
    "Island_Cite_4_State",
    "Island_Saint_Louis_4_State",
    "Buildings_1850_State",
    "Island_Cite_3_State",
    "Island_Saint_Louis_3_State",
    "Roads_4",
    "Forest_Cleared_4",
    "Modern_Railways",
    "Modern_Stations",
    "Gare_",
    "Landmark_Eiffel",
    "Landmark_La_Defense",
    "Landmark_Champ",
    "Champ_",
    "Eiffel_",
    "Defense_",
)


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


def remap_frame(frame):
    if frame < PHASE_START:
        return frame
    return PHASE_START + (frame - PHASE_START) * STRETCH


def retime_id(animated_id):
    changed = 0
    for fcurve in animation_fcurves(animated_id):
        for point in fcurve.keyframe_points:
            if point.co.x < PHASE_START:
                continue
            point.co.x = remap_frame(point.co.x)
            point.handle_left.x = remap_frame(point.handle_left.x)
            point.handle_right.x = remap_frame(point.handle_right.x)
            changed += 1
        fcurve.update()
    return changed


def main():
    changed = 0
    touched = 0
    for obj in bpy.context.scene.objects:
        if not obj.name.startswith(TARGET_PREFIXES):
            continue
        object_changes = retime_id(obj)
        if obj.type == "MESH" and obj.data.shape_keys is not None:
            object_changes += retime_id(obj.data.shape_keys)
        if object_changes:
            changed += object_changes
            touched += 1
    bpy.context.scene.frame_set(1)
    output_path = Path(bpy.data.filepath)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"TAIL_RETIME objects={touched} keyframes={changed} stretch={STRETCH:.6f}")


if __name__ == "__main__":
    main()
