import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("inputs", nargs="+", type=Path)
    return parser.parse_args(args)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bounds(objects):
    corners = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    minimum = Vector((min(point.x for point in corners), min(point.y for point in corners), min(point.z for point in corners)))
    maximum = Vector((max(point.x for point in corners), max(point.y for point in corners), max(point.z for point in corners)))
    return minimum, maximum


def add_material(name, color, roughness=0.7):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF") or next(
        (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
        None,
    )
    if shader is None:
        raise RuntimeError(f"Principled shader missing from {name}")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    return material


def setup_stage():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.fps = 30
    scene.render.image_settings.color_depth = "8"
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.115, 0.16, 0.075, 1.0)
    background.inputs["Strength"].default_value = 0.55
    scene.view_settings.look = "AgX - Medium High Contrast"

    camera_data = bpy.data.cameras.new("Preview_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 7.8
    camera = bpy.data.objects.new("Preview_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (8.2, -10.6, 7.6)
    look_at(camera, (0.0, 0.0, 1.8))
    scene.camera = camera

    sun_data = bpy.data.lights.new("Preview_Sun", "SUN")
    sun_data.energy = 3.1
    sun_data.angle = math.radians(3.0)
    sun = bpy.data.objects.new("Preview_Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(38), math.radians(-18), math.radians(32))

    area_data = bpy.data.lights.new("Preview_Fill", "AREA")
    area_data.energy = 650
    area_data.shape = "DISK"
    area_data.size = 8.0
    area = bpy.data.objects.new("Preview_Fill", area_data)
    bpy.context.collection.objects.link(area)
    area.location = (-4.0, -2.0, 8.0)
    look_at(area, (0.0, 0.0, 1.5))

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0.0, 0.0, -0.025))
    floor = bpy.context.object
    floor.name = "Preview_Floor"
    floor.data.materials.append(add_material("Preview_Floor_Material", (0.20, 0.28, 0.12), 0.82))
    return {camera, sun, area, floor}


def remove_imported(imported):
    for obj in imported:
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)


def import_and_normalize(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh imported from {path}")

    minimum, maximum = world_bounds(meshes)
    dimensions = maximum - minimum
    center = (minimum + maximum) * 0.5
    source_max_dimension = max(dimensions)
    scale = 5.5 / max(0.0001, source_max_dimension)

    root = bpy.data.objects.new(f"Preview_Root_{path.stem}", None)
    bpy.context.collection.objects.link(root)
    for obj in imported:
        if obj.parent is None:
            world_matrix = obj.matrix_world.copy()
            obj.parent = root
            obj.matrix_world = world_matrix
    root.scale = (scale, scale, scale)
    root.location = (-center.x * scale, -center.y * scale, -minimum.z * scale)

    mesh_vertices = sum(len(obj.data.vertices) for obj in meshes)
    for obj in meshes:
        obj.data.calc_loop_triangles()
    mesh_triangles = sum(len(obj.data.loop_triangles) for obj in meshes)
    return imported + [root], root, {
        "path": str(path.resolve()),
        "objects": len(imported),
        "mesh_objects": len(meshes),
        "vertices": mesh_vertices,
        "triangles": mesh_triangles,
        "source_bounds_min": list(minimum),
        "source_bounds_max": list(maximum),
        "source_dimensions": list(dimensions),
        "preview_scale": scale,
    }


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    clear_scene()
    stage_objects = setup_stage()
    reports = []

    for path in args.inputs:
        imported, root, report = import_and_normalize(path)
        rendered = []
        for angle in (0, 90, 180, 270):
            root.rotation_euler[2] = math.radians(angle)
            output_path = args.output_dir / f"{path.stem}_{angle:03d}.png"
            bpy.context.scene.render.filepath = str(output_path.resolve())
            bpy.ops.render.render(write_still=True)
            rendered.append(str(output_path.resolve()))
        report["renders"] = rendered
        reports.append(report)
        remove_imported(imported)

    args.report.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
