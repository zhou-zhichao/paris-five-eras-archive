import json

import bpy
from mathutils import Vector


MATERIAL_NAMES = (
    "Land_Material",
    "Riverbed_Silt",
    "Riverbank_Silt",
    "Riverbank_Sand",
    "Water_Material",
    "Forest_Dark",
    "Forest_Light",
    "Forest_Trunk",
    "Forest_Olive",
    "Forest_Deep",
)


def socket_value(socket):
    value = socket.default_value
    if hasattr(value, "__len__") and not isinstance(value, str):
        return list(value)
    return value


def material_report(material):
    report = {
        "name": material.name,
        "diffuse_color": list(material.diffuse_color),
        "use_nodes": material.use_nodes,
    }
    if not material.use_nodes or material.node_tree is None:
        return report
    principled = next(
        (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
        None,
    )
    if principled:
        names = (
            "Base Color",
            "Metallic",
            "Roughness",
            "IOR",
            "Specular IOR Level",
            "Coat Weight",
            "Coat Roughness",
            "Transmission Weight",
            "Emission Color",
            "Emission Strength",
        )
        report["principled"] = {
            name: {
                "value": socket_value(principled.inputs[name]),
                "linked": principled.inputs[name].is_linked,
            }
            for name in names
            if name in principled.inputs
        }
    report["nodes"] = [
        {
            "name": node.name,
            "type": node.type,
        }
        for node in material.node_tree.nodes
    ]
    return report


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[index] for point in points) for index in range(3)],
        "max": [max(point[index] for point in points) for index in range(3)],
    }


def object_report(obj):
    report = {
        "name": obj.name,
        "type": obj.type,
        "bounds": world_bounds(obj),
        "materials": [
            slot.material.name if slot.material else None for slot in obj.material_slots
        ],
    }
    if obj.type == "MESH":
        report.update(
            {
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "smooth_polygons": sum(face.use_smooth for face in obj.data.polygons),
                "z_values": sorted(
                    {round(vertex.co.z, 5) for vertex in obj.data.vertices}
                )[:30],
                "color_attributes": [
                    {
                        "name": attribute.name,
                        "domain": attribute.domain,
                        "data_type": attribute.data_type,
                    }
                    for attribute in obj.data.color_attributes
                ],
            }
        )
    return report


scene = bpy.context.scene
world = scene.world
background = None
if world and world.use_nodes and world.node_tree:
    node = next(
        (item for item in world.node_tree.nodes if item.type == "BACKGROUND"),
        None,
    )
    if node:
        background = {
            "color": socket_value(node.inputs["Color"]),
            "strength": node.inputs["Strength"].default_value,
        }

sun = bpy.data.objects.get("Sun")
report = {
    "scene": {
        "engine": scene.render.engine,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
        "world_background": background,
        "world_nodes": [
            {"name": node.name, "type": node.type}
            for node in world.node_tree.nodes
        ]
        if world and world.use_nodes and world.node_tree
        else [],
        "eevee": {
            "samples": scene.eevee.taa_render_samples,
            "gtao": scene.eevee.use_gtao,
            "gtao_distance": scene.eevee.gtao_distance,
            "gtao_quality": scene.eevee.gtao_quality,
            "shadows": scene.eevee.use_shadows,
            "shadow_resolution_scale": scene.eevee.shadow_resolution_scale,
        },
    },
    "sun": {
        "rotation": list(sun.rotation_euler),
        "energy": sun.data.energy,
        "angle": sun.data.angle,
        "color": list(sun.data.color),
        "use_shadow": sun.data.use_shadow,
    }
    if sun
    else None,
    "materials": [
        material_report(bpy.data.materials[name])
        for name in MATERIAL_NAMES
        if name in bpy.data.materials
    ],
    "objects": [
        object_report(bpy.data.objects[name])
        for name in (
            "Land",
            "Seine",
            "Seine_Riverbank",
            "Ile_de_la_Cite_Margin",
            "Ile_Saint_Louis_Margin",
            "Forest_Persistent",
        )
        if name in bpy.data.objects
    ],
}

print("ENVIRONMENT_V18_BEGIN")
print(json.dumps(report, indent=2))
print("ENVIRONMENT_V18_END")
