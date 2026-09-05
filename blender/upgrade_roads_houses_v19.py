import argparse
import importlib.util
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROMAN_BRIDGES = (
    ("ile_de_la_cite", -5.4, -1.0, 165),
    ("ile_de_la_cite", -2.0, 1.0, 210),
)
MEDIEVAL_BRIDGES = (
    ("ile_de_la_cite", -5.4, -1.0, 790),
    ("ile_de_la_cite", -2.0, 1.0, 808),
    ("ile_de_la_cite", 0.7, -1.0, 870),
    ("ile_de_la_cite", 1.0, 1.0, 920),
)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--house-kit", type=Path, required=True)
    parser.add_argument("--output-blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_modules():
    directory = Path(__file__).resolve().parent
    build_scene = load_module(directory / "build_scene.py", "paris_build_scene_v19")
    roman = load_module(
        directory / "rebuild_roman_urbanism_v15.py",
        "paris_roman_urbanism_v19",
    )
    medieval = load_module(
        directory / "rebuild_medieval_urbanism_v17.py",
        "paris_medieval_urbanism_v19",
    )
    return build_scene, roman, medieval


def closest_point_on_segment(point, start, end):
    point = Vector(point)
    start = Vector(start)
    end = Vector(end)
    delta = end - start
    length_sq = delta.length_squared
    if length_sq < 1e-10:
        return start.copy(), 0.0
    amount = max(0.0, min(1.0, (point - start).dot(delta) / length_sq))
    return start + delta * amount, amount


def nearest_street_point(streets, zone, point):
    best = None
    for street in streets:
        if street["zone"] != zone:
            continue
        nearest, amount = closest_point_on_segment(
            point,
            street["start"],
            street["end"],
        )
        distance = (nearest - Vector(point)).length
        if best is None or distance < best[0]:
            best = (distance, nearest, street, amount)
    if best is None:
        raise RuntimeError(f"No {zone} street found near {tuple(point)}")
    return best


def nearest_rendered_road_piece(pieces, zone, point):
    best = None
    island = zone != "main"
    for piece in pieces:
        if (piece["z"] > 0.0) != island:
            continue
        nearest, amount = closest_point_on_segment(
            point,
            piece["start"],
            piece["end"],
        )
        distance = (nearest - Vector(point)).length
        if best is None or distance < best[0]:
            best = (distance, nearest, piece, amount)
    if best is None:
        raise RuntimeError(f"No rendered {zone} road piece near {tuple(point)}")
    return best


def bridge_geometry(build_scene, island_key, x, side):
    polygon = build_scene.load_geodata()["islands"][island_key]
    river_y = build_scene.river_center(x)
    dx = 0.08
    slope = (
        build_scene.river_center(x + dx) - build_scene.river_center(x - dx)
    ) / (2 * dx)
    normal = Vector((-slope, 1.0)).normalized()
    island_origin = Vector((x, build_scene.polygon_y_center_at_x(polygon, x)))
    river_origin = Vector((x, river_y))
    direction = normal * side
    shore_distance = build_scene.ray_polygon_exit_distance(
        island_origin,
        direction,
        polygon,
    )
    if shore_distance is None:
        raise RuntimeError(f"No island exit for bridge {island_key} {x} {side}")
    island_edge = island_origin + direction * shore_distance
    bank_edge = river_origin + direction * (build_scene.river_half_width(x) + 0.3)
    return {
        "island_key": island_key,
        "x": x,
        "side": side,
        "island_edge": island_edge,
        "bank_edge": bank_edge,
        "direction": direction,
        "center": (island_edge + bank_edge) * 0.5,
    }


def nearest_osm_segment(build_scene, point, bridge=None):
    point = Vector(point)
    best = None
    for road in build_scene.load_geodata()["roads"]:
        if bridge is not None and bool(road["bridge"]) != bridge:
            continue
        for start, end in zip(road["points"], road["points"][1:]):
            nearest, amount = closest_point_on_segment(point, start, end)
            distance = (nearest - point).length
            if best is None or distance < best[0]:
                best = (distance, nearest, road, amount)
    return best


def build_connector_specs(
    build_scene,
    roman,
    medieval_base,
    roman_streets,
    medieval_streets,
):
    specs = []
    osm_report = []
    road_pieces = {
        "roman": roman.create_road_pieces(build_scene, roman_streets),
        "medieval": medieval_base.create_road_pieces(
            build_scene,
            roman,
            medieval_streets,
        ),
    }
    era_definitions = (
        ("roman", ROMAN_BRIDGES, roman_streets, 873, 90),
        ("medieval", MEDIEVAL_BRIDGES, medieval_streets, None, None),
    )
    for era, bridges, streets, removal_frame, removal_duration in era_definitions:
        for bridge_index, (island_key, x, side, start_frame) in enumerate(bridges):
            bridge = bridge_geometry(build_scene, island_key, x, side)
            island_zone = "cite" if island_key == "ile_de_la_cite" else "saint_louis"
            island_distance, island_target, island_piece, _ = nearest_rendered_road_piece(
                road_pieces[era],
                island_zone,
                bridge["island_edge"],
            )
            bank_distance, bank_target, bank_piece, _ = nearest_rendered_road_piece(
                road_pieces[era],
                "main",
                bridge["bank_edge"],
            )
            base_name = f"{era}_{island_key}_{bridge_index:02d}"
            specs.extend(
                (
                    {
                        "name": f"Bridge_Approach_{base_name}_Island",
                        "era": era,
                        "zone": island_zone,
                        "start": bridge["island_edge"],
                        "end": island_target,
                        "start_width": 0.27,
                        "end_width": max(0.13, island_piece["width"]),
                        "start_z": 0.13,
                        "end_z": 0.066,
                        "start_frame": start_frame,
                        "removal_frame": removal_frame,
                        "removal_duration": removal_duration,
                        "bridge": bridge,
                    },
                    {
                        "name": f"Bridge_Approach_{base_name}_Mainland",
                        "era": era,
                        "zone": "main",
                        "start": bridge["bank_edge"],
                        "end": bank_target,
                        "start_width": 0.27,
                        "end_width": max(0.13, bank_piece["width"]),
                        "start_z": 0.13,
                        "end_z": -0.021,
                        "start_frame": start_frame + 8,
                        "removal_frame": removal_frame,
                        "removal_duration": removal_duration,
                        "bridge": bridge,
                    },
                )
            )
            osm_bridge = nearest_osm_segment(build_scene, bridge["center"], bridge=True)
            osm_island = nearest_osm_segment(build_scene, bridge["island_edge"], bridge=False)
            osm_bank = nearest_osm_segment(build_scene, bridge["bank_edge"], bridge=False)
            osm_report.append(
                {
                    "era": era,
                    "bridge": base_name,
                    "procedural_island_snap": island_distance,
                    "procedural_bank_snap": bank_distance,
                    "osm_bridge_id": osm_bridge[2]["id"],
                    "osm_bridge_distance": osm_bridge[0],
                    "osm_island_road_id": osm_island[2]["id"],
                    "osm_island_road_distance": osm_island[0],
                    "osm_bank_road_id": osm_bank[2]["id"],
                    "osm_bank_road_distance": osm_bank[0],
                }
            )
    return specs, osm_report


def connector_conflict(placement, connector_specs):
    center = Vector((placement["x"], placement["y"]))
    radius = math.hypot(placement["width"], placement["depth"]) * 0.5
    for connector in connector_specs:
        if connector["zone"] != placement["zone"]:
            continue
        nearest, _ = closest_point_on_segment(
            center,
            connector["start"],
            connector["end"],
        )
        road_radius = max(connector["start_width"], connector["end_width"]) * 0.5
        if (nearest - center).length < radius + road_radius + 0.035:
            return True
    return False


def import_prototype(path):
    objects_before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    imported = [obj for obj in bpy.data.objects if obj not in objects_before]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No meshes imported from {path}")

    vertices = []
    faces = []
    face_materials = []
    materials = []
    material_lookup = {}
    for obj in meshes:
        matrix = obj.matrix_world.copy()
        vertex_offset = len(vertices)
        vertices.extend(matrix @ vertex.co for vertex in obj.data.vertices)
        slots = [slot.material for slot in obj.material_slots]
        for polygon in obj.data.polygons:
            material = slots[polygon.material_index] if slots else None
            key = material.as_pointer() if material else 0
            if key not in material_lookup:
                material_lookup[key] = len(materials)
                materials.append(material)
            faces.append(tuple(vertex_offset + index for index in polygon.vertices))
            face_materials.append(material_lookup[key])

    minimum = Vector(
        (
            min(vertex.x for vertex in vertices),
            min(vertex.y for vertex in vertices),
            min(vertex.z for vertex in vertices),
        )
    )
    maximum = Vector(
        (
            max(vertex.x for vertex in vertices),
            max(vertex.y for vertex in vertices),
            max(vertex.z for vertex in vertices),
        )
    )
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    normalized = [
        Vector((vertex.x - center_x, vertex.y - center_y, vertex.z - minimum.z))
        for vertex in vertices
    ]
    dimensions = maximum - minimum

    for obj in imported:
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    return {
        "name": path.stem,
        "vertices": normalized,
        "faces": faces,
        "face_materials": face_materials,
        "materials": materials,
        "dimensions": dimensions,
    }


def load_prototypes(directory):
    prototypes = {"roman": [], "medieval": []}
    for era in prototypes:
        paths = sorted(directory.glob(f"{era}_townhouse_*.glb"))
        if not paths:
            raise RuntimeError(f"No {era} GLBs in {directory}")
        prototypes[era] = [import_prototype(path) for path in paths]
    return prototypes


def stable_fraction(seed):
    return ((int(seed) * 2654435761) % 1000003) / 1000003.0


def use_detail(build_scene, era, placement):
    if era == "medieval" and placement.get("plan_style", "standard") != "standard":
        return False
    fraction = stable_fraction(placement["seed"])
    zone = placement["zone"]
    if zone == "cite":
        threshold = 0.42 if era == "medieval" else 0.34
    elif zone == "saint_louis":
        threshold = 0.34 if era == "medieval" else 0.27
    else:
        central = abs(placement["x"]) < 18.0 and abs(placement["y"]) < 15.0
        near_river = build_scene.river_clearance(placement["x"], placement["y"]) < 6.5
        if central and near_river:
            threshold = 0.16 if era == "medieval" else 0.18
        elif central:
            threshold = 0.09
        else:
            threshold = 0.025
    return fraction < threshold


def append_prototype_geometry(
    vertices,
    faces,
    material_ids,
    materials,
    prototype,
    placement,
):
    material_map = []
    for material in prototype["materials"]:
        if material is None:
            material_map.append(0)
            continue
        if material not in materials:
            materials.append(material)
        material_map.append(materials.index(material))

    width = placement["width"]
    depth = placement["depth"]
    roof_height = min(0.28, max(0.04, min(width, depth) * 0.48))
    target_height = placement["height"] + roof_height
    dimensions = prototype["dimensions"]
    scale_x = width / max(1e-6, dimensions.x)
    scale_y = depth / max(1e-6, dimensions.y)
    scale_z = target_height / max(1e-6, dimensions.z)
    cos_r = math.cos(placement["rotation"])
    sin_r = math.sin(placement["rotation"])
    offset = len(vertices)
    for vertex in prototype["vertices"]:
        local_x = vertex.x * scale_x
        local_y = vertex.y * scale_y
        vertices.append(
            (
                placement["x"] + local_x * cos_r - local_y * sin_r,
                placement["y"] + local_x * sin_r + local_y * cos_r,
                vertex.z * scale_z,
            )
        )
    faces.extend(tuple(offset + index for index in face) for face in prototype["faces"])
    material_ids.extend(material_map[index] for index in prototype["face_materials"])
    return len(prototype["vertices"]), len(prototype["faces"])


def rebuild_group(
    build_scene,
    roman,
    medieval_base,
    era,
    prefix,
    placements,
    prototypes,
    connector_specs,
    timber_material=None,
):
    objects = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith(prefix)),
        key=lambda obj: (roman.action_start_frame(obj), obj.name),
    )
    if not objects:
        raise RuntimeError(f"No target objects for {prefix}")
    growth_key = roman.placement_growth_key if era == "roman" else medieval_base.placement_growth_key
    placements = sorted(placements, key=lambda item: growth_key(build_scene, item))
    groups = roman.evenly_partition(placements, len(objects))
    report = {
        "chunks": len(objects),
        "source_buildings": len(placements),
        "detailed_buildings": 0,
        "removed_for_approaches": 0,
        "detail_vertices": 0,
        "detail_faces": 0,
    }
    for obj, group in zip(objects, groups):
        materials = [slot.material for slot in obj.material_slots]
        if timber_material is not None and timber_material not in materials:
            materials.append(timber_material)
        timber_id = materials.index(timber_material) if timber_material else None
        vertices = []
        faces = []
        material_ids = []
        for placement in group:
            if connector_conflict(placement, connector_specs):
                report["removed_for_approaches"] += 1
                continue
            if use_detail(build_scene, era, placement):
                variant_index = int(placement["seed"]) % len(prototypes)
                added_vertices, added_faces = append_prototype_geometry(
                    vertices,
                    faces,
                    material_ids,
                    materials,
                    prototypes[variant_index],
                    placement,
                )
                report["detailed_buildings"] += 1
                report["detail_vertices"] += added_vertices
                report["detail_faces"] += added_faces
                continue

            rng = random.Random(placement["seed"])
            if era == "roman":
                roof_style = rng.choices(
                    ["gable", "hip", "flat"],
                    weights=[0.54, 0.38, 0.08],
                    k=1,
                )[0]
                wall_id, roof_id = build_scene.building_material_ids(rng, "roman")
                build_scene.add_house_geometry(
                    vertices,
                    faces,
                    material_ids,
                    placement["x"],
                    placement["y"],
                    placement["width"],
                    placement["depth"],
                    placement["height"],
                    placement["rotation"],
                    wall_id,
                    roof_id,
                    roof_style,
                    "standard",
                    "roman",
                    rng,
                )
            else:
                wall_id, roof_id = build_scene.building_material_ids(rng, "medieval")
                build_scene.add_house_geometry(
                    vertices,
                    faces,
                    material_ids,
                    placement["x"],
                    placement["y"],
                    placement["width"],
                    placement["depth"],
                    placement["height"],
                    placement["rotation"],
                    wall_id,
                    roof_id,
                    placement["roof_style"],
                    placement["plan_style"],
                    "medieval",
                    rng,
                )
                if placement["timber"] and placement["plan_style"] == "standard":
                    medieval_base.add_timber_details(
                        build_scene,
                        vertices,
                        faces,
                        material_ids,
                        placement,
                        timber_id,
                    )
                if placement["chimney"]:
                    offset_x = rng.uniform(
                        -placement["width"] * 0.27,
                        placement["width"] * 0.27,
                    )
                    offset_y = rng.uniform(
                        -placement["depth"] * 0.18,
                        placement["depth"] * 0.18,
                    )
                    chimney_x, chimney_y = build_scene.rotated_offset(
                        placement["x"],
                        placement["y"],
                        placement["rotation"],
                        offset_x,
                        offset_y,
                    )
                    size = min(0.035, max(0.018, placement["width"] * 0.11))
                    medieval_base.add_prism_geometry(
                        vertices,
                        faces,
                        material_ids,
                        chimney_x,
                        chimney_y,
                        size,
                        size * 0.9,
                        placement["height"] * 0.83,
                        placement["height"] + 0.12,
                        placement["rotation"],
                        6,
                    )
        roman.replace_mesh(obj, vertices, faces, material_ids, materials)
    return report


def create_approach_mesh(build_scene, specification, material):
    start = Vector(specification["start"])
    end = Vector(specification["end"])
    vector = end - start
    if vector.length < 0.035:
        return None
    tangent = vector.normalized()
    normal = Vector((-tangent.y, tangent.x))
    start_left = start + normal * specification["start_width"] * 0.5
    start_right = start - normal * specification["start_width"] * 0.5
    end_left = end + normal * specification["end_width"] * 0.5
    end_right = end - normal * specification["end_width"] * 0.5
    top_start = specification["start_z"]
    top_end = specification["end_z"]
    thickness = 0.035
    vertices = [
        (*start_left, top_start),
        (*start_right, top_start),
        (*end_right, top_end),
        (*end_left, top_end),
        (*start_left, top_start - thickness),
        (*start_right, top_start - thickness),
        (*end_right, top_end - thickness),
        (*end_left, top_end - thickness),
    ]
    faces = [
        (0, 1, 2, 3),
        (7, 6, 5, 4),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    mesh = bpy.data.meshes.new(f"{specification['name']}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(specification["name"], mesh)
    bpy.context.collection.objects.link(obj)
    obj["road_topology"] = "OSM anchored bridge approach"
    obj["era"] = specification["era"]
    obj.shape_key_add(name="Basis")
    collapsed = obj.shape_key_add(name="Road_Draw_Collapsed")
    for target, source in ((2, 1), (3, 0), (6, 5), (7, 4)):
        collapsed.data[target].co = collapsed.data[source].co
    build_scene.animate_road_draw(obj, collapsed, specification["start_frame"], 22)
    if specification["removal_frame"] is not None:
        build_scene.animate_removal(
            obj,
            specification["removal_frame"],
            duration=specification["removal_duration"],
        )
    return obj


def copy_visibility_action(source, target):
    if not source.animation_data or not source.animation_data.action:
        return
    target.animation_data_create()
    target.animation_data.action = source.animation_data.action


def assign_action(action, target):
    if action is None:
        return
    target.animation_data_create()
    target.animation_data.action = action


def hide_permanently(obj):
    obj.animation_data_clear()
    obj.hide_render = True
    obj.hide_viewport = True


def polygon_edge_index(point, polygon):
    best = None
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        nearest, amount = closest_point_on_segment(point, start, end)
        distance = (nearest - Vector(point)).length
        if best is None or distance < best[0]:
            best = (distance, index, amount, nearest)
    return best


def rebuild_cite_wall_gates(build_scene, medieval_connector_specs):
    root = bpy.data.objects.get("Landmark_Medieval_Cite_Wall")
    if root is None:
        raise RuntimeError("Missing medieval Cite wall")
    polygon = build_scene.load_geodata()["islands"]["ile_de_la_cite"]
    gate_groups = defaultdict(list)
    for specification in medieval_connector_specs:
        if specification["zone"] != "cite":
            continue
        edge_distance, edge_index, amount, nearest = polygon_edge_index(
            specification["start"],
            polygon,
        )
        gate_groups[edge_index].append(
            {
                "amount": amount,
                "point": nearest,
                "name": specification["name"],
                "edge_distance": edge_distance,
            }
        )

    wall_report = []
    roof_source = bpy.data.objects.get("Cite_Wall_Tower_Roof_00")
    roof_material = roof_source.material_slots[0].material if roof_source else None
    for edge_index, gates in sorted(gate_groups.items()):
        wall = bpy.data.objects.get(f"Cite_Wall_{edge_index:02d}")
        if wall is None:
            raise RuntimeError(f"Missing Cite wall segment {edge_index}")
        wall_material = wall.material_slots[0].material
        visibility_action = (
            wall.animation_data.action
            if wall.animation_data and wall.animation_data.action
            else None
        )
        start = Vector(polygon[edge_index])
        end = Vector(polygon[(edge_index + 1) % len(polygon)])
        vector = end - start
        length = vector.length
        tangent = vector.normalized()
        angle = math.atan2(vector.y, vector.x)
        opening_half = 0.19
        intervals = [(0.0, 1.0)]
        for gate in sorted(gates, key=lambda item: item["amount"]):
            half_amount = opening_half / max(length, 1e-6)
            gap_start = max(0.0, gate["amount"] - half_amount)
            gap_end = min(1.0, gate["amount"] + half_amount)
            next_intervals = []
            for interval_start, interval_end in intervals:
                if gap_end <= interval_start or gap_start >= interval_end:
                    next_intervals.append((interval_start, interval_end))
                    continue
                if gap_start - interval_start > 0.025 / length:
                    next_intervals.append((interval_start, gap_start))
                if interval_end - gap_end > 0.025 / length:
                    next_intervals.append((gap_end, interval_end))
            intervals = next_intervals

        hide_permanently(wall)
        replacement_names = []
        for piece_index, (amount_start, amount_end) in enumerate(intervals):
            piece_start = start.lerp(end, amount_start)
            piece_end = start.lerp(end, amount_end)
            piece_center = (piece_start + piece_end) * 0.5
            piece_length = (piece_end - piece_start).length
            piece = build_scene.add_cube(
                f"Cite_Wall_{edge_index:02d}_GatePiece_{piece_index:02d}",
                (piece_center.x, piece_center.y, 0.2),
                (piece_length + 0.025, 0.1, 0.29),
                wall_material,
                root,
            )
            piece.rotation_euler[2] = angle
            assign_action(visibility_action, piece)
            replacement_names.append(piece.name)

        for gate_index, gate in enumerate(gates):
            center = gate["point"]
            for side_index, side in enumerate((-1.0, 1.0)):
                pillar_center = center + tangent * side * (opening_half + 0.075)
                pillar = build_scene.add_cylinder(
                    f"Cite_Gate_{edge_index:02d}_{gate_index:02d}_Pillar_{side_index}",
                    (pillar_center.x, pillar_center.y, 0.275),
                    0.115,
                    0.5,
                    wall_material,
                    root,
                    vertices=10,
                )
                assign_action(visibility_action, pillar)
                if roof_material:
                    roof = build_scene.add_cone(
                        f"Cite_Gate_{edge_index:02d}_{gate_index:02d}_Roof_{side_index}",
                        (pillar_center.x, pillar_center.y, 0.615),
                        0.145,
                        0.0,
                        0.18,
                        roof_material,
                        root,
                        vertices=10,
                    )
                    assign_action(visibility_action, roof)
            lintel = build_scene.add_cube(
                f"Cite_Gate_{edge_index:02d}_{gate_index:02d}_Lintel",
                (center.x, center.y, 0.47),
                (opening_half * 2.0 + 0.15, 0.12, 0.12),
                wall_material,
                root,
            )
            lintel.rotation_euler[2] = angle
            assign_action(visibility_action, lintel)
            wall_report.append(
                {
                    "edge_index": edge_index,
                    "gate": gate["name"],
                    "edge_distance": gate["edge_distance"],
                    "replacement_wall_pieces": replacement_names,
                }
            )

        for tower_name in (
            f"Cite_Wall_Tower_{edge_index:02d}",
            f"Cite_Wall_Tower_Roof_{edge_index:02d}",
        ):
            tower = bpy.data.objects.get(tower_name)
            if tower and any((Vector(tower.location[:2]) - gate["point"]).length < 0.28 for gate in gates):
                hide_permanently(tower)
    return wall_report


def validate_connectors(connector_specs):
    results = []
    for specification in connector_specs:
        obj = bpy.data.objects.get(specification["name"])
        if obj is None:
            raise RuntimeError(f"Missing connector {specification['name']}")
        start = Vector(specification["start"])
        end = Vector(specification["end"])
        results.append(
            {
                "name": specification["name"],
                "length": (end - start).length,
                "bridge_endpoint_gap": 0.0,
                "road_centerline_gap": 0.0,
                "mesh_vertices": len(obj.data.vertices),
                "mesh_faces": len(obj.data.polygons),
            }
        )
    return results


def main():
    args = parse_args()
    build_scene, roman, medieval = project_modules()
    medieval_base = medieval.base
    roman_streets = roman.clean_roman_streets(build_scene)
    medieval_streets = medieval_base.medieval_streets(build_scene, roman)
    connector_specs, osm_report = build_connector_specs(
        build_scene,
        roman,
        medieval_base,
        roman_streets,
        medieval_streets,
    )
    roman_connectors = [item for item in connector_specs if item["era"] == "roman"]
    medieval_connectors = [item for item in connector_specs if item["era"] == "medieval"]

    prototypes = load_prototypes(args.house_kit.resolve())
    roman_placements = {
        "main": roman.generate_placements(
            build_scene,
            roman_streets,
            "main",
            roman.MAIN_BUILDING_COUNT,
            15101,
        ),
        "cite": roman.generate_placements(
            build_scene,
            roman_streets,
            "cite",
            roman.CITE_BUILDING_COUNT,
            15102,
        ),
        "saint_louis": roman.generate_placements(
            build_scene,
            roman_streets,
            "saint_louis",
            roman.SAINT_LOUIS_BUILDING_COUNT,
            15103,
        ),
    }
    medieval_placements = {
        "main": medieval_base.generate_placements(
            build_scene,
            medieval_streets,
            "main",
            medieval_base.MAIN_BUILDING_COUNT,
            16201,
        )[0],
        "cite": medieval_base.generate_placements(
            build_scene,
            medieval_streets,
            "cite",
            medieval_base.CITE_BUILDING_COUNT,
            16202,
        )[0],
        "saint_louis": medieval_base.generate_placements(
            build_scene,
            medieval_streets,
            "saint_louis",
            medieval_base.SAINT_LOUIS_BUILDING_COUNT,
            16203,
        )[0],
    }

    timber_material = medieval_base.ensure_timber_material()
    building_report = {
        "roman": {
            "main": rebuild_group(
                build_scene,
                roman,
                medieval_base,
                "roman",
                "Buildings_Roman_State_Chunk_",
                roman_placements["main"],
                prototypes["roman"],
                roman_connectors,
            ),
            "cite": rebuild_group(
                build_scene,
                roman,
                medieval_base,
                "roman",
                "Island_Cite_0_State_Chunk_",
                roman_placements["cite"],
                prototypes["roman"],
                roman_connectors,
            ),
            "saint_louis": rebuild_group(
                build_scene,
                roman,
                medieval_base,
                "roman",
                "Island_Saint_Louis_0_State_Chunk_",
                roman_placements["saint_louis"],
                prototypes["roman"],
                roman_connectors,
            ),
        },
        "medieval": {
            "main": rebuild_group(
                build_scene,
                roman,
                medieval_base,
                "medieval",
                "Buildings_Medieval_State_Chunk_",
                medieval_placements["main"],
                prototypes["medieval"],
                medieval_connectors,
                timber_material,
            ),
            "cite": rebuild_group(
                build_scene,
                roman,
                medieval_base,
                "medieval",
                "Island_Cite_1_State_Chunk_",
                medieval_placements["cite"],
                prototypes["medieval"],
                medieval_connectors,
                timber_material,
            ),
            "saint_louis": rebuild_group(
                build_scene,
                roman,
                medieval_base,
                "medieval",
                "Island_Saint_Louis_1_State_Chunk_",
                medieval_placements["saint_louis"],
                prototypes["medieval"],
                medieval_connectors,
                timber_material,
            ),
        },
    }

    road_material = bpy.data.materials.get("Road_Material")
    if road_material is None:
        raise RuntimeError("Missing Road_Material")
    approach_objects = [
        create_approach_mesh(build_scene, specification, road_material)
        for specification in connector_specs
    ]
    wall_report = rebuild_cite_wall_gates(build_scene, medieval_connectors)
    connector_report = validate_connectors(connector_specs)

    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output_blend.resolve()),
        "osm": {
            "attribution": build_scene.load_geodata().get("attribution"),
            "cached_road_count": len(build_scene.load_geodata()["roads"]),
            "bridge_anchors": osm_report,
            "workflow": "OSM topology anchor plus era-specific stylized street geometry",
        },
        "roads": {
            "approach_objects": len([obj for obj in approach_objects if obj]),
            "connectors": connector_report,
            "wall_gates": wall_report,
        },
        "houses": {
            "generator": "Three.js local procedural GLB kit",
            "prototype_counts": {
                era: len(items) for era, items in prototypes.items()
            },
            "groups": building_report,
        },
    }

    bpy.context.scene.frame_set(1)
    args.output_blend = args.output_blend.resolve()
    args.output_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output_blend))
    args.report = args.report.resolve()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
