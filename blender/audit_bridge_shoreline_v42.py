import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_DIR / "reports" / "bridge_shoreline_audit_v42.json"
BRIDGE_NAME = "Landmark_Petit_Pont_Chatelet_Trellis"
FRAME = 1450


def cross_2d(a, b):
    return a[0] * b[1] - a[1] * b[0]


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "minimum": [min(point[i] for point in points) for i in range(3)],
        "maximum": [max(point[i] for point in points) for i in range(3)],
    }


def projected_bounds(obj, origin, axis, normal):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    longitudinal = [(point.x - origin.x) * axis.x + (point.y - origin.y) * axis.y for point in points]
    lateral = [(point.x - origin.x) * normal.x + (point.y - origin.y) * normal.y for point in points]
    return [min(longitudinal), max(longitudinal)], [min(lateral), max(lateral)]


def line_mesh_intersections(obj, origin, axis):
    if obj.type != "MESH":
        return []
    mesh = obj.data
    matrix = obj.matrix_world
    hits = []
    for edge in mesh.edges:
        first = matrix @ mesh.vertices[edge.vertices[0]].co
        second = matrix @ mesh.vertices[edge.vertices[1]].co
        delta = (second.x - first.x, second.y - first.y)
        denominator = cross_2d((axis.x, axis.y), delta)
        if abs(denominator) < 1e-9:
            continue
        offset = (first.x - origin.x, first.y - origin.y)
        t = cross_2d(offset, delta) / denominator
        s = cross_2d(offset, (axis.x, axis.y)) / denominator
        if -1e-6 <= s <= 1.0 + 1e-6:
            point = origin + axis * t
            hits.append((t, point.x, point.y, first.z + (second.z - first.z) * s))

    hits.sort(key=lambda hit: hit[0])
    unique = []
    for hit in hits:
        if unique and abs(hit[0] - unique[-1][0]) < 0.001:
            unique[-1][3] = max(unique[-1][3], hit[3])
            continue
        unique.append(list(hit))
    return unique


def near_bridge(obj, origin, axis, normal):
    if obj.type != "MESH":
        return False
    longitudinal, lateral = projected_bounds(obj, origin, axis, normal)
    return longitudinal[1] >= -1.2 and longitudinal[0] <= 1.2 and lateral[1] >= -0.45 and lateral[0] <= 0.45


def main():
    scene = bpy.context.scene
    scene.frame_set(FRAME)
    root = bpy.data.objects[BRIDGE_NAME]
    axis = (root.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
    axis.z = 0.0
    axis.normalize()
    normal = Vector((-axis.y, axis.x, 0.0))
    origin = root.matrix_world.translation.copy()

    exact_names = {
        "Ile_de_la_Cite",
        "Ile_de_la_Cite_Margin",
        "Seine",
        "Seine_Riverbank",
        "OSM_Bridgehead_744835294_Island",
        "OSM_Bridgehead_744835294_Mainland",
        "Bridge_Approach_medieval_ile_de_la_cite_00_Island",
        "Bridge_Approach_medieval_ile_de_la_cite_00_Mainland",
        "Petit_Pont_Mainland_Approach_v41",
    }
    selected = []
    for obj in bpy.data.objects:
        if obj.name in exact_names:
            selected.append(obj)
            continue
        if obj.name.startswith(("Cite_Wall_v21_", "Cite_Gate_v21_", "Roads_1_Chunk_", "Island_Cite_1_State_Chunk_")):
            if near_bridge(obj, origin, axis, normal):
                selected.append(obj)

    objects = []
    for obj in selected:
        longitudinal, lateral = projected_bounds(obj, origin, axis, normal)
        objects.append(
            {
                "name": obj.name,
                "type": obj.type,
                "visible": not obj.hide_render,
                "bounds": world_bounds(obj),
                "longitudinal": longitudinal,
                "lateral": lateral,
                "line_intersections": line_mesh_intersections(obj, origin, axis),
            }
        )

    bridge_meshes = [obj for obj in root.children_recursive if obj.type == "MESH"]
    bridge_points = [obj.matrix_world @ Vector(corner) for obj in bridge_meshes for corner in obj.bound_box]
    bridge_longitudinal = [
        (point.x - origin.x) * axis.x + (point.y - origin.y) * axis.y for point in bridge_points
    ]
    bridge_lateral = [
        (point.x - origin.x) * normal.x + (point.y - origin.y) * normal.y for point in bridge_points
    ]

    bridge_vertices = []
    for obj in bridge_meshes:
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            longitudinal = (point.x - origin.x) * axis.x + (point.y - origin.y) * axis.y
            lateral = (point.x - origin.x) * normal.x + (point.y - origin.y) * normal.y
            bridge_vertices.append((longitudinal, lateral, point.z))
    bridge_centerline_samples = {}
    for sample in (-0.40, -0.25, 0.00, 0.25, 0.40, 0.46, 0.55, 0.62):
        heights = sorted(
            point[2]
            for point in bridge_vertices
            if abs(point[0] - sample) <= 0.025 and abs(point[1]) <= 0.045
        )
        if heights:
            bridge_centerline_samples[f"{sample:.2f}"] = {
                "minimum": heights[0],
                "median": heights[len(heights) // 2],
                "maximum": heights[-1],
                "count": len(heights),
            }

    report = {
        "frame": FRAME,
        "bridge_origin": list(origin),
        "bridge_axis": list(axis),
        "bridge_normal": list(normal),
        "bridge_longitudinal": [min(bridge_longitudinal), max(bridge_longitudinal)],
        "bridge_lateral": [min(bridge_lateral), max(bridge_lateral)],
        "bridge_centerline_samples": bridge_centerline_samples,
        "objects": sorted(objects, key=lambda item: item["name"]),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
