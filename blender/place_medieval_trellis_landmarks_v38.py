import argparse
import json
import math
import sys
from collections import deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "outputs" / "medieval_landmarks_1259_trellis_v1"
FULL_STATE_FRAMES = {1: 1450, 2: 2100, 3: 2775, 4: 3500}
BRIDGE_ISLAND_POINT = (-2.0898, 0.5654)
BRIDGE_MAINLAND_POINT = (-2.2276, 0.1946)
BRIDGE_VECTOR = (
    BRIDGE_ISLAND_POINT[0] - BRIDGE_MAINLAND_POINT[0],
    BRIDGE_ISLAND_POINT[1] - BRIDGE_MAINLAND_POINT[1],
)
BRIDGE_VECTOR_LENGTH = math.hypot(*BRIDGE_VECTOR)
BRIDGE_UNIT = (
    BRIDGE_VECTOR[0] / BRIDGE_VECTOR_LENGTH,
    BRIDGE_VECTOR[1] / BRIDGE_VECTOR_LENGTH,
)
BRIDGE_ROTATION = math.atan2(BRIDGE_VECTOR[1], BRIDGE_VECTOR[0])
BRIDGE_ISLAND_EXTENSION = 0.16
BRIDGE_ISLAND_RISE = 0.055


LANDMARK_SPECS = [
    {
        "name": "Landmark_Petit_Pont_Chatelet_Trellis",
        "path": MODEL_DIR / "petit_pont_petit_chatelet.glb",
        "location": (-2.256, 0.120, -0.200),
        "rotation": BRIDGE_ROTATION,
        "dimensions": (0.95, 0.52, 0.72),
        "start": 930,
        "duration": 28,
        "death_start": 2175,
        "death_duration": 28,
        "active_eras": [1, 2],
        "clearance": 0.035,
        "site": "Petit-Pont / Petit Chatelet",
    },
    {
        "name": "Landmark_Sainte_Chapelle_Trellis",
        "path": MODEL_DIR / "sainte_chapelle.glb",
        "location": (-3.59, 2.70, 0.055),
        "rotation": math.radians(-31.5),
        "dimensions": (0.96, 0.48, 0.90),
        "start": 970,
        "duration": 28,
        "death_start": None,
        "death_duration": None,
        "active_eras": [1, 2, 3, 4],
        "clearance": 0.045,
        "site": "Sainte-Chapelle",
    },
    {
        "name": "Landmark_Saint_Germain_des_Pres_Trellis",
        "path": MODEL_DIR / "saint_germain_des_pres.glb",
        "location": (-12.15, 0.95, 0.055),
        "rotation": math.radians(84.0),
        "dimensions": (1.35, 1.65, 0.98),
        "start": 1010,
        "duration": 28,
        "death_start": 2175,
        "death_duration": 28,
        "active_eras": [1, 2],
        "clearance": 0.180,
        "site": "Saint-Germain-des-Pres abbey",
    },
    {
        "name": "Landmark_Tour_du_Temple_Trellis",
        "path": MODEL_DIR / "tour_du_temple.glb",
        "location": (8.20, 12.45, 0.055),
        "rotation": math.radians(-8.0),
        "dimensions": (0.42, 0.48, 0.58),
        "start": 1050,
        "duration": 28,
        "death_start": 2175,
        "death_duration": 28,
        "active_eras": [1, 2],
        "clearance": 0.050,
        "site": "Tour du Temple",
    },
]


BRIDGE_MAINLAND_ROAD_SPEC = {
    "name": "Petit_Pont_Mainland_Road_Clearance",
    "location": (
        LANDMARK_SPECS[0]["location"][0] - BRIDGE_UNIT[0] * 0.61,
        LANDMARK_SPECS[0]["location"][1] - BRIDGE_UNIT[1] * 0.61,
        0.055,
    ),
    "rotation": BRIDGE_ROTATION,
    "dimensions": (0.44, 0.20, 0.10),
    "active_eras": [1, 2],
    "clearance": 0.018,
}
BRIDGE_ISLAND_ROAD_SPEC = {
    "name": "Petit_Pont_Island_Road_Clearance",
    "location": (
        LANDMARK_SPECS[0]["location"][0] + BRIDGE_UNIT[0] * 0.57,
        LANDMARK_SPECS[0]["location"][1] + BRIDGE_UNIT[1] * 0.57,
        0.055,
    ),
    "rotation": BRIDGE_ROTATION,
    "dimensions": (0.36, 0.22, 0.10),
    "active_eras": [1, 2],
    "clearance": 0.020,
}
SITE_CLEARANCE_SPECS = [
    *LANDMARK_SPECS,
    BRIDGE_MAINLAND_ROAD_SPEC,
    BRIDGE_ISLAND_ROAD_SPEC,
]


BUILDING_PREFIXES = {
    1: (
        "Buildings_Medieval_State_Chunk_",
        "Island_Cite_1_State_Chunk_",
        "Island_Saint_Louis_1_State_Chunk_",
    ),
    2: (
        "Buildings_1700_State_Chunk_",
        "Island_Cite_2_State_Chunk_",
        "Island_Saint_Louis_2_State_Chunk_",
    ),
    3: (
        "Buildings_1850_State_Chunk_",
        "Island_Cite_3_State_Chunk_",
        "Island_Saint_Louis_3_State_Chunk_",
    ),
    4: (
        "Buildings_Modern_State_Chunk_",
        "Island_Cite_4_State_Chunk_",
        "Island_Saint_Louis_4_State_Chunk_",
    ),
}


OLD_CITE_GATE_PARTS = [
    "Cite_Gate_v21_05_00_Lintel",
    "Cite_Gate_v21_05_00_Roof_0",
    "Cite_Gate_v21_05_00_Roof_1",
    "Cite_Gate_v21_05_00_Tower_0",
    "Cite_Gate_v21_05_00_Tower_1",
]


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(args)


def descendants(root):
    result = []
    stack = list(root.children)
    while stack:
        child = stack.pop()
        result.append(child)
        stack.extend(child.children)
    return result


def remove_tree(root):
    for obj in reversed(descendants(root)):
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    if root.name in bpy.data.objects:
        bpy.data.objects.remove(root, do_unlink=True)


def remove_named_tree(name):
    root = bpy.data.objects.get(name)
    if root is not None:
        remove_tree(root)


def hide_curve(obj):
    action = getattr(getattr(obj, "animation_data", None), "action", None)
    if action is None:
        return None
    return next((curve for curve in action.fcurves if curve.data_path == "hide_render"), None)


def set_constant_hide_keys(obj):
    curve = hide_curve(obj)
    if curve is None:
        return
    for keyframe in curve.keyframe_points:
        keyframe.interpolation = "CONSTANT"


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


def insert_hide_key(obj, frame, hidden):
    bpy.context.scene.frame_set(frame)
    obj.hide_render = hidden
    obj.keyframe_insert(data_path="hide_render", frame=frame)


def animate_lifecycle(root, start_frame, duration, death_start=None, death_duration=None):
    targets = [root, *descendants(root)]
    for target in targets:
        insert_hide_key(target, 1, True)
        insert_hide_key(target, start_frame - 1, True)
        insert_hide_key(target, start_frame, False)
        if death_start is not None and death_duration is not None:
            insert_hide_key(target, death_start + death_duration, False)
            insert_hide_key(target, death_start + death_duration + 1, True)
        set_constant_hide_keys(target)

    final_location = tuple(root.location)
    final_scale = tuple(root.scale)
    peak_frame = start_frame + max(3, duration - 2)
    root.location = (final_location[0], final_location[1], final_location[2] - 0.18)
    root.scale = (final_scale[0], final_scale[1], 0.012)
    root.keyframe_insert(data_path="location", frame=start_frame)
    root.keyframe_insert(data_path="scale", frame=start_frame)
    root.location = (final_location[0], final_location[1], final_location[2] + 0.012)
    root.scale = (final_scale[0], final_scale[1], 1.045)
    root.keyframe_insert(data_path="location", frame=peak_frame)
    root.keyframe_insert(data_path="scale", frame=peak_frame)
    root.location = final_location
    root.scale = final_scale
    root.keyframe_insert(data_path="location", frame=start_frame + duration)
    root.keyframe_insert(data_path="scale", frame=start_frame + duration)

    if death_start is not None and death_duration is not None:
        root.location = final_location
        root.scale = final_scale
        root.keyframe_insert(data_path="location", frame=death_start)
        root.keyframe_insert(data_path="scale", frame=death_start)
        root.location = (final_location[0], final_location[1], final_location[2] - 0.18)
        root.scale = (final_scale[0], final_scale[1], 0.018)
        root.keyframe_insert(data_path="location", frame=death_start + death_duration)
        root.keyframe_insert(data_path="scale", frame=death_start + death_duration)
        root.location = final_location
        root.scale = final_scale

    set_motion_easing(root)


def mesh_world_bounds(meshes):
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector(
        (
            min(point.x for point in corners),
            min(point.y for point in corners),
            min(point.z for point in corners),
        )
    )
    maximum = Vector(
        (
            max(point.x for point in corners),
            max(point.y for point in corners),
            max(point.z for point in corners),
        )
    )
    return minimum, maximum


def set_principled_input(node, name, value):
    socket = node.inputs.get(name)
    if socket is not None and not socket.is_linked:
        socket.default_value = value


def polish_materials(materials, prefix):
    for index, material in enumerate(materials):
        if material is None:
            continue
        material.name = f"{prefix}_Material_{index:02d}"
        material.diffuse_color[3] = 1.0
        if not material.use_nodes or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            set_principled_input(node, "Metallic", 0.0)
            set_principled_input(node, "Roughness", 0.72)
            set_principled_input(node, "Specular IOR Level", 0.25)
            set_principled_input(node, "Coat Weight", 0.0)


def smoothstep(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3.0 - 2.0 * value)


def warp_bridge_to_island(root, meshes):
    bpy.context.view_layer.update()
    inverse_root = root.matrix_world.inverted()
    transforms = {
        obj: inverse_root @ obj.matrix_world
        for obj in meshes
    }
    root_points = [
        transforms[obj] @ vertex.co
        for obj in meshes
        for vertex in obj.data.vertices
    ]
    maximum_x = max(point.x for point in root_points)
    stretch_start = 0.08
    rise_start = 0.30

    for obj in meshes:
        transform = transforms[obj]
        inverse_transform = transform.inverted()
        for vertex in obj.data.vertices:
            point = transform @ vertex.co
            original_x = point.x
            stretch_progress = smoothstep(
                (original_x - stretch_start) / max(1e-6, maximum_x - stretch_start)
            )
            rise_progress = smoothstep(
                (original_x - rise_start) / max(1e-6, maximum_x - rise_start)
            )
            point.x += BRIDGE_ISLAND_EXTENSION * stretch_progress
            point.z += BRIDGE_ISLAND_RISE * rise_progress
            vertex.co = inverse_transform @ point
        obj.data.update()

    root["island_extension"] = BRIDGE_ISLAND_EXTENSION
    root["island_rise"] = BRIDGE_ISLAND_RISE
    root["warp_stretch_start"] = stretch_start
    root["warp_rise_start"] = rise_start
    return {
        "extension": BRIDGE_ISLAND_EXTENSION,
        "rise": BRIDGE_ISLAND_RISE,
        "stretch_start": stretch_start,
        "rise_start": rise_start,
        "original_maximum_x": maximum_x,
    }


def import_landmark(spec):
    path = spec["path"]
    if not path.is_file():
        raise FileNotFoundError(path)

    before_objects = set(bpy.data.objects)
    before_materials = set(bpy.data.materials)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    imported = [obj for obj in bpy.data.objects if obj not in before_objects]
    imported_materials = [material for material in bpy.data.materials if material not in before_materials]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh found in {path}")

    minimum, maximum = mesh_world_bounds(meshes)
    source_dimensions = maximum - minimum
    source_center = (minimum + maximum) * 0.5

    root = bpy.data.objects.new(spec["name"], None)
    root.empty_display_type = "PLAIN_AXES"
    bpy.context.collection.objects.link(root)
    root.location = spec["location"]
    root.rotation_euler[2] = spec["rotation"]

    model = bpy.data.objects.new(f"{spec['name']}_Model", None)
    model.empty_display_type = "CUBE"
    bpy.context.collection.objects.link(model)
    model.parent = root

    for obj in imported:
        if obj.parent is None:
            world_matrix = obj.matrix_world.copy()
            obj.parent = model
            obj.matrix_world = world_matrix

    target_dimensions = Vector(spec["dimensions"])
    scale = Vector(
        (
            target_dimensions.x / max(0.0001, source_dimensions.x),
            target_dimensions.y / max(0.0001, source_dimensions.y),
            target_dimensions.z / max(0.0001, source_dimensions.z),
        )
    )
    model.scale = scale
    model.location = (
        -source_center.x * scale.x,
        -source_center.y * scale.y,
        -minimum.z * scale.z,
    )

    for index, obj in enumerate(meshes):
        obj.name = f"{spec['name']}_Mesh_{index:02d}"
        obj["source_glb"] = str(path.resolve())
    polish_materials(imported_materials, spec["name"])

    root["source_glb"] = str(path.resolve())
    root["historical_site"] = spec["site"]
    root["target_dimensions"] = tuple(target_dimensions)
    root["active_eras"] = tuple(spec["active_eras"])
    root["first_era"] = min(spec["active_eras"])
    root["last_era"] = max(spec["active_eras"])
    if spec["name"] == "Landmark_Petit_Pont_Chatelet_Trellis":
        root["bridge_warp"] = json.dumps(warp_bridge_to_island(root, meshes))
    animate_lifecycle(
        root,
        spec["start"],
        spec["duration"],
        spec["death_start"],
        spec["death_duration"],
    )
    return root, meshes, source_dimensions


def rotated_box_corners(spec, extra_margin=0.0):
    half_x = spec["dimensions"][0] * 0.5 + spec["clearance"] + extra_margin
    half_y = spec["dimensions"][1] * 0.5 + spec["clearance"] + extra_margin
    center_x, center_y = spec["location"][:2]
    cos_r = math.cos(spec["rotation"])
    sin_r = math.sin(spec["rotation"])
    corners = []
    for local_x, local_y in ((-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)):
        corners.append(
            (
                center_x + local_x * cos_r - local_y * sin_r,
                center_y + local_x * sin_r + local_y * cos_r,
            )
        )
    return corners


def projection_interval(points, axis):
    values = [point[0] * axis[0] + point[1] * axis[1] for point in points]
    return min(values), max(values)


def intervals_overlap(first, second):
    return first[1] >= second[0] and second[1] >= first[0]


def aabb_intersects_spec(min_x, max_x, min_y, max_y, spec, extra_margin=0.0):
    aabb = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
    box = rotated_box_corners(spec, extra_margin)
    cos_r = math.cos(spec["rotation"])
    sin_r = math.sin(spec["rotation"])
    axes = ((1.0, 0.0), (0.0, 1.0), (cos_r, sin_r), (-sin_r, cos_r))
    return all(
        intervals_overlap(projection_interval(aabb, axis), projection_interval(box, axis))
        for axis in axes
    )


def object_world_xy_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        min(point.x for point in corners),
        max(point.x for point in corners),
        min(point.y for point in corners),
        max(point.y for point in corners),
    )


def face_components(bm):
    unvisited = set(bm.faces)
    while unvisited:
        seed = unvisited.pop()
        component = [seed]
        queue = deque([seed])
        while queue:
            face = queue.popleft()
            for edge in face.edges:
                for neighbor in edge.link_faces:
                    if neighbor in unvisited:
                        unvisited.remove(neighbor)
                        component.append(neighbor)
                        queue.append(neighbor)
        yield component


def component_world_xy_bounds(component, matrix_world):
    vertices = {vertex for face in component for vertex in face.verts}
    points = [matrix_world @ vertex.co for vertex in vertices]
    return (
        min(point.x for point in points),
        max(point.x for point in points),
        min(point.y for point in points),
        max(point.y for point in points),
    )


def polygon_axes(points):
    axes = []
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        edge_x = following[0] - point[0]
        edge_y = following[1] - point[1]
        length = math.hypot(edge_x, edge_y)
        if length <= 1e-8:
            continue
        axes.append((-edge_y / length, edge_x / length))
    return axes


def convex_polygons_intersect(first, second, gap=0.0):
    for axis in [*polygon_axes(first), *polygon_axes(second)]:
        first_interval = projection_interval(first, axis)
        second_interval = projection_interval(second, axis)
        if first_interval[1] + gap < second_interval[0]:
            return False
        if second_interval[1] + gap < first_interval[0]:
            return False
    return True


def point_in_convex_polygon(point, polygon):
    sign = None
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        cross = (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (point[0] - start[0])
        if abs(cross) <= 1e-8:
            continue
        current_sign = cross > 0.0
        if sign is None:
            sign = current_sign
        elif current_sign != sign:
            return False
    return True


def point_segment_distance(point, start, end):
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    length_sq = delta_x * delta_x + delta_y * delta_y
    if length_sq <= 1e-12:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    progress = ((point[0] - start[0]) * delta_x + (point[1] - start[1]) * delta_y) / length_sq
    progress = min(1.0, max(0.0, progress))
    closest = (start[0] + delta_x * progress, start[1] + delta_y * progress)
    return math.hypot(point[0] - closest[0], point[1] - closest[1])


def point_polygon_distance(point, polygon):
    if point_in_convex_polygon(point, polygon):
        return 0.0
    return min(
        point_segment_distance(point, polygon[index], polygon[(index + 1) % len(polygon)])
        for index in range(len(polygon))
    )


def delete_bmesh_faces(obj, bm, faces_to_delete, removed_items):
    mesh = obj.data
    before_faces = len(mesh.polygons)
    before_vertices = len(mesh.vertices)
    bmesh.ops.delete(bm, geom=list(faces_to_delete), context="FACES")
    loose_edges = [edge for edge in bm.edges if not edge.link_faces]
    if loose_edges:
        bmesh.ops.delete(bm, geom=loose_edges, context="EDGES")
    loose_vertices = [vertex for vertex in bm.verts if not vertex.link_faces and not vertex.link_edges]
    if loose_vertices:
        bmesh.ops.delete(bm, geom=loose_vertices, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    result = {
        "object": obj.name,
        "removed_components": removed_items,
        "removed_buildings": removed_items,
        "removed_faces": before_faces - len(mesh.polygons),
        "removed_vertices": before_vertices - len(mesh.vertices),
        "remaining_faces": len(mesh.polygons),
    }
    if not mesh.polygons:
        bpy.data.objects.remove(obj, do_unlink=True)
        result["object_removed"] = True
    else:
        result["object_removed"] = False
    return result


def matching_specs_for_object(obj, specs, extra_margin=0.0):
    coarse_bounds = object_world_xy_bounds(obj)
    return [
        spec
        for spec in specs
        if aabb_intersects_spec(*coarse_bounds, spec, extra_margin=extra_margin)
    ]


def clear_medieval_house_groups_from_object(obj, specs):
    matching_specs = matching_specs_for_object(obj, specs)
    if not matching_specs:
        return None
    first_house_slot = next(
        (
            index
            for index, material in enumerate(obj.data.materials)
            if material is not None and material.name.startswith("House_v37_")
        ),
        None,
    )
    if first_house_slot is None:
        return clear_components_from_object(obj, matching_specs)
    if obj.data.users > 1:
        obj.data = obj.data.copy()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    groups = {}
    for face in bm.faces:
        material_index = face.material_index
        if material_index < first_house_slot or material_index >= len(obj.data.materials):
            continue
        material = obj.data.materials[material_index]
        if material is None or not material.name.startswith("House_v37_"):
            continue
        group_index = (material_index - first_house_slot) // 8
        groups.setdefault(group_index, []).append(face)

    matrix_world = obj.matrix_world.copy()
    faces_to_delete = set()
    removed_houses = 0
    for faces in groups.values():
        bounds = component_world_xy_bounds(faces, matrix_world)
        if any(aabb_intersects_spec(*bounds, spec) for spec in matching_specs):
            faces_to_delete.update(faces)
            removed_houses += 1
    if not faces_to_delete:
        bm.free()
        return None
    return delete_bmesh_faces(obj, bm, faces_to_delete, removed_houses)


def clear_procedural_buildings_from_object(obj, specs):
    matching_specs = matching_specs_for_object(obj, specs)
    if not matching_specs:
        return None
    if obj.data.users > 1:
        obj.data = obj.data.copy()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    matrix_world = obj.matrix_world.copy()
    minimum_z = min(vertex.co.z for vertex in bm.verts)

    ground_faces = []
    ground_polygons = []
    for face in bm.faces:
        if not face.verts or max(abs(vertex.co.z - minimum_z) for vertex in face.verts) > 1e-5:
            continue
        polygon = [(point.x, point.y) for point in (matrix_world @ vertex.co for vertex in face.verts)]
        if len(polygon) < 3:
            continue
        ground_faces.append(face)
        ground_polygons.append(polygon)
    if not ground_faces:
        bm.free()
        return clear_components_from_object(obj, matching_specs)

    parents = list(range(len(ground_faces)))

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

    for first in range(len(ground_polygons)):
        for second in range(first + 1, len(ground_polygons)):
            if convex_polygons_intersect(ground_polygons[first], ground_polygons[second], gap=0.001):
                union(first, second)

    clusters = {}
    for index, polygon in enumerate(ground_polygons):
        clusters.setdefault(find(index), []).append(polygon)
    spec_polygons = [rotated_box_corners(spec) for spec in matching_specs]
    marked_clusters = {
        cluster_id
        for cluster_id, polygons in clusters.items()
        if any(
            convex_polygons_intersect(polygon, spec_polygon)
            for polygon in polygons
            for spec_polygon in spec_polygons
        )
    }
    if not marked_clusters:
        bm.free()
        return None

    faces_to_delete = set()
    cluster_items = list(clusters.items())
    for face in bm.faces:
        center = matrix_world @ face.calc_center_median()
        point = (center.x, center.y)
        closest_cluster = min(
            cluster_items,
            key=lambda item: min(point_polygon_distance(point, polygon) for polygon in item[1]),
        )[0]
        if closest_cluster in marked_clusters:
            faces_to_delete.add(face)
    return delete_bmesh_faces(obj, bm, faces_to_delete, len(marked_clusters))


def clear_components_from_object(obj, specs, extra_margin=0.0):
    coarse_bounds = object_world_xy_bounds(obj)
    matching_specs = [
        spec
        for spec in specs
        if aabb_intersects_spec(*coarse_bounds, spec, extra_margin=extra_margin)
    ]
    if not matching_specs:
        return None

    if obj.data.users > 1:
        obj.data = obj.data.copy()
    mesh = obj.data
    before_faces = len(mesh.polygons)
    before_vertices = len(mesh.vertices)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    matrix_world = obj.matrix_world.copy()
    faces_to_delete = set()
    removed_components = 0

    for component in face_components(bm):
        bounds = component_world_xy_bounds(component, matrix_world)
        if any(
            aabb_intersects_spec(*bounds, spec, extra_margin=extra_margin)
            for spec in matching_specs
        ):
            faces_to_delete.update(component)
            removed_components += 1

    if not faces_to_delete:
        bm.free()
        return None

    bmesh.ops.delete(bm, geom=list(faces_to_delete), context="FACES")
    loose_edges = [edge for edge in bm.edges if not edge.link_faces]
    if loose_edges:
        bmesh.ops.delete(bm, geom=loose_edges, context="EDGES")
    loose_vertices = [vertex for vertex in bm.verts if not vertex.link_faces and not vertex.link_edges]
    if loose_vertices:
        bmesh.ops.delete(bm, geom=loose_vertices, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    result = {
        "object": obj.name,
        "removed_components": removed_components,
        "removed_faces": before_faces - len(mesh.polygons),
        "removed_vertices": before_vertices - len(mesh.vertices),
        "remaining_faces": len(mesh.polygons),
    }
    if not mesh.polygons:
        bpy.data.objects.remove(obj, do_unlink=True)
        result["object_removed"] = True
    else:
        result["object_removed"] = False
    return result


def clear_spatial_clusters_from_object(obj, specs, extra_margin=0.0):
    matching_specs = matching_specs_for_object(obj, specs, extra_margin=extra_margin)
    if not matching_specs:
        return None
    if obj.data.users > 1:
        obj.data = obj.data.copy()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    matrix_world = obj.matrix_world.copy()
    components = list(face_components(bm))
    bounds = [component_world_xy_bounds(component, matrix_world) for component in components]
    parents = list(range(len(components)))

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

    gap = 0.003
    for first in range(len(bounds)):
        first_bounds = bounds[first]
        for second in range(first + 1, len(bounds)):
            second_bounds = bounds[second]
            if first_bounds[1] + gap < second_bounds[0] or second_bounds[1] + gap < first_bounds[0]:
                continue
            if first_bounds[3] + gap < second_bounds[2] or second_bounds[3] + gap < first_bounds[2]:
                continue
            union(first, second)

    clusters = {}
    cluster_bounds = {}
    for index, component in enumerate(components):
        root = find(index)
        clusters.setdefault(root, []).extend(component)
        current = cluster_bounds.get(root)
        component_bounds = bounds[index]
        if current is None:
            cluster_bounds[root] = list(component_bounds)
        else:
            current[0] = min(current[0], component_bounds[0])
            current[1] = max(current[1], component_bounds[1])
            current[2] = min(current[2], component_bounds[2])
            current[3] = max(current[3], component_bounds[3])

    marked_clusters = {
        root
        for root, cluster_bound in cluster_bounds.items()
        if any(
            aabb_intersects_spec(*cluster_bound, spec, extra_margin=extra_margin)
            for spec in matching_specs
        )
    }
    if not marked_clusters:
        bm.free()
        return None
    faces_to_delete = {
        face
        for root in marked_clusters
        for face in clusters[root]
    }
    return delete_bmesh_faces(obj, bm, faces_to_delete, len(marked_clusters))


def clear_site_geometry():
    report = {"buildings": {}, "forest": {}}
    for era, frame in FULL_STATE_FRAMES.items():
        specs = [spec for spec in SITE_CLEARANCE_SPECS if era in spec["active_eras"]]
        if not specs:
            continue
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()

        building_candidates = [
            obj
            for obj in list(bpy.data.objects)
            if obj.type == "MESH" and obj.name.startswith(BUILDING_PREFIXES[era])
        ]
        building_results = []
        for obj in building_candidates:
            result = clear_procedural_buildings_from_object(obj, specs)
            if result is not None:
                building_results.append(result)
        report["buildings"][str(era)] = building_results

        forest_prefix = f"Forest_Cleared_{era}_Chunk_"
        forest_candidates = [
            obj
            for obj in list(bpy.data.objects)
            if obj.type == "MESH" and obj.name.startswith(forest_prefix)
        ]
        forest_results = []
        for obj in forest_candidates:
            result = clear_spatial_clusters_from_object(obj, specs, extra_margin=0.02)
            if result is not None:
                forest_results.append(result)
        report["forest"][str(era)] = forest_results
    return report


def override_hidden_interval(root, start_frame, end_frame):
    targets = [root, *descendants(root)]
    for target in targets:
        insert_hide_key(target, start_frame - 1, False)
        insert_hide_key(target, start_frame, True)
        insert_hide_key(target, end_frame - 1, True)
        insert_hide_key(target, end_frame, False)
        set_constant_hide_keys(target)


def hide_from_frame(obj, start_frame):
    bpy.context.scene.frame_set(start_frame - 1)
    before_hidden = bool(obj.hide_render)
    curve = hide_curve(obj)
    if curve is not None:
        for point in curve.keyframe_points:
            if point.co.x >= start_frame:
                point.co[1] = 1.0
        curve.update()
    insert_hide_key(obj, start_frame - 1, before_hidden)
    insert_hide_key(obj, start_frame, True)
    set_constant_hide_keys(obj)


def configure_bridge_replacement():
    bridge_spec = LANDMARK_SPECS[0]
    replacement_end = bridge_spec["death_start"] + bridge_spec["death_duration"] + 1
    old_bridge = bpy.data.objects.get("OSM_Bridge_744835294")
    if old_bridge is None:
        raise RuntimeError("OSM bridge 744835294 was not found")
    override_hidden_interval(old_bridge, bridge_spec["start"], replacement_end)

    hidden_gate_parts = []
    for name in OLD_CITE_GATE_PARTS:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        hide_from_frame(obj, bridge_spec["start"])
        hidden_gate_parts.append(name)
    return {
        "old_bridge": old_bridge.name,
        "replacement_start": bridge_spec["start"],
        "replacement_end": replacement_end,
        "hidden_gate_parts": hidden_gate_parts,
        "island_point": list(BRIDGE_ISLAND_POINT),
        "mainland_point": list(BRIDGE_MAINLAND_POINT),
        "rotation_degrees": math.degrees(BRIDGE_ROTATION),
    }


def placement_report(spec, root, meshes, source_dimensions):
    bpy.context.scene.frame_set(spec["start"] + spec["duration"] + 2)
    bpy.context.view_layer.update()
    minimum, maximum = mesh_world_bounds(meshes)
    return {
        "name": spec["name"],
        "site": spec["site"],
        "source": str(spec["path"].resolve()),
        "source_dimensions": list(source_dimensions),
        "target_dimensions": list(spec["dimensions"]),
        "placed_bounds_min": list(minimum),
        "placed_bounds_max": list(maximum),
        "location": list(root.location),
        "rotation_degrees": math.degrees(root.rotation_euler[2]),
        "start_frame": spec["start"],
        "duration_frames": spec["duration"],
        "death_start": spec["death_start"],
        "death_duration": spec["death_duration"],
        "active_eras": list(spec["active_eras"]),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "triangles": sum(len(obj.data.polygons) for obj in meshes),
    }


def summarize_clearance(clearance_report):
    summary = {}
    for category, by_era in clearance_report.items():
        summary[category] = {}
        for era, entries in by_era.items():
            summary[category][era] = {
                "objects_modified": len(entries),
                "components_removed": sum(entry["removed_components"] for entry in entries),
                "faces_removed": sum(entry["removed_faces"] for entry in entries),
                "vertices_removed": sum(entry["removed_vertices"] for entry in entries),
            }
    return summary


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    source_blend = bpy.data.filepath

    for spec in LANDMARK_SPECS:
        remove_named_tree(spec["name"])

    bridge_report = configure_bridge_replacement()
    imported = []
    for spec in LANDMARK_SPECS:
        root, meshes, source_dimensions = import_landmark(spec)
        imported.append((spec, root, meshes, source_dimensions))

    clearance_report = clear_site_geometry()
    landmarks = [placement_report(*entry) for entry in imported]
    report = {
        "source_blend": source_blend,
        "output_blend": str(args.output),
        "bridge_replacement": bridge_report,
        "clearance_summary": summarize_clearance(clearance_report),
        "clearance_details": clearance_report,
        "landmarks": landmarks,
    }

    bpy.context.scene.frame_set(1450)
    bpy.context.view_layer.update()
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
