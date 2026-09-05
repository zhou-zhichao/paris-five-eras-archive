import collections
import json
from pathlib import Path

import bpy

scene = bpy.context.scene
report = {
    "objects": len(bpy.data.objects),
    "roots": [],
    "materials": [m.name for m in bpy.data.materials],
    "frames": {},
    "images": [{"name": i.name, "path": i.filepath, "packed": bool(i.packed_file)} for i in bpy.data.images],
}
for obj in bpy.data.objects:
    if obj.parent is None:
        report["roots"].append({"name": obj.name, "type": obj.type, "children": len(obj.children), "location": list(obj.location)})
for frame in [1450, 2100, 2800, 3550]:
    scene.frame_set(frame)
    report["frames"][frame] = {
        "camera_location": list(scene.camera.location),
        "camera_rotation": list(scene.camera.rotation_euler),
        "ortho_scale": scene.camera.data.ortho_scale,
        "root_states": [{"name": o.name, "scale": list(o.scale), "hidden": o.hide_render} for o in bpy.data.objects if o.parent is None and o.type == "EMPTY"],
    }
out = Path(__file__).resolve().parents[1] / "reports" / "resume-scene.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(report, indent=2))
print("INSPECTION", out)
