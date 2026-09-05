import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


LANDMARKS = {
    "Landmark_Petit_Pont_Chatelet_Trellis": {"start": 930, "end": 2204},
    "Landmark_Sainte_Chapelle_Trellis": {"start": 970, "end": None},
    "Landmark_Saint_Germain_des_Pres_Trellis": {"start": 1010, "end": 2204},
    "Landmark_Tour_du_Temple_Trellis": {"start": 1050, "end": 2204},
}
FRAMES = [1, 929, 930, 944, 958, 969, 970, 984, 998, 1009, 1010, 1024, 1038, 1049, 1050, 1064, 1078, 1450, 2174, 2175, 2189, 2203, 2204, 3500]
BRIDGE_ISLAND_POINT = Vector((-2.0898, 0.5654))
BRIDGE_MAINLAND_POINT = Vector((-2.2276, 0.1946))
BRIDGE_UNIT = (BRIDGE_ISLAND_POINT - BRIDGE_MAINLAND_POINT).normalized()
BRIDGE_NORMAL = Vector((-BRIDGE_UNIT.y, BRIDGE_UNIT.x))


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def effectively_hidden(obj):
    current = obj
    while current is not None:
        if current.hide_render:
            return True
        current = current.parent
    return False


def object_state(obj):
    return {
        "hide_render": bool(obj.hide_render),
        "effectively_hidden": effectively_hidden(obj),
        "location": list(obj.location),
        "scale": list(obj.scale),
    }


def cross_2d(first, second):
    return first.x * second.y - first.y * second.x


def line_mesh_intersections(obj, origin, axis):
    hits = []
    for edge in obj.data.edges:
        first_world = obj.matrix_world @ obj.data.vertices[edge.vertices[0]].co
        second_world = obj.matrix_world @ obj.data.vertices[edge.vertices[1]].co
        first = Vector((first_world.x, first_world.y))
        second = Vector((second_world.x, second_world.y))
        delta = second - first
        denominator = cross_2d(axis, delta)
        if abs(denominator) < 1e-9:
            continue
        offset = first - origin
        t = cross_2d(offset, delta) / denominator
        segment_progress = cross_2d(offset, axis) / denominator
        if -1e-6 <= segment_progress <= 1.0 + 1e-6:
            hits.append(t)
    hits.sort()
    unique = []
    for hit in hits:
        if not unique or abs(hit - unique[-1]) >= 0.001:
            unique.append(hit)
    return unique


def bridge_projection():
    root = bpy.data.objects.get("Landmark_Petit_Pont_Chatelet_Trellis")
    mesh = bpy.data.objects.get("Landmark_Petit_Pont_Chatelet_Trellis_Mesh_00")
    if root is None or mesh is None:
        raise RuntimeError("Petit-Pont TRELLIS mesh was not found")
    origin = Vector((root.matrix_world.translation.x, root.matrix_world.translation.y))
    axis = Vector((math.cos(root.rotation_euler.z), math.sin(root.rotation_euler.z)))
    perpendicular = Vector((-axis.y, axis.x))
    projections = []
    cross_offsets = []
    for vertex in mesh.data.vertices:
        world = mesh.matrix_world @ vertex.co
        delta = Vector((world.x, world.y)) - origin
        projections.append(delta.dot(axis))
        cross_offsets.append(delta.dot(perpendicular))

    island = bpy.data.objects.get("Ile_de_la_Cite")
    road = bpy.data.objects.get("Roads_1_Chunk_00013")
    if island is None or road is None:
        raise RuntimeError("Bridge shoreline audit geometry was not found")
    island_hits = [hit for hit in line_mesh_intersections(island, origin, axis) if hit > 0.0]
    road_hits = [hit for hit in line_mesh_intersections(road, origin, axis) if hit > 0.0]
    if not island_hits or not road_hits:
        raise RuntimeError("Bridge shoreline audit found no forward intersections")
    island_edge = min(island_hits)
    road_edge = min(road_hits)
    model_maximum = max(projections)
    return {
        "model_projection_min": min(projections),
        "model_projection_max": model_maximum,
        "island_land_edge": island_edge,
        "island_road_edge": road_edge,
        "island_land_overlap": model_maximum - island_edge,
        "island_road_overlap": model_maximum - road_edge,
        "cross_offset_min": min(cross_offsets),
        "cross_offset_max": max(cross_offsets),
        "island_extension": float(root.get("island_extension", 0.0)),
        "island_rise": float(root.get("island_rise", 0.0)),
    }


def main():
    args = parse_args()
    args.report = args.report.resolve()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    states = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        states[str(frame)] = {}
        for name in LANDMARKS:
            obj = bpy.data.objects.get(name)
            if obj is None:
                raise RuntimeError(f"Missing landmark root: {name}")
            states[str(frame)][name] = object_state(obj)
        for name in (
            "OSM_Bridge_744835294_Deck_00",
            "Cite_Gate_v21_05_00_Tower_0",
        ):
            obj = bpy.data.objects.get(name)
            if obj is None:
                raise RuntimeError(f"Missing audit object: {name}")
            states[str(frame)][name] = object_state(obj)

    checks = []
    for name, timing in LANDMARKS.items():
        start = timing["start"]
        checks.append((f"{name}: hidden before start", states[str(start - 1)][name]["effectively_hidden"]))
        checks.append((f"{name}: visible at start", not states[str(start)][name]["effectively_hidden"]))
        checks.append((f"{name}: starts collapsed", states[str(start)][name]["scale"][2] <= 0.02))
        checks.append((f"{name}: fully grown", states[str(start + 28)][name]["scale"][2] >= 0.99))
        checks.append((f"{name}: visible in medieval frame", not states["1450"][name]["effectively_hidden"]))
        if timing["end"] is None:
            checks.append((f"{name}: persists to modern frame", not states["3500"][name]["effectively_hidden"]))
        else:
            checks.append((f"{name}: hidden after historical lifetime", states[str(timing["end"])][name]["effectively_hidden"]))

    old_bridge_name = "OSM_Bridge_744835294_Deck_00"
    checks.extend(
        [
            ("old bridge visible before replacement", not states["929"][old_bridge_name]["effectively_hidden"]),
            ("old bridge hidden during replacement", states["1450"][old_bridge_name]["effectively_hidden"]),
            ("old bridge restored after replacement", not states["2204"][old_bridge_name]["effectively_hidden"]),
            ("old Cite gate hidden when TRELLIS bridge appears", states["930"]["Cite_Gate_v21_05_00_Tower_0"]["effectively_hidden"]),
            ("obsolete raised approach slab removed", bpy.data.objects.get("Petit_Pont_Mainland_Approach_v41") is None),
        ]
    )

    scene.frame_set(1450)
    bpy.context.view_layer.update()
    projection = bridge_projection()
    checks.extend(
        [
            ("bridge overlaps visible island land", projection["island_land_overlap"] >= 0.05),
            ("bridge reaches the island road", projection["island_road_overlap"] >= 0.02),
            ("bridge is not overextended into the city", projection["island_road_overlap"] <= 0.12),
            ("bridge terminal rises to road grade", projection["island_rise"] >= 0.05),
        ]
    )
    failures = [name for name, passed in checks if not passed]
    report = {
        "blend": bpy.data.filepath,
        "checks": [{"name": name, "passed": bool(passed)} for name, passed in checks],
        "failure_count": len(failures),
        "failures": failures,
        "bridge_projection": projection,
        "states": states,
    }
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise RuntimeError("Lifecycle audit failed: " + "; ".join(failures))


if __name__ == "__main__":
    main()
