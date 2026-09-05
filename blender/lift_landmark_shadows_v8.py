import argparse
import json
import sys
from pathlib import Path

import bpy


SETTINGS = {
    "Landmark_Notre_Dame_GLB": (0.78, 0.12),
    "Landmark_Louvre_GLB": (0.74, 0.13),
    "Landmark_Arc_de_Triomphe_GLB": (0.72, 0.14),
    "Landmark_Palais_Garnier_GLB": (0.82, 0.11),
    "Landmark_Gare_du_Nord_GLB": (0.78, 0.12),
    "Landmark_Eiffel_Tower_GLB": (0.86, 0.055),
}


def parse_args():
    args = sys.argv
    args = args[args.index("--") + 1 :] if "--" in args else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(args)


def apply_shadow_lift(prefix, gamma_value, emission_strength):
    material = next((item for item in bpy.data.materials if item.name.startswith(prefix)), None)
    if material is None or not material.use_nodes or material.node_tree is None:
        raise RuntimeError(f"Missing landmark material for {prefix}")
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    lift = nodes.get(f"{prefix}_Color_Lift")
    if bsdf is None or lift is None:
        raise RuntimeError(f"Missing v7 color lift nodes for {prefix}")

    gamma = nodes.new("ShaderNodeGamma")
    gamma.name = f"{prefix}_Shadow_Lift"
    gamma.label = "Lift baked texture shadows"
    gamma.location = (lift.location.x + 210, lift.location.y)
    gamma.inputs["Gamma"].default_value = gamma_value
    links.new(lift.outputs["Color"], gamma.inputs["Color"])

    for input_name in ("Base Color", "Emission Color"):
        target = bsdf.inputs.get(input_name)
        if target is None:
            continue
        for link in list(links):
            if link.to_socket == target:
                links.remove(link)
        links.new(gamma.outputs["Color"], target)
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    return {
        "material": material.name,
        "gamma": gamma_value,
        "emission": emission_strength,
    }


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(args.output),
        "materials": [
            apply_shadow_lift(prefix, gamma_value, emission_strength)
            for prefix, (gamma_value, emission_strength) in SETTINGS.items()
        ],
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
