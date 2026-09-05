import importlib.util
import json
import math
import random
from pathlib import Path

import bmesh
import bpy


BLENDER_DIR = Path(__file__).resolve().parent
BASE_PATH = BLENDER_DIR / "rebuild_medieval_urbanism_v16.py"


def load_base():
    spec = importlib.util.spec_from_file_location("paris_medieval_urbanism_v16_base", BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base()
base.CITE_BUILDING_COUNT = 155
base.SAINT_LOUIS_BUILDING_COUNT = 108

original_style_for_candidate = base.style_for_candidate
original_medieval_streets = base.medieval_streets
original_point_in_rotated_box = base.point_in_rotated_box
original_rebuild_medieval_roads = base.rebuild_medieval_roads
original_generate_placements = base.generate_placements


def style_for_candidate(rng, zone):
    if zone == "main":
        return original_style_for_candidate(rng, zone)

    if zone == "cite":
        width = rng.uniform(0.125, 0.205)
        depth = rng.uniform(0.12, 0.195)
        height = rng.uniform(0.28, 0.57)
    else:
        width = rng.uniform(0.12, 0.2)
        depth = rng.uniform(0.115, 0.19)
        height = rng.uniform(0.245, 0.51)

    plan_values = ["standard", "annex", "courtyard", "tower", "chapel"]
    plan_style = rng.choices(
        plan_values,
        weights=[0.925, 0.05, 0.01, 0.01, 0.005],
        k=1,
    )[0]
    roof_style = rng.choices(
        ["gable", "hip", "pyramid", "mansard", "flat"],
        weights=[0.59, 0.23, 0.08, 0.035, 0.065],
        k=1,
    )[0]
    return width, depth, height, plan_style, roof_style


def rotated_point(center_x, center_y, rotation, local_x, local_y):
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    return (
        center_x + local_x * cos_r - local_y * sin_r,
        center_y + local_x * sin_r + local_y * cos_r,
    )


def church_perimeter_streets(roman_helpers):
    center_x, center_y, rotation = 0.15, 0.25, -0.55
    specifications = (
        ((-1.5, 0.91), (1.5, 0.91), (1,)),
        ((-1.5, -0.91), (1.5, -0.91), (-1,)),
        ((-1.45, -0.92), (-1.45, 0.92), (1,)),
        ((1.45, -0.92), (1.45, 0.92), (-1,)),
    )
    segments = []
    for local_start, local_end, sides in specifications:
        start = rotated_point(center_x, center_y, rotation, *local_start)
        end = rotated_point(center_x, center_y, rotation, *local_end)
        segments.extend(
            roman_helpers.polyline_segments(
                [start, end],
                0.075,
                "cite",
                frontage=True,
                sides=sides,
                kind="cathedral_lane",
            )
        )
    return segments


def medieval_streets(bs, roman_helpers):
    segments = original_medieval_streets(bs, roman_helpers)
    segments.extend(church_perimeter_streets(roman_helpers))
    return segments


def reserved_footprints(zone):
    if zone == "cite":
        return [(0.15, 0.25, 1.22, 0.745, -0.55)]
    return []


def point_in_rotated_box(x, y, footprint, margin=0.0):
    # Roads only need a narrow safety strip around the actual cathedral mesh.
    return original_point_in_rotated_box(x, y, footprint, margin=min(margin, 0.045))


def cathedral_south_infill(bs, streets, footprint_index):
    street_index = next(
        (
            index
            for index, street in enumerate(streets)
            if street["zone"] == "cite"
            and street["kind"] == "cathedral_lane"
            and cathedral_local_midpoint(street)[1] < -0.8
        ),
        0,
    )
    polygon = base.zone_polygon(bs, "cite")
    placements = []
    for index in range(12):
        rng = random.Random(17301 + index)
        local_x = -1.045 + index * 0.19
        local_y = -0.817 + rng.uniform(-0.004, 0.004)
        x, y = rotated_point(0.15, 0.25, -0.55, local_x, local_y)
        width = rng.uniform(0.15, 0.17)
        depth = rng.uniform(0.088, 0.098)
        height = rng.uniform(0.39, 0.53)
        half_width, half_depth = bs.house_half_extents(width, depth, "standard")
        footprint_radius = math.hypot(half_width, half_depth)
        placement = {
            "x": x,
            "y": y,
            "width": width,
            "depth": depth,
            "height": height,
            "rotation": -0.55,
            "street_angle": -0.55,
            "street_width": 0.075,
            "street_index": street_index,
            "zone": "cite",
            "band": 0.0,
            "priority": -10.0 + index * 0.01,
            "seed": 17301 + index,
            "plan_style": "standard",
            "roof_style": rng.choice(("gable", "gable", "hip")),
            "timber": rng.random() < 0.42,
            "chimney": rng.random() < 0.48,
            "half_width": half_width,
            "half_depth": half_depth,
        }
        footprint = (x, y, half_width, half_depth, placement["rotation"])
        if not base.zone_contains(bs, "cite", x, y):
            continue
        if bs.polygon_edge_distance(x, y, polygon) < footprint_radius + 0.018:
            continue
        if not base.clear_of_streets(bs, placement, streets, extra=0.002):
            continue
        if not footprint_index.can_add(footprint):
            continue
        footprint_index.add(footprint)
        placements.append(placement)
    return placements


def cathedral_local_midpoint(street):
    midpoint_x = (street["start"][0] + street["end"][0]) * 0.5
    midpoint_y = (street["start"][1] + street["end"][1]) * 0.5
    delta_x = midpoint_x - 0.15
    delta_y = midpoint_y - 0.25
    cos_r = math.cos(-0.55)
    sin_r = math.sin(-0.55)
    return (
        delta_x * cos_r + delta_y * sin_r,
        -delta_x * sin_r + delta_y * cos_r,
    )


def generate_placements(bs, streets, zone, target_count, seed):
    placements, footprint_index = original_generate_placements(
        bs,
        streets,
        zone,
        target_count,
        seed,
    )
    if zone == "cite":
        placements.extend(cathedral_south_infill(bs, streets, footprint_index))
    return placements, footprint_index


def stabilize_water():
    seine = bpy.data.objects.get("Seine")
    if seine is None or seine.type != "MESH":
        raise RuntimeError("Missing Seine water mesh")

    mesh = seine.data
    negative_faces = sum(face.normal.z < 0.0 for face in mesh.polygons)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if negative_faces:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    if any(len(face.verts) > 3 for face in bm.faces):
        bmesh.ops.triangulate(
            bm,
            faces=list(bm.faces),
            quad_method="BEAUTY",
            ngon_method="BEAUTY",
        )
    bm.normal_update()
    downward_faces = [face for face in bm.faces if face.normal.z < 0.0]
    if downward_faces:
        bmesh.ops.reverse_faces(bm, faces=downward_faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    material = bpy.data.materials.get("Water_Material")
    if material is None or not material.use_nodes:
        raise RuntimeError("Missing Water_Material")
    nodes = material.node_tree.nodes
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    roughness_map = next((node for node in nodes if node.type == "MAP_RANGE"), None)
    bump = next((node for node in nodes if node.type == "BUMP"), None)
    glossy = nodes.get("Water_Reflection_Glossy")
    reflection_amount = nodes.get("Water_Reflection_Amount")

    if roughness_map:
        roughness_map.inputs["To Min"].default_value = 0.17
        roughness_map.inputs["To Max"].default_value = 0.24
    if bump:
        bump.inputs["Strength"].default_value = 0.006
        bump.inputs["Distance"].default_value = 0.012
    if glossy:
        glossy.inputs["Roughness"].default_value = 0.14
    if reflection_amount:
        reflection_amount.inputs["To Min"].default_value = 0.08
        reflection_amount.inputs["To Max"].default_value = 0.28
    bsdf.inputs["Transmission Weight"].default_value = 0.0
    bsdf.inputs["Coat Weight"].default_value = 0.22
    bsdf.inputs["Coat Roughness"].default_value = 0.14

    scene = bpy.context.scene
    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_method = "PROBE"
    scene.eevee.ray_tracing_options.resolution_scale = "1"

    probe = bpy.data.objects.get("Seine_Planar_Reflection_Probe")
    if probe:
        probe.location.z = -0.13
        probe.scale = (110.0, 80.0, 1.0)
        probe.data.clip_start = 0.05
        probe.data.influence_distance = 4.0

    return {
        "reversed_face_count": negative_faces,
        "triangle_count": len(mesh.polygons),
        "positive_normals": sum(face.normal.z > 0.0 for face in mesh.polygons),
        "ray_tracing_method": scene.eevee.ray_tracing_method,
        "roughness": [0.17, 0.24],
        "bump_strength": 0.006,
    }


water_report = None


def rebuild_medieval_roads(bs, roman_helpers, streets):
    global water_report
    result = original_rebuild_medieval_roads(bs, roman_helpers, streets)
    water_report = stabilize_water()
    return result


base.style_for_candidate = style_for_candidate
base.medieval_streets = medieval_streets
base.reserved_footprints = reserved_footprints
base.point_in_rotated_box = point_in_rotated_box
base.generate_placements = generate_placements
base.rebuild_medieval_roads = rebuild_medieval_roads


def main():
    args = base.parse_args()
    base.main()
    report_path = args.report.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["v17_adjustments"] = {
        "island_building_scale": "matched_to_mainland",
        "cathedral_perimeter_streets": 4,
        "cathedral_reserved_footprint": list(reserved_footprints("cite")[0]),
        "water": water_report,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["v17_adjustments"], indent=2))


if __name__ == "__main__":
    main()
