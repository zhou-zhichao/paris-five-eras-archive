import json
from collections import Counter

import bpy
from mathutils import Vector


NAMES = [
    "Buildings_1700_State_Chunk_00307",
    "Island_Cite_3_State_Chunk_00102",
    "Island_Cite_4_State_Chunk_00090",
]


def main():
    report = {}
    for name in NAMES:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            continue
        if "1700" in name:
            bpy.context.scene.frame_set(2100)
        elif "_3_State" in name:
            bpy.context.scene.frame_set(2775)
        elif "_4_State" in name:
            bpy.context.scene.frame_set(3500)
        bpy.context.view_layer.update()
        corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        slot_report = []
        face_counts = Counter(polygon.material_index for polygon in obj.data.polygons)
        for index, material in enumerate(obj.data.materials):
            slot_report.append(
                {
                    "index": index,
                    "name": material.name if material is not None else None,
                    "faces": face_counts.get(index, 0),
                }
            )
        report[name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "world_bounds": [
                [min(point.x for point in corners), min(point.y for point in corners), min(point.z for point in corners)],
                [max(point.x for point in corners), max(point.y for point in corners), max(point.z for point in corners)],
            ],
            "slots": slot_report,
        }
    print("HOUSE_GROUPS_JSON=" + json.dumps(report))


if __name__ == "__main__":
    main()
