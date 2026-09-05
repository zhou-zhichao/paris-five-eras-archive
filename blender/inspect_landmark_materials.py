import json

import bpy


PREFIX = "Landmark_"
records = []
seen = set()
for obj in bpy.data.objects:
    if obj.type != "MESH" or not obj.name.startswith(PREFIX):
        continue
    for material in obj.data.materials:
        if material is None or material.name in seen:
            continue
        seen.add(material.name)
        nodes = material.node_tree.nodes if material.use_nodes and material.node_tree else []
        links = material.node_tree.links if material.use_nodes and material.node_tree else []
        bsdf = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
        base_link = None
        if bsdf is not None:
            base_link = next((link for link in links if link.to_node == bsdf and link.to_socket == bsdf.inputs.get("Base Color")), None)
        records.append(
            {
                "material": material.name,
                "nodes": [{"name": node.name, "type": node.type} for node in nodes],
                "base_color_source": base_link.from_node.name if base_link else None,
                "roughness": bsdf.inputs["Roughness"].default_value if bsdf else None,
                "metallic": bsdf.inputs["Metallic"].default_value if bsdf else None,
            }
        )

print(json.dumps(records, indent=2))
