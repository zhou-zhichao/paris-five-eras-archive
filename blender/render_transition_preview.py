from pathlib import Path

import bpy


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_DIR / "previews" / "medieval_transition_2min_timing.mp4"


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_start = 1020
    scene.frame_end = 1440
    scene.render.resolution_percentage = 50
    scene.eevee.taa_render_samples = 8
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.filepath = str(OUTPUT_PATH)
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
