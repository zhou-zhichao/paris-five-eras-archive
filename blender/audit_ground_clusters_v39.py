import importlib.util
import json
from pathlib import Path

import bmesh
import bpy


MODULE_PATH = Path(__file__).with_name("place_medieval_trellis_landmarks_v38.py")
NAMES = [
    "Buildings_Medieval_State_Chunk_00801",
    "Buildings_Medieval_State_Chunk_00879",
    "Island_Cite_1_State_Chunk_00065",
    "Island_Cite_1_State_Chunk_00072",
]


def load_module():
    specification = importlib.util.spec_from_file_location("landmark_v39_audit", MODULE_PATH)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def cluster_count(module, polygons):
    parents = list(range(len(polygons)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(first, second):
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parents[second_root] = first_root

    for first in range(len(polygons)):
        for second in range(first + 1, len(polygons)):
            if module.convex_polygons_intersect(polygons[first], polygons[second], gap=0.001):
                union(first, second)
    return len({find(index) for index in range(len(polygons))})


def main():
    module = load_module()
    bpy.context.scene.frame_set(1450)
    bpy.context.view_layer.update()
    report = {}
    for name in NAMES:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        matrix_world = obj.matrix_world.copy()
        minimum_z = min(vertex.co.z for vertex in bm.verts)
        ground_polygons = []
        for face in bm.faces:
            if not face.verts or max(abs(vertex.co.z - minimum_z) for vertex in face.verts) > 1e-5:
                continue
            polygon = [(point.x, point.y) for point in (matrix_world @ vertex.co for vertex in face.verts)]
            if len(polygon) >= 3:
                ground_polygons.append(polygon)
        report[name] = {
            "minimum_z": minimum_z,
            "ground_faces": len(ground_polygons),
            "ground_clusters": cluster_count(module, ground_polygons) if ground_polygons else 0,
            "faces": len(bm.faces),
        }
        bm.free()
    print("GROUND_CLUSTERS_JSON=" + json.dumps(report))


if __name__ == "__main__":
    main()
