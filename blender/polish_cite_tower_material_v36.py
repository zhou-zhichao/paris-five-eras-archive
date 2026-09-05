import argparse
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def principled(material):
    if not material.use_nodes or material.node_tree is None:
        raise RuntimeError(f"Material has no nodes: {material.name}")
    node = material.node_tree.nodes.get("Principled BSDF")
    if node is None:
        node = next(
            (
                candidate
                for candidate in material.node_tree.nodes
                if candidate.type == "BSDF_PRINCIPLED"
            ),
            None,
        )
    if node is None:
        raise RuntimeError(f"Material has no Principled BSDF: {material.name}")
    return node


def socket_value(node, name):
    socket = node.inputs.get(name)
    if socket is None:
        return None
    value = socket.default_value
    if hasattr(value, "__len__"):
        return [float(item) for item in value]
    return float(value)


def configure_material(source_name, target_name, settings):
    source = bpy.data.materials.get(source_name)
    if source is None:
        raise RuntimeError(f"Missing source material: {source_name}")
    material = bpy.data.materials.get(target_name)
    if material is None:
        material = source.copy()
        material.name = target_name
    bsdf = principled(material)
    before = {
        name: socket_value(bsdf, name)
        for name in (
            "Base Color",
            "Metallic",
            "Roughness",
            "Diffuse Roughness",
            "Specular IOR Level",
            "Coat Weight",
            "Coat Roughness",
        )
    }
    for name, value in settings.items():
        socket = bsdf.inputs.get(name)
        if socket is not None:
            socket.default_value = value
    material.diffuse_color = (*settings["Base Color"][:3], 1.0)
    material["v36_finish"] = "matte weathered masonry"
    after = {
        name: socket_value(bsdf, name)
        for name in before
    }
    return material, {"material": material.name, "before": before, "after": after}


def is_cite_tower_object(obj):
    if not obj.name.startswith(("Cite_Wall_", "Cite_Gate_")):
        return False
    return "Tower" in obj.name or "Roof" in obj.name


def main():
    args = parse_args()
    args.output_blend = args.output_blend.resolve()
    args.report = args.report.resolve()
    args.output_blend.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    stone, stone_report = configure_material(
        "Landmark_Stone",
        "Cite_Tower_Stone_Matte_v36",
        {
            "Base Color": (0.72, 0.64, 0.48, 1.0),
            "Metallic": 0.0,
            "Roughness": 0.76,
            "Diffuse Roughness": 0.32,
            "Specular IOR Level": 0.22,
            "Coat Weight": 0.0,
            "Coat Roughness": 0.62,
        },
    )
    roof, roof_report = configure_material(
        "Roof_Terracotta",
        "Cite_Tower_Terracotta_Matte_v36",
        {
            "Base Color": (0.38, 0.068, 0.025, 1.0),
            "Metallic": 0.0,
            "Roughness": 0.68,
            "Diffuse Roughness": 0.28,
            "Specular IOR Level": 0.24,
            "Coat Weight": 0.0,
            "Coat Roughness": 0.58,
        },
    )

    assignments = []
    for obj in bpy.data.objects:
        if not is_cite_tower_object(obj):
            continue
        for slot in obj.material_slots:
            if slot.material is None:
                continue
            source_name = slot.material.name
            if source_name == "Landmark_Stone":
                slot.material = stone
            elif source_name == "Roof_Terracotta":
                slot.material = roof
            else:
                continue
            assignments.append(
                {
                    "object": obj.name,
                    "source": source_name,
                    "target": slot.material.name,
                    "visible": not obj.hide_render,
                }
            )

    if not assignments:
        raise RuntimeError("No Cite tower material slots were reassigned")
    scene = bpy.context.scene
    scene["v36_cite_tower_finish"] = (
        "Matte weathered stone and terracotta with subdued specular response"
    )
    source_blend = bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(
        filepath=str(args.output_blend),
        compress=True,
    )
    report = {
        "version": "v36",
        "source_blend": source_blend,
        "output_blend": str(args.output_blend),
        "materials": [stone_report, roof_report],
        "assignment_count": len(assignments),
        "visible_assignment_count": sum(
            1 for assignment in assignments if assignment["visible"]
        ),
        "assignments": assignments,
    }
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "assignments"}, indent=2))


if __name__ == "__main__":
    main()
