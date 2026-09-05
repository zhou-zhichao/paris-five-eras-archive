import argparse
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


MATERIAL_SETTINGS = {
    "Landmark_Notre_Dame_GLB": {"value": 1.42, "saturation": 0.94, "roughness": 0.38, "emission": 0.10},
    "Landmark_Louvre_GLB": {"value": 1.42, "saturation": 0.94, "roughness": 0.37, "emission": 0.11},
    "Landmark_Arc_de_Triomphe_GLB": {"value": 1.46, "saturation": 0.92, "roughness": 0.38, "emission": 0.11},
    "Landmark_Palais_Garnier_GLB": {"value": 1.32, "saturation": 0.96, "roughness": 0.34, "emission": 0.09},
    "Landmark_Gare_du_Nord_GLB": {"value": 1.38, "saturation": 0.94, "roughness": 0.36, "emission": 0.10},
    "Landmark_Eiffel_Tower_GLB": {"value": 1.18, "saturation": 0.92, "roughness": 0.31, "emission": 0.045, "metallic": 0.16},
}


CLEARANCE_SPECS = [
    ((0.15, 0.25), (2.40, 1.45), -0.55, 0.42),
    ((-10.8, 11.9), (3.40, 4.00), math.radians(90.0), 0.48),
    ((-40.2, 23.2), (1.15, 0.82), 0.0, 0.42),
    ((-13.6, 18.4), (2.30, 1.72), math.radians(-4.0), 0.46),
    ((6.5, 26.15), (3.40, 4.60), math.radians(173.0), 0.48),
    ((-40.6, 6.0), (2.75, 2.75), 0.0, 0.34),
]


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(args)


def find_landmark_material(prefix):
    return next((material for material in bpy.data.materials if material.name.startswith(prefix)), None)


def polish_material(prefix, settings):
    material = find_landmark_material(prefix)
    if material is None or not material.use_nodes or material.node_tree is None:
        raise RuntimeError(f"Missing node material for {prefix}")
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        raise RuntimeError(f"Missing Principled BSDF for {prefix}")
    base_input = bsdf.inputs.get("Base Color")
    source_link = next((link for link in links if link.to_socket == base_input), None)
    if source_link is None:
        raise RuntimeError(f"Base color is not texture-driven for {prefix}")

    source_socket = source_link.from_socket
    links.remove(source_link)
    lift = nodes.new("ShaderNodeHueSaturation")
    lift.name = f"{prefix}_Color_Lift"
    lift.label = "Landmark texture lift"
    lift.location = (source_socket.node.location.x + 240, source_socket.node.location.y)
    lift.inputs["Hue"].default_value = 0.5
    lift.inputs["Saturation"].default_value = settings["saturation"]
    lift.inputs["Value"].default_value = settings["value"]
    lift.inputs["Fac"].default_value = 1.0
    links.new(source_socket, lift.inputs["Color"])
    links.new(lift.outputs["Color"], base_input)

    bsdf.inputs["Roughness"].default_value = settings["roughness"]
    bsdf.inputs["Metallic"].default_value = settings.get("metallic", 0.0)
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.16
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.24
    if "IOR Level" in bsdf.inputs:
        bsdf.inputs["IOR Level"].default_value = 0.58
    if "Emission Color" in bsdf.inputs:
        links.new(lift.outputs["Color"], bsdf.inputs["Emission Color"])
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = settings["emission"]

    return {
        "material": material.name,
        "value": settings["value"],
        "saturation": settings["saturation"],
        "roughness": settings["roughness"],
        "emission": settings["emission"],
        "metallic": settings.get("metallic", 0.0),
    }


def point_inside_clearance(point):
    for center, dimensions, rotation, extra in CLEARANCE_SPECS:
        dx = point.x - center[0]
        dy = point.y - center[1]
        cos_r = math.cos(rotation)
        sin_r = math.sin(rotation)
        local_x = dx * cos_r + dy * sin_r
        local_y = -dx * sin_r + dy * cos_r
        if abs(local_x) <= dimensions[0] * 0.5 + extra and abs(local_y) <= dimensions[1] * 0.5 + extra:
            return True
    return False


def clear_vegetation_mesh(obj):
    if obj.data.shape_keys is not None:
        raise RuntimeError(f"Refusing to edit shape-key mesh: {obj.name}")
    before_vertices = len(obj.data.vertices)
    before_faces = len(obj.data.polygons)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    world_matrix = obj.matrix_world.copy()
    to_delete = [vertex for vertex in bm.verts if point_inside_clearance(world_matrix @ vertex.co)]
    bmesh.ops.delete(bm, geom=to_delete, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return {
        "object": obj.name,
        "vertices_before": before_vertices,
        "vertices_after": len(obj.data.vertices),
        "vertices_removed": before_vertices - len(obj.data.vertices),
        "faces_before": before_faces,
        "faces_after": len(obj.data.polygons),
        "faces_removed": before_faces - len(obj.data.polygons),
    }


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

    material_report = [polish_material(prefix, settings) for prefix, settings in MATERIAL_SETTINGS.items()]
    vegetation_report = []
    for name in ("Forest_Persistent", "Champ_Formal_Tree_Rows"):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            vegetation_report.append(clear_vegetation_mesh(obj))

    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output),
        "materials": material_report,
        "vegetation": vegetation_report,
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
