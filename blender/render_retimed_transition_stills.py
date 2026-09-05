from pathlib import Path

import bpy


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "stills" / "retimed_transition"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_percentage = 50
    scene.eevee.taa_render_samples = 8
    scene.render.image_settings.file_format = "PNG"
    for index, frame in enumerate(range(1020, 1441, 30)):
        scene.frame_set(frame)
        scene.render.filepath = str(OUTPUT_DIR / f"{index:02d}_{frame}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
