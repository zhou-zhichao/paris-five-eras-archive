import bpy, os, sys
scene = bpy.context.scene
out = os.path.abspath("renders/wdebug"); os.makedirs(out, exist_ok=True)
scene.render.resolution_x = 480; scene.render.resolution_y = 270; scene.eevee.taa_render_samples = 4
scene.frame_set(1)


def shot(name):
    scene.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("[dbg]", name, flush=True)


shot("a_default")
scene.use_nodes = False
shot("b_nocomp")
scene.use_nodes = True
for ob in scene.objects:
    if ob.name not in ("WATER", "TERRAIN", "Camera", "CamTarget", "Sun"):
        ob.hide_render = True
shot("c_water_terrain_only")
bpy.data.objects["TERRAIN"].hide_render = True
shot("d_water_only")
w = bpy.data.objects["WATER"]
print("[dbg] water z", w.location.z, "faces", len(w.data.polygons), "hide_render", w.hide_render, "visible", w.visible_get())
print("[dbg] cam", tuple(scene.camera.matrix_world.translation), "clip", scene.camera.data.clip_start, scene.camera.data.clip_end)
print("[dbg] mist", scene.world.mist_settings.start, scene.world.mist_settings.depth)
