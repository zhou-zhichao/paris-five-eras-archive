"""Render one review frame; never start animation rendering."""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument("--frame", type=int, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--width", type=int, default=960)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
scene = bpy.context.scene
scene.frame_set(args.frame)
scene.render.resolution_x = args.width
scene.render.resolution_y = round(args.width * 9 / 16)
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.use_motion_blur = False
scene.eevee.taa_render_samples = 16
scene.render.filepath = str(args.output.resolve())
args.output.parent.mkdir(parents=True, exist_ok=True)
bounds = []
for obj in bpy.data.objects:
    if obj.parent is not None or not obj.name.startswith(("Landmark_", "Modern_Stations")):
        continue
    points = [child.matrix_world @ Vector(corner) for child in obj.children_recursive if child.type == "MESH" and not child.hide_render for corner in child.bound_box]
    if points:
        bounds.append({"name": obj.name, "bounds": [min(p.x for p in points), min(p.y for p in points), max(p.x for p in points), max(p.y for p in points)]})
args.output.with_suffix(".json").write_text(json.dumps({"frame":args.frame, "protected_landmarks": bounds}, indent=2))
bpy.ops.render.render(write_still=True)
print("STILL_COMPLETE", args.output)
