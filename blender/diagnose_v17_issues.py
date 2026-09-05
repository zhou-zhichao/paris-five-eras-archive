import json
from collections import Counter

import bpy
from mathutils import Vector


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[axis] for point in corners) for axis in range(3)],
        "max": [max(point[axis] for point in corners) for axis in range(3)],
    }


def public_properties(data):
    result = {}
    for name in dir(data):
        if name.startswith("_"):
            continue
        try:
            value = getattr(data, name)
        except Exception:
            continue
        if isinstance(value, (bool, int, float, str)):
            result[name] = value
    return result


def mesh_report(obj):
    mesh = obj.data
    mesh.calc_tangents() if mesh.uv_layers else None
    corner_normals = [tuple(item.vector) for item in mesh.corner_normals]
    polygon_keys = []
    for polygon in mesh.polygons:
        points = sorted(
            tuple(round(value, 5) for value in mesh.vertices[index].co)
            for index in polygon.vertices
        )
        polygon_keys.append(tuple(points))
    duplicates = sum(count - 1 for count in Counter(polygon_keys).values() if count > 1)
    geometry_rows = []
    for polygon in mesh.polygons:
        points = [mesh.vertices[index].co for index in polygon.vertices]
        edge_lengths = [
            (points[(index + 1) % len(points)] - points[index]).length
            for index in range(len(points))
        ]
        signed_triangles = []
        for index in range(1, len(points) - 1):
            first = points[index] - points[0]
            second = points[index + 1] - points[0]
            signed_triangles.append(first.x * second.y - first.y * second.x)
        geometry_rows.append(
            {
                "index": polygon.index,
                "area": polygon.area,
                "max_edge": max(edge_lengths),
                "signed_triangles": signed_triangles,
                "center": list(polygon.center),
            }
        )
    suspect_rows = sorted(
        geometry_rows,
        key=lambda row: (
            min(row["signed_triangles"], default=0.0),
            row["area"],
        ),
    )[:12]
    return {
        "name": obj.name,
        "bounds": world_bounds(obj),
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "duplicate_polygons": duplicates,
        "face_area": {
            "min": min((row["area"] for row in geometry_rows), default=None),
            "max": max((row["area"] for row in geometry_rows), default=None),
        },
        "mixed_or_negative_triangulation": sum(
            any(value <= 0.0 for value in row["signed_triangles"])
            for row in geometry_rows
        ),
        "suspect_faces": suspect_rows,
        "normal_z": {
            "negative": sum(polygon.normal.z < -1e-5 for polygon in mesh.polygons),
            "flat": sum(abs(polygon.normal.z) <= 1e-5 for polygon in mesh.polygons),
            "positive": sum(polygon.normal.z > 1e-5 for polygon in mesh.polygons),
        },
        "smooth_faces": sum(polygon.use_smooth for polygon in mesh.polygons),
        "corner_normal_z": {
            "min": min((normal[2] for normal in corner_normals), default=None),
            "max": max((normal[2] for normal in corner_normals), default=None),
            "negative": sum(normal[2] < -1e-5 for normal in corner_normals),
            "flat": sum(abs(normal[2]) <= 1e-5 for normal in corner_normals),
            "positive": sum(normal[2] > 1e-5 for normal in corner_normals),
        },
        "has_custom_normals": getattr(mesh, "has_custom_normals", None),
        "z_values": sorted({round(vertex.co.z, 5) for vertex in mesh.vertices})[:30],
    }


scene = bpy.context.scene
water_material = bpy.data.materials.get("Water_Material")
water_users = []
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    if any(slot.material == water_material for slot in obj.material_slots):
        water_users.append(mesh_report(obj))

probe = bpy.data.objects.get("Seine_Planar_Reflection_Probe")
probe_report = None
if probe:
    probe_report = {
        "name": probe.name,
        "type": probe.type,
        "location": list(probe.location),
        "rotation": list(probe.rotation_euler),
        "scale": list(probe.scale),
        "dimensions": list(probe.dimensions),
        "bounds": world_bounds(probe),
        "data": public_properties(probe.data),
    }

notre = bpy.data.objects.get("Landmark_Notre_Dame_GLB")
notre_mesh = bpy.data.objects.get("Landmark_Notre_Dame_GLB_Mesh")
notre_chain = []
current = notre_mesh
while current:
    notre_chain.append(current)
    current = current.parent

eevee = scene.eevee
report = {
    "engine": scene.render.engine,
    "render": {
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "percentage": scene.render.resolution_percentage,
        "samples": eevee.taa_samples,
        "use_raytracing": getattr(eevee, "use_raytracing", None),
        "ray_tracing_method": getattr(eevee, "ray_tracing_method", None),
    },
    "probe": probe_report,
    "light_probes": [
        {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "scale": list(obj.scale),
        }
        for obj in bpy.data.objects
        if obj.type == "LIGHT_PROBE"
    ],
    "water_users": water_users,
    "notre_dame": {
        "parent": world_bounds(notre) if notre else None,
        "hierarchy": [
            {
                "name": item.name,
                "type": item.type,
                "location": list(item.location),
                "rotation": list(item.rotation_euler),
                "scale": list(item.scale),
                "dimensions": list(item.dimensions),
                "bounds": world_bounds(item),
            }
            for item in notre_chain
        ],
    },
}

print("V17_DIAGNOSTIC_BEGIN")
print(json.dumps(report, indent=2, default=str))
print("V17_DIAGNOSTIC_END")
