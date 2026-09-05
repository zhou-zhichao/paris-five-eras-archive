import argparse
import sys
from pathlib import Path

import bmesh
import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1470)
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_motion_blur = False
    scene.eevee.taa_render_samples = 24

    mesh = bpy.data.objects["Seine"].data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(
        bm,
        faces=list(bm.faces),
        quad_method="BEAUTY",
        ngon_method="BEAUTY",
    )
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    print(f"WATER_TRIANGLES {len(mesh.polygons)}")

    scene.render.filepath = str(args.output)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
