"""Render settings applied on the server before `-a` (runs inside Blender after the blend is loaded).
Environment overrides: PARIS_RES_X, PARIS_RES_Y, PARIS_SAMPLES.
"""
import bpy, os

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = int(os.environ.get("PARIS_RES_X", "2560"))
scene.render.resolution_y = int(os.environ.get("PARIS_RES_Y", "1440"))
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = int(os.environ.get("PARIS_SAMPLES", "32"))
scene.render.fps = 30
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.render.image_settings.compression = 15
scene.render.film_transparent = False
scene.render.use_persistent_data = False
scene.render.use_overwrite = False       # workers skip frames that already exist (resume-friendly)
scene.render.use_placeholder = True      # claim frames so parallel workers don't collide
# GPU for EEVEE is implicit (OpenGL/Vulkan); make Cycles devices irrelevant
print(f"[configure] {scene.render.resolution_x}x{scene.render.resolution_y} samples={scene.eevee.taa_render_samples} frames {scene.frame_start}-{scene.frame_end}", flush=True)
