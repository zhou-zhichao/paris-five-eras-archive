"""Assemble the Blender scene (London) from cache/scene_data.npz.

usage: blender -b --python build_scene.py -- [--out cache/london.blend] [--subsample N] [--frames 5400]
"""
import bpy, bmesh, json, math, os, sys, time
import numpy as np
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kits, history, timeline, landmarks

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    if name in ARGS:
        return ARGS[ARGS.index(name) + 1]
    return default
CACHE = os.path.join(HERE, "..", "cache")
OUT = arg("--out", os.path.join(CACHE, "london.blend"))
SUB = int(arg("--subsample", "1"))
T0 = time.time()
def log(*a): print(f"[build {time.time()-T0:6.1f}s]", *a, flush=True)

FPS = timeline.FPS
FRAMES = int(arg("--frames", str(timeline.TOTAL_FRAMES)))
ROAD_W = 0.62      # road strip width multiplier
WALL_SCALE = 2.0   # city walls exaggerated like the buildings
TREE_SCALE = 3.9
LM_SCALE_XY = 1.25   # landmark footprint exaggeration (buildings are drawn 2x)
LM_SCALE_Z = 1.5     # landmarks are raised 1.5x so they read on the map
WATER_Z = -0.4

# ------------------------------------------------------------------ scene reset
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FRAMES
scene.unit_settings.system = 'METRIC'

D = np.load(os.path.join(CACHE, "scene_data.npz"))
R = np.load(os.path.join(CACHE, "rasters.npz"))
META = json.load(open(os.path.join(CACHE, "scene_meta.json")))
RX0, RX1, RY0, RY1, CELL = (META["raster"][k] for k in ("x0", "x1", "y0", "y1", "cell"))
NX, NY = (RX1 - RX0) // CELL, (RY1 - RY0) // CELL
TER = META["terrain"]
HMAP = D["hmap"]
WATER_R = R["water"]
log("data loaded", META["counts"])


def sample_h(xs, ys):
    fx = (np.asarray(xs) - TER["x0"]) / TER["step"]; fy = (np.asarray(ys) - TER["y0"]) / TER["step"]
    i = np.clip(fx.astype(int), 0, HMAP.shape[1] - 2); j = np.clip(fy.astype(int), 0, HMAP.shape[0] - 2)
    u = fx - i; v = fy - j
    return ((1 - u) * (1 - v) * HMAP[j, i] + u * (1 - v) * HMAP[j, i + 1] + (1 - u) * v * HMAP[j + 1, i] + u * v * HMAP[j + 1, i + 1])


def h_at(x, y):
    return float(sample_h(np.array([x]), np.array([y]))[0])


def is_water(x, y):
    c = int(np.clip((x - RX0) / CELL, 0, NX - 1)); r = int(np.clip((RY1 - y) / CELL, 0, NY - 1))
    return bool(WATER_R[r, c])


def frame_of_year(y):
    return timeline.t_of_year(y) * FPS + 1


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c


def link(ob, c):
    c.objects.link(ob)
    return ob


C_KITS = coll("KITS")
C_CITY = coll("CITY")
C_TREES = coll("TREES")
C_ROADS = coll("ROADS")
C_ENV = coll("ENV")
C_LM = coll("LANDMARKS")
C_BR = coll("BRIDGES")
C_WALLS = coll("WALLS")

KITS = kits.build_all_kits(C_KITS)
TREES = kits.build_trees(C_KITS)
log("kits built")


# ------------------------------------------------------------------ mesh helpers
def mesh_from_faces(name, verts, faces, face_attrs=None, mats=None, mat_index=None):
    me = bpy.data.meshes.new(name)
    verts = np.asarray(verts, dtype=np.float32); faces = np.asarray(faces, dtype=np.int32)
    n, m = len(verts), len(faces)
    k = faces.shape[1]
    me.vertices.add(n); me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(m * k); me.loops.foreach_set("vertex_index", faces.ravel())
    me.polygons.add(m)
    me.polygons.foreach_set("loop_start", np.arange(0, m * k, k, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(m, k, dtype=np.int32))
    if mat_index is not None:
        me.polygons.foreach_set("material_index", np.asarray(mat_index, dtype=np.int32))
    me.update(calc_edges=True)
    if face_attrs:
        for an, arr in face_attrs.items():
            a = me.attributes.new(an, 'FLOAT', 'FACE'); a.data.foreach_set("value", np.asarray(arr, dtype=np.float32))
    for mt in (mats or []):
        me.materials.append(mt)
    return bpy.data.objects.new(name, me)


def keyframe_year(idblock, path, index=-1):
    for t, y in timeline.SAMPLES:
        f = t * FPS + 1
        if f > FRAMES + 1:
            break
        if index >= 0:
            exec("idblock" + path + "[index] = y", {"idblock": idblock, "y": float(y), "index": index})
        else:
            exec("idblock" + path + " = y", {"idblock": idblock, "y": float(y)})
        idblock.keyframe_insert(data_path=path.lstrip("."), frame=f, index=index)
    owner = idblock.id_data if hasattr(idblock, "id_data") else idblock
    ad = owner.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


# ------------------------------------------------------------------ geometry node groups
def gn_nodes(ng):
    return ng.nodes, ng.links


def make_growth_group():
    ng = bpy.data.node_groups.new("CityGrowth", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Collection", in_out='INPUT', socket_type='NodeSocketCollection')
    ng.interface.new_socket("Year", in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, l = gn_nodes(ng)
    gi = n.new("NodeGroupInput"); go = n.new("NodeGroupOutput")

    def attr(name, typ='FLOAT'):
        a = n.new("GeometryNodeInputNamedAttribute"); a.data_type = typ; a.inputs["Name"].default_value = name
        return a
    birth, death, dur, rot = attr("birth"), attr("death"), attr("dur"), attr("rot")
    scale = attr("scale", 'FLOAT_VECTOR'); kit = attr("kit", 'INT')

    def cmp(op, a, b):
        c = n.new("FunctionNodeCompare"); c.data_type = 'FLOAT'; c.operation = op
        l.new(a, c.inputs[0]); l.new(b, c.inputs[1]); return c
    def math(op, a, b=None, default=None):
        m = n.new("ShaderNodeMath"); m.operation = op
        if a is not None: l.new(a, m.inputs[0])
        if b is not None: l.new(b, m.inputs[1])
        if default is not None: m.inputs[1].default_value = default
        return m
    year = gi.outputs["Year"]
    born = cmp('GREATER_EQUAL', year, birth.outputs["Attribute"])
    living = cmp('LESS_THAN', year, death.outputs["Attribute"])
    alive = n.new("FunctionNodeBooleanMath"); alive.operation = 'AND'
    l.new(born.outputs["Result"], alive.inputs[0]); l.new(living.outputs["Result"], alive.inputs[1])
    dead = n.new("FunctionNodeBooleanMath"); dead.operation = 'NOT'; l.new(alive.outputs[0], dead.inputs[0])
    dele = n.new("GeometryNodeDeleteGeometry"); dele.domain = 'POINT'; dele.mode = 'ALL'
    l.new(gi.outputs["Geometry"], dele.inputs["Geometry"]); l.new(dead.outputs[0], dele.inputs["Selection"])
    age = math('SUBTRACT', year, birth.outputs["Attribute"])
    s = math('DIVIDE', age.outputs[0], dur.outputs["Attribute"]); s.use_clamp = True
    oms = math('SUBTRACT', None, s.outputs[0]); oms.inputs[0].default_value = 1.0
    cube = math('POWER', oms.outputs[0], None, default=3.0)
    s2 = math('SUBTRACT', None, cube.outputs[0]); s2.inputs[0].default_value = 1.0
    pis = math('MULTIPLY', s.outputs[0], None, default=3.14159265); sn = math('SINE', pis.outputs[0])
    bump = math('MULTIPLY', sn.outputs[0], None, default=0.18)
    onep = math('ADD', bump.outputs[0], None, default=1.0)
    sz = math('MULTIPLY', s2.outputs[0], onep.outputs[0])
    sxy = math('MULTIPLY_ADD', s2.outputs[0], None, default=0.55); sxy.inputs[2].default_value = 0.45
    comb = n.new("ShaderNodeCombineXYZ"); l.new(sxy.outputs[0], comb.inputs[0]); l.new(sxy.outputs[0], comb.inputs[1]); l.new(sz.outputs[0], comb.inputs[2])
    vmul = n.new("ShaderNodeVectorMath"); vmul.operation = 'MULTIPLY'
    l.new(scale.outputs["Attribute"], vmul.inputs[0]); l.new(comb.outputs[0], vmul.inputs[1])
    rotv = n.new("ShaderNodeCombineXYZ"); l.new(rot.outputs["Attribute"], rotv.inputs[2])
    ci = n.new("GeometryNodeCollectionInfo"); ci.transform_space = 'ORIGINAL'
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    l.new(gi.outputs["Collection"], ci.inputs["Collection"])
    iop = n.new("GeometryNodeInstanceOnPoints")
    l.new(dele.outputs["Geometry"], iop.inputs["Points"]); l.new(ci.outputs["Instances"], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    l.new(kit.outputs["Attribute"], iop.inputs["Instance Index"])
    l.new(rotv.outputs[0], iop.inputs["Rotation"]); l.new(vmul.outputs[0], iop.inputs["Scale"])
    l.new(iop.outputs["Instances"], go.inputs["Geometry"])
    return ng


def make_tree_group():
    ng = bpy.data.node_groups.new("TreeLife", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Collection", in_out='INPUT', socket_type='NodeSocketCollection')
    ng.interface.new_socket("Year", in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, l = gn_nodes(ng)
    gi = n.new("NodeGroupInput"); go = n.new("NodeGroupOutput")
    def attr(name, typ='FLOAT'):
        a = n.new("GeometryNodeInputNamedAttribute"); a.data_type = typ; a.inputs["Name"].default_value = name
        return a
    death, rot, sc, kind = attr("death"), attr("rot"), attr("s"), attr("kind", 'INT')
    year = gi.outputs["Year"]
    rem = n.new("ShaderNodeMath"); rem.operation = 'SUBTRACT'; l.new(death.outputs["Attribute"], rem.inputs[0]); l.new(year, rem.inputs[1])
    fade = n.new("ShaderNodeMath"); fade.operation = 'DIVIDE'; fade.use_clamp = True; l.new(rem.outputs[0], fade.inputs[0]); fade.inputs[1].default_value = 6.0
    gone = n.new("FunctionNodeCompare"); gone.data_type = 'FLOAT'; gone.operation = 'LESS_EQUAL'
    l.new(fade.outputs[0], gone.inputs[0]); gone.inputs[1].default_value = 0.0
    dele = n.new("GeometryNodeDeleteGeometry"); dele.domain = 'POINT'; dele.mode = 'ALL'
    l.new(gi.outputs["Geometry"], dele.inputs["Geometry"]); l.new(gone.outputs["Result"], dele.inputs["Selection"])
    smul = n.new("ShaderNodeMath"); smul.operation = 'MULTIPLY'; l.new(sc.outputs["Attribute"], smul.inputs[0]); l.new(fade.outputs[0], smul.inputs[1])
    comb = n.new("ShaderNodeCombineXYZ")
    for i in range(3):
        l.new(smul.outputs[0], comb.inputs[i])
    rotv = n.new("ShaderNodeCombineXYZ"); l.new(rot.outputs["Attribute"], rotv.inputs[2])
    ci = n.new("GeometryNodeCollectionInfo"); ci.transform_space = 'ORIGINAL'
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    l.new(gi.outputs["Collection"], ci.inputs["Collection"])
    iop = n.new("GeometryNodeInstanceOnPoints")
    l.new(dele.outputs["Geometry"], iop.inputs["Points"]); l.new(ci.outputs["Instances"], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    l.new(kind.outputs["Attribute"], iop.inputs["Instance Index"])
    l.new(rotv.outputs[0], iop.inputs["Rotation"]); l.new(comb.outputs[0], iop.inputs["Scale"])
    l.new(iop.outputs["Instances"], go.inputs["Geometry"])
    return ng


def make_face_group():
    ng = bpy.data.node_groups.new("FaceLife", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Year", in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, l = gn_nodes(ng)
    gi = n.new("NodeGroupInput"); go = n.new("NodeGroupOutput")
    def attr(name):
        a = n.new("GeometryNodeInputNamedAttribute"); a.data_type = 'FLOAT'; a.inputs["Name"].default_value = name
        return a
    birth, death = attr("birth"), attr("death")
    year = gi.outputs["Year"]
    born = n.new("FunctionNodeCompare"); born.operation = 'GREATER_EQUAL'; l.new(year, born.inputs[0]); l.new(birth.outputs["Attribute"], born.inputs[1])
    living = n.new("FunctionNodeCompare"); living.operation = 'LESS_THAN'; l.new(year, living.inputs[0]); l.new(death.outputs["Attribute"], living.inputs[1])
    alive = n.new("FunctionNodeBooleanMath"); alive.operation = 'AND'; l.new(born.outputs[0], alive.inputs[0]); l.new(living.outputs[0], alive.inputs[1])
    dead = n.new("FunctionNodeBooleanMath"); dead.operation = 'NOT'; l.new(alive.outputs[0], dead.inputs[0])
    dele = n.new("GeometryNodeDeleteGeometry"); dele.domain = 'FACE'; dele.mode = 'ALL'
    l.new(gi.outputs["Geometry"], dele.inputs["Geometry"]); l.new(dead.outputs[0], dele.inputs["Selection"])
    l.new(dele.outputs["Geometry"], go.inputs["Geometry"])
    return ng


NG_GROWTH = make_growth_group()
NG_TREE = make_tree_group()
NG_FACE = make_face_group()


def socket_id(ng, name):
    for it in ng.interface.items_tree:
        if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.name == name:
            return it.identifier
    raise KeyError(name)


def add_gn(ob, ng, collection=None):
    mod = ob.modifiers.new("life", 'NODES')
    mod.node_group = ng
    if collection is not None:
        mod[socket_id(ng, "Collection")] = collection
    yid = socket_id(ng, "Year")
    mod[yid] = 0.0
    keyframe_year(mod, f'["{yid}"]')
    return mod


# ------------------------------------------------------------------ buildings
def point_cloud(name, xyz, attrs):
    me = bpy.data.meshes.new(name)
    n = len(xyz)
    me.vertices.add(n); me.vertices.foreach_set("co", np.asarray(xyz, dtype=np.float32).ravel())
    for an, (typ, arr) in attrs.items():
        a = me.attributes.new(an, typ, 'POINT')
        if typ == 'FLOAT_VECTOR':
            a.data.foreach_set("vector", np.asarray(arr, dtype=np.float32).ravel())
        elif typ == 'INT':
            a.data.foreach_set("value", np.asarray(arr, dtype=np.int32))
        else:
            a.data.foreach_set("value", np.asarray(arr, dtype=np.float32))
    me.update()
    return bpy.data.objects.new(name, me)


b_era = D["b_era"]
sel_all = np.arange(len(b_era))[::SUB]
for era_i, era in enumerate(kits.ERA_NAMES):
    idx = sel_all[b_era[sel_all] == era_i]
    if len(idx) == 0:
        continue
    xyz = np.stack([D["b_x"][idx], D["b_y"][idx], D["b_z"][idx]], axis=1)
    scale = np.stack([D["b_sx"][idx], D["b_sy"][idx], D["b_sz"][idx]], axis=1)
    ob = point_cloud(f"CITY_{era}", xyz, {
        "birth": ('FLOAT', D["b_birth"][idx]), "death": ('FLOAT', D["b_death"][idx]), "dur": ('FLOAT', D["b_dur"][idx]),
        "rot": ('FLOAT', D["b_rot"][idx]), "scale": ('FLOAT_VECTOR', scale), "kit": ('INT', D["b_kit"][idx])})
    link(ob, C_CITY)
    add_gn(ob, NG_GROWTH, bpy.data.collections[f"KIT_{era}"])
    log("city", era, len(idx))

idx = np.arange(len(D["t_x"]))[::SUB]
xyz = np.stack([D["t_x"][idx], D["t_y"][idx], D["t_z"][idx]], axis=1)
ob = point_cloud("TREES", xyz, {"death": ('FLOAT', D["t_death"][idx]), "rot": ('FLOAT', D["t_rot"][idx]),
                                "s": ('FLOAT', D["t_s"][idx] * TREE_SCALE), "kind": ('INT', D["t_kind"][idx])})
link(ob, C_TREES)
add_gn(ob, NG_TREE, bpy.data.collections["KIT_trees"])
log("trees", len(idx))

# ------------------------------------------------------------------ roads / rail / walls
MAT_ROAD = kits.material("road", (0.62, 0.54, 0.38), rough=0.95)
MAT_ASPHALT = kits.material("asphalt", (0.60, 0.58, 0.52), rough=0.95)
MAT_RAIL = kits.material("rail", (0.30, 0.28, 0.26), rough=0.95)
MAT_WALL = kits.material("wall", (0.72, 0.68, 0.58), rough=0.9)
MAT_WALLROOF = kits.material("wallroof", (0.32, 0.33, 0.36), rough=0.9)


def strips(pieces_xy, widths, z):
    p0 = pieces_xy[:, 0:2]; p1 = pieces_xy[:, 2:4]
    d = p1 - p0; L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    t = d / L; nrm = np.stack([-t[:, 1], t[:, 0]], axis=1)
    w = widths[:, None] / 2
    ext = t * np.minimum(w, 4.0)
    a = p0 - ext - nrm * w; b = p1 + ext - nrm * w; c = p1 + ext + nrm * w; dd = p0 - ext + nrm * w
    z = np.asarray(z)
    if z.ndim == 1:
        z0 = z1 = z
    else:
        z0, z1 = z[:, 0], z[:, 1]
    verts = np.concatenate([np.column_stack([a, z0]), np.column_stack([b, z1]), np.column_stack([c, z1]), np.column_stack([dd, z0])])
    n = len(p0)
    faces = np.stack([np.arange(n), np.arange(n) + n, np.arange(n) + 2 * n, np.arange(n) + 3 * n], axis=1)
    return verts, faces


roads = D["roads"]
over_water = roads[:, 7] > 0.5
zmid0 = sample_h(roads[:, 0], roads[:, 1]) + 0.45; zmid1 = sample_h(roads[:, 2], roads[:, 3]) + 0.45
zmid0 = np.where(over_water, 1.2, zmid0); zmid1 = np.where(over_water, 1.2, zmid1)     # small culverts over canals / docks
rw = roads[:, 4] * ROAD_W
rw = np.where(roads[:, 8] < 0.5, rw * 1.8, rw)
verts, faces = strips(roads[:, :4], rw, np.stack([zmid0, zmid1], axis=1))
mi = np.where(roads[:, 8] < 0.5, 1, 0)
ob = mesh_from_faces("ROADS", verts, faces, {"birth": roads[:, 5], "death": roads[:, 6]}, [MAT_ROAD, MAT_ASPHALT], mi)
link(ob, C_ROADS); add_gn(ob, NG_FACE)
log("roads", len(roads))

rail = D["rail"]
z0 = sample_h(rail[:, 0], rail[:, 1]) + 0.6; z1 = sample_h(rail[:, 2], rail[:, 3]) + 0.6
z0 = np.where(rail[:, 5] > 0.5, 6.0, z0); z1 = np.where(rail[:, 5] > 0.5, 6.0, z1)
verts, faces = strips(rail[:, :4], np.full(len(rail), 7.0), np.stack([z0, z1], axis=1))
ob = mesh_from_faces("RAIL", verts, faces, {"birth": rail[:, 4], "death": np.full(len(rail), 9999.0)}, [MAT_RAIL])
link(ob, C_ROADS); add_gn(ob, NG_FACE)
log("rail", len(rail))

walls = D["walls"]
bm = bmesh.new(); fb, fd = [], []
for x0, y0, x1, y1, b, d, h, tower in walls:
    zg = min(h_at(x0, y0), h_at(x1, y1))
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1:
        continue
    ang = math.atan2(dy, dx)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    nf0 = len(bm.faces)
    h = h * WALL_SCALE
    ww = 5.0 * WALL_SCALE
    kits._box(bm, 0, 0, 0, L + 1.0, ww, h, mat=0)
    kits._box(bm, 0, 0, h, L + 1.0, ww + 2, 1.2 * WALL_SCALE, mat=1)
    if tower > 0.5:
        kits._cylinder(bm, -L / 2, 0, 0, 0.8 * ww, h * 1.4, n=8, mat=0)
        kits._cone(bm, -L / 2, 0, h * 1.4, 0.9 * ww, 5 * WALL_SCALE, n=8, mat=1)
    M = Matrix.Translation((cx, cy, zg)) @ Matrix.Rotation(ang, 4, 'Z')
    bm.faces.ensure_lookup_table()
    for f in bm.faces[nf0:]:
        for v in f.verts:
            if not v.tag:
                v.co = M @ v.co
                v.tag = True
        fb.append(b); fd.append(d)
me = bpy.data.meshes.new("WALLS"); bm.to_mesh(me); bm.free()
a = me.attributes.new("birth", 'FLOAT', 'FACE'); a.data.foreach_set("value", np.array(fb, dtype=np.float32))
a = me.attributes.new("death", 'FLOAT', 'FACE'); a.data.foreach_set("value", np.array(fd, dtype=np.float32))
me.materials.append(MAT_WALL); me.materials.append(MAT_WALLROOF)
ob = bpy.data.objects.new("WALLS", me); link(ob, C_WALLS); add_gn(ob, NG_FACE)
log("walls", len(fb))

# ------------------------------------------------------------------ baked images
def image_from_gray(name, arr, channels=None):
    h, w = (arr if arr is not None else channels[0]).shape
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    rgba = np.empty((h, w, 4), dtype=np.float32)
    if channels is None:
        rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = arr[::-1] / 255.0
    else:
        for i, ch in enumerate(channels):
            rgba[..., i] = ch[::-1] / 255.0
    rgba[..., 3] = 1.0
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = os.path.join(CACHE, name + ".png")
    img.file_format = 'PNG'
    img.save()
    img.colorspace_settings.name = 'Non-Color'
    return img


IMG_TERRAIN = image_from_gray("bake_terrain", None, channels=[R["shore_land"], R["park_year"], R["kind"]])
IMG_WATER = image_from_gray("bake_water", R["water_depth"])
log("images baked")


def add_map_nodes(nt, img, interp='Linear'):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.vector_type = 'POINT'
    mp.inputs["Scale"].default_value = (1.0 / (RX1 - RX0), 1.0 / (RY1 - RY0), 1.0)
    mp.inputs["Location"].default_value = (-RX0 / (RX1 - RX0), -RY0 / (RY1 - RY0), 0.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    it = nt.nodes.new("ShaderNodeTexImage"); it.image = img; it.interpolation = interp; it.extension = 'EXTEND'
    nt.links.new(mp.outputs["Vector"], it.inputs["Vector"])
    return it


# ------------------------------------------------------------------ terrain
GRID = 25.0
gx = np.arange(RX0, RX1 + 1, GRID); gy = np.arange(RY0, RY1 + 1, GRID)
GX, GY = np.meshgrid(gx, gy)
GZ = sample_h(GX.ravel(), GY.ravel()).reshape(GX.shape)
ci = np.clip(((GX - RX0) / CELL).astype(int), 0, NX - 1); ri = np.clip(((RY1 - GY) / CELL).astype(int), 0, NY - 1)
wet = WATER_R[ri, ci]
GZ = np.where(wet, -6.0, GZ)
nyv, nxv = GX.shape
verts = np.stack([GX.ravel(), GY.ravel(), GZ.ravel()], axis=1)
ii, jj = np.meshgrid(np.arange(nxv - 1), np.arange(nyv - 1))
i0 = (jj * nxv + ii).ravel()
faces = np.stack([i0, i0 + 1, i0 + nxv + 1, i0 + nxv], axis=1)
MAT_GROUND = bpy.data.materials.new("ground"); MAT_GROUND.use_nodes = True
nt = MAT_GROUND.node_tree; nt.nodes.clear()
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(bsdf.outputs[0], outn.inputs[0])
bsdf.inputs["Roughness"].default_value = 1.0; bsdf.inputs["Specular IOR Level"].default_value = 0.1
tex = add_map_nodes(nt, IMG_TERRAIN, 'Closest')
sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(tex.outputs["Color"], sep.inputs[0])
tex_lin = add_map_nodes(nt, IMG_TERRAIN, 'Linear')          # smooth shore band (no pixel steps at close range)
sep_lin = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(tex_lin.outputs["Color"], sep_lin.inputs[0])
tc = nt.nodes.new("ShaderNodeTexCoord")
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 0.0015; noise.inputs["Detail"].default_value = 3.0
nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
noise2 = nt.nodes.new("ShaderNodeTexNoise"); noise2.inputs["Scale"].default_value = 0.06; noise2.inputs["Detail"].default_value = 2.0
nt.links.new(tc.outputs["Object"], noise2.inputs["Vector"])
g1 = nt.nodes.new("ShaderNodeMixRGB"); g1.blend_type = 'MIX'
g1.inputs[1].default_value = (0.09, 0.135, 0.04, 1); g1.inputs[2].default_value = (0.15, 0.19, 0.065, 1)
nt.links.new(noise.outputs["Fac"], g1.inputs[0])
g2 = nt.nodes.new("ShaderNodeMixRGB"); g2.blend_type = 'MULTIPLY'; g2.inputs[0].default_value = 0.25
nt.links.new(g1.outputs[0], g2.inputs[1]); nt.links.new(noise2.outputs["Fac"], g2.inputs[2])
year_node = nt.nodes.new("ShaderNodeValue"); year_node.name = "Year"; year_node.label = "Year"
enc255 = nt.nodes.new("ShaderNodeMath"); enc255.operation = 'MULTIPLY'; enc255.inputs[1].default_value = 255.0
nt.links.new(sep.outputs[1], enc255.inputs[0])
dec = nt.nodes.new("ShaderNodeMath"); dec.operation = 'MULTIPLY_ADD'; dec.inputs[1].default_value = 2400.0 / 254.0; dec.inputs[2].default_value = -300.0 - 2400.0 / 254.0
nt.links.new(enc255.outputs[0], dec.inputs[0])
isgreen = nt.nodes.new("ShaderNodeMath"); isgreen.operation = 'GREATER_THAN'; isgreen.inputs[1].default_value = 0.002
nt.links.new(sep.outputs[1], isgreen.inputs[0])
born = nt.nodes.new("ShaderNodeMath"); born.operation = 'GREATER_THAN'
nt.links.new(year_node.outputs[0], born.inputs[0]); nt.links.new(dec.outputs[0], born.inputs[1])
parkfac0 = nt.nodes.new("ShaderNodeMath"); parkfac0.operation = 'MULTIPLY'
nt.links.new(isgreen.outputs[0], parkfac0.inputs[0]); nt.links.new(born.outputs[0], parkfac0.inputs[1])
kind_is_park = nt.nodes.new("ShaderNodeMath"); kind_is_park.operation = 'GREATER_THAN'; kind_is_park.inputs[1].default_value = 0.2
nt.links.new(sep.outputs[2], kind_is_park.inputs[0])
parkfac = nt.nodes.new("ShaderNodeMath"); parkfac.operation = 'MULTIPLY'
nt.links.new(parkfac0.outputs[0], parkfac.inputs[0]); nt.links.new(kind_is_park.outputs[0], parkfac.inputs[1])
isforest = nt.nodes.new("ShaderNodeMath"); isforest.operation = 'GREATER_THAN'; isforest.inputs[1].default_value = 0.9
nt.links.new(sep.outputs[2], isforest.inputs[0])
isheath = nt.nodes.new("ShaderNodeMath"); isheath.operation = 'GREATER_THAN'; isheath.inputs[1].default_value = 0.7
nt.links.new(sep.outputs[2], isheath.inputs[0])
parkcol = nt.nodes.new("ShaderNodeMixRGB"); parkcol.inputs[1].default_value = (0.20, 0.36, 0.08, 1); parkcol.inputs[2].default_value = (0.09, 0.15, 0.045, 1)
nt.links.new(isforest.outputs[0], parkcol.inputs[0])
heathcol = nt.nodes.new("ShaderNodeMixRGB"); heathcol.inputs[2].default_value = (0.17, 0.24, 0.07, 1)
nt.links.new(isheath.outputs[0], heathcol.inputs[0]); nt.links.new(parkcol.outputs[0], heathcol.inputs[1])
# heath keeps the forest colour where forest, heath colour otherwise
mixpark = nt.nodes.new("ShaderNodeMixRGB"); nt.links.new(parkfac.outputs[0], mixpark.inputs[0])
nt.links.new(g2.outputs[0], mixpark.inputs[1]); nt.links.new(parkcol.outputs[0], mixpark.inputs[2])
# marsh (kind == 30/255) shown until its drainage year (same encoding as park years, reversed test)
ismarsh_lo = nt.nodes.new("ShaderNodeMath"); ismarsh_lo.operation = 'GREATER_THAN'; ismarsh_lo.inputs[1].default_value = 0.10
ismarsh_hi = nt.nodes.new("ShaderNodeMath"); ismarsh_hi.operation = 'LESS_THAN'; ismarsh_hi.inputs[1].default_value = 0.14
nt.links.new(sep.outputs[2], ismarsh_lo.inputs[0]); nt.links.new(sep.outputs[2], ismarsh_hi.inputs[0])
ismarsh = nt.nodes.new("ShaderNodeMath"); ismarsh.operation = 'MULTIPLY'
nt.links.new(ismarsh_lo.outputs[0], ismarsh.inputs[0]); nt.links.new(ismarsh_hi.outputs[0], ismarsh.inputs[1])
notborn = nt.nodes.new("ShaderNodeMath"); notborn.operation = 'SUBTRACT'; notborn.inputs[0].default_value = 1.0
nt.links.new(born.outputs[0], notborn.inputs[1])
marshfac = nt.nodes.new("ShaderNodeMath"); marshfac.operation = 'MULTIPLY'
nt.links.new(ismarsh.outputs[0], marshfac.inputs[0]); nt.links.new(notborn.outputs[0], marshfac.inputs[1])
marshmix = nt.nodes.new("ShaderNodeMixRGB"); marshmix.inputs[2].default_value = (0.13, 0.19, 0.10, 1)
nt.links.new(marshfac.outputs[0], marshmix.inputs[0]); nt.links.new(mixpark.outputs[0], marshmix.inputs[1])
sand = nt.nodes.new("ShaderNodeMixRGB"); sand.inputs[2].default_value = (0.42, 0.38, 0.22, 1)
nt.links.new(sep_lin.outputs[0], sand.inputs[0]); nt.links.new(marshmix.outputs[0], sand.inputs[1])
nt.links.new(sand.outputs[0], bsdf.inputs["Base Color"])
keyframe_year(year_node.outputs[0], ".default_value")

ob = mesh_from_faces("TERRAIN", verts, faces, None, [MAT_GROUND])
for p in ob.data.polygons:
    p.use_smooth = True
link(ob, C_ENV)
big = 300000.0
ob = mesh_from_faces("GROUND_FAR", [(-big, -big, -3.0), (big, -big, -3.0), (big, big, -3.0), (-big, big, -3.0)], [(0, 1, 2, 3)], None, [MAT_GROUND])
link(ob, C_ENV)
log("terrain", verts.shape)

# ------------------------------------------------------------------ water
# Flicker fix: no overlapping water surfaces (build_geo unions the layers), a calmer material
# (higher roughness, weak large-scale ripple instead of fine noise bump) and no per-frame animation.
MAT_WATER = bpy.data.materials.new("water"); MAT_WATER.use_nodes = True
nt = MAT_WATER.node_tree; nt.nodes.clear()
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(bsdf.outputs[0], outn.inputs[0])
bsdf.inputs["Roughness"].default_value = 0.45; bsdf.inputs["Specular IOR Level"].default_value = 0.35
tex = add_map_nodes(nt, IMG_WATER)
wc = nt.nodes.new("ShaderNodeMixRGB"); wc.inputs[1].default_value = (0.24, 0.42, 0.40, 1); wc.inputs[2].default_value = (0.07, 0.21, 0.25, 1)
nt.links.new(tex.outputs["Color"], wc.inputs[0])
nt.links.new(wc.outputs[0], bsdf.inputs["Base Color"])
rip = nt.nodes.new("ShaderNodeTexNoise"); rip.inputs["Scale"].default_value = 0.004; rip.inputs["Detail"].default_value = 2.0
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.025
nt.links.new(rip.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def fill_polygon_mesh(bm, outer, holes, z=0.0, zfn=None):
    edges = []
    for ring in [outer] + list(holes):
        pts = [tuple(p) for p in ring]
        if len(pts) > 1 and abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6:
            pts = pts[:-1]
        if len(pts) < 3:
            continue
        vs = [bm.verts.new((x, y, (zfn(x, y) if zfn else z))) for x, y in pts]
        for i in range(len(vs)):
            try:
                edges.append(bm.edges.new((vs[i], vs[(i + 1) % len(vs)])))
            except ValueError:
                pass
    nf0 = len(bm.faces)
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    bm.faces.ensure_lookup_table()
    return len(bm.faces) - nf0


# dock birth years from the researched water events (polygons that intersect a dock polygon)
def _bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


dock_events = [(_bbox(w["outer"]), w) for w in META["water_events"] if w["birth"] > -9000]


def dock_birth(outer):
    x0, y0, x1, y1 = _bbox(outer)
    best = None
    for (a0, b0, a1, b1), w in dock_events:
        if a0 <= x1 and a1 >= x0 and b0 <= y1 and b1 >= y0:
            best = w["birth"] if best is None else min(best, w["birth"])
    return best if best is not None else 1830


bm = bmesh.new()
fb, fd = [], []
nwater = 0
for w in META["water"]:
    if w["kind"] != "river" and w["area"] < 15000:
        continue
    if w["kind"] == "river":
        b, d = -9999.0, 9999.0
    elif w["kind"] == "dock":
        b, d = float(dock_birth(w["outer"])), 9999.0
    elif w["kind"] == "reservoir":
        b, d = 1860.0, 9999.0
    else:
        b, d = -9999.0, 9999.0
    n = fill_polygon_mesh(bm, w["outer"], w["holes"])
    fb += [b] * n; fd += [d] * n
    nwater += 1
me = bpy.data.meshes.new("WATER"); bm.to_mesh(me); bm.free()
a = me.attributes.new("birth", 'FLOAT', 'FACE'); a.data.foreach_set("value", np.array(fb, dtype=np.float32))
a = me.attributes.new("death", 'FLOAT', 'FACE'); a.data.foreach_set("value", np.array(fd, dtype=np.float32))
me.materials.append(MAT_WATER)
ob = bpy.data.objects.new("WATER", me); ob.location.z = WATER_Z; link(ob, C_ENV); add_gn(ob, NG_FACE)
log("water polys", nwater, "faces", len(me.polygons))

# canals as strips following the terrain
cpieces, cbirth = [], []


def canal_year(name):
    for k, v in history.CANAL_YEARS.items():
        if k.lower() in (name or "").lower():
            return v
    return -9999 if not name else 1810      # unnamed waterways are natural streams; named unknown ones canals


for c in META["canals"]:
    pts = c["pts"]
    yr = canal_year(c.get("name", ""))
    for i in range(len(pts) - 1):
        cpieces.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c["width"]))
        cbirth.append(yr)
if cpieces:
    cp = np.array(cpieces, dtype=np.float32)
    zc = np.stack([sample_h(cp[:, 0], cp[:, 1]) + 0.25, sample_h(cp[:, 2], cp[:, 3]) + 0.25], axis=1)
    verts, faces = strips(cp[:, :4], cp[:, 4], zc)
    ob = mesh_from_faces("CANALS", verts, faces, {"birth": np.array(cbirth, dtype=np.float32), "death": np.full(len(cp), 9999.0)}, [MAT_WATER])
    link(ob, C_ENV); add_gn(ob, NG_FACE)

# historic water (lost rivers, pre-embankment foreshore, filled docks): terrain-following surfaces with a lifetime
bm = bmesh.new(); fb, fd = [], []
for w in META["water_events"]:
    if w["death"] >= 9000:
        continue          # docks that still exist are in WATER
    n = fill_polygon_mesh(bm, w["outer"], w["holes"], zfn=lambda x, y: max(h_at(x, y) + 0.3, WATER_Z + 0.05))
    fb += [w["birth"]] * n; fd += [w["death"]] * n
me = bpy.data.meshes.new("WATER_HIST"); bm.to_mesh(me); bm.free()
if len(fb):
    a = me.attributes.new("birth", 'FLOAT', 'FACE'); a.data.foreach_set("value", np.array(fb, dtype=np.float32))
    a = me.attributes.new("death", 'FLOAT', 'FACE'); a.data.foreach_set("value", np.array(fd, dtype=np.float32))
    me.materials.append(MAT_WATER)
    ob = bpy.data.objects.new("WATER_HIST", me); link(ob, C_ENV); add_gn(ob, NG_FACE)
log("historic water faces", len(fb))


# ------------------------------------------------------------------ animated holders (landmarks, bridges)
def animate_holder(holder, birth, death, S):
    fb = frame_of_year(birth); fdth = frame_of_year(death) if death < 9000 else None
    pop = 1.6 * FPS
    holder.scale = (0.001, 0.001, 0.001); holder.keyframe_insert("scale", frame=fb - 1)
    holder.hide_render = True; holder.keyframe_insert("hide_render", frame=fb - 1)
    holder.hide_render = False; holder.keyframe_insert("hide_render", frame=fb)
    holder.scale = S; holder.keyframe_insert("scale", frame=fb + pop)
    if fdth:
        holder.scale = S; holder.keyframe_insert("scale", frame=fdth - 12)
        holder.scale = (0.001, 0.001, 0.001); holder.keyframe_insert("scale", frame=fdth)
        holder.hide_render = False; holder.keyframe_insert("hide_render", frame=fdth - 1)
        holder.hide_render = True; holder.keyframe_insert("hide_render", frame=fdth)
    for fc in holder.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER' if fc.data_path == "scale" else 'CONSTANT'
            kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'


# ------------------------------------------------------------------ landmarks
n_lm = 0
for entry in history.LANDMARKS:
    name, x, y, rot, birth, death, builder, prm = entry
    if builder is None:
        continue
    try:
        ob, base = landmarks.build_landmark(entry, C_LM)
    except Exception as e:  # noqa
        log("landmark failed", name, builder, e); continue
    z = h_at(x, y)
    holder = bpy.data.objects.new("LMH_" + name, None)
    link(holder, C_LM)
    holder.location = (x, y, z)
    holder.rotation_euler = (0, 0, math.radians(rot))
    ob.parent = holder
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_basis = base
    S = (1.0, 1.0, 1.0) if builder in ("airport",) else (LM_SCALE_XY, LM_SCALE_XY, LM_SCALE_Z)
    animate_holder(holder, birth, death, S)
    n_lm += 1
log("landmarks placed", n_lm)


# ------------------------------------------------------------------ bridges: one clean deck per historical bridge
def crossing(x, y):
    """(angle, span) of the shortest land-to-land line through the water at (x, y)."""
    best = None
    for deg in range(0, 180, 4):
        a = math.radians(deg)
        dx, dy = math.cos(a), math.sin(a)
        ends = []
        for s in (1, -1):
            k = 0
            while k < 120 and is_water(x + s * dx * k * 5, y + s * dy * k * 5):
                k += 1
            ends.append(k * 5)
        span = ends[0] + ends[1]
        if best is None or span < best[1]:
            best = (a, span, ends)
    return best


n_br = 0
for b in META["bridges"]:
    x, y = b["x"], b["y"]
    if abs(x) > 25000 or abs(y) > 19000:
        continue
    if not is_water(x, y):
        # nudge onto the water if the mid-span coordinate is slightly off
        found = False
        for r_ in (20, 40, 60, 90, 120):
            for deg in range(0, 360, 30):
                xx, yy = x + r_ * math.cos(math.radians(deg)), y + r_ * math.sin(math.radians(deg))
                if is_water(xx, yy):
                    x, y = xx, yy; found = True; break
            if found:
                break
        if not found:
            log("bridge not on water", b["id"]); continue
    ang, span, ends = crossing(x, y)
    # recentre on the span
    cx = x + math.cos(ang) * (ends[0] - ends[1]) / 2; cy = y + math.sin(ang) * (ends[0] - ends[1]) / 2
    variants = [(b["id"], b["birth"], b["death"], None)]
    if b["id"].startswith("old_london_bridge"):
        variants = [(b["id"], b["birth"], 1762, "old_london_bridge"), (b["id"] + "_bare", 1762, b["death"], "old_london_bridge_bare")]
    for vid, vb, vd, glb in variants:
        bb = dict(b); bb["id"] = vid
        try:
            ob = landmarks.build_bridge(bb, C_BR, glb)
        except Exception as e:  # noqa
            log("bridge failed", vid, e); continue
        # fit the model length to the real span (+ abutments)
        L_model = max(ob.dimensions.x, 1.0)
        fit = (span + 16.0) / L_model
        holder = bpy.data.objects.new("BRH_" + vid, None)
        link(holder, C_BR)
        holder.location = (cx, cy, WATER_Z)
        holder.rotation_euler = (0, 0, ang)
        ob.parent = holder
        ob.matrix_parent_inverse = Matrix.Identity(4)
        animate_holder(holder, vb, vd, (fit, 1.25, LM_SCALE_Z))
        n_br += 1
log("bridges placed", n_br)

# ------------------------------------------------------------------ camera
# The Thames runs west-east: the camera sits south-south-west of the City and looks north-north-east,
# pulling back from Roman Londinium to the whole Greater London basin.
VIEW_W = [(0, 1000), (6, 1150), (12, 1500), (22, 2300), (34, 3200), (46, 4000), (60, 5000), (72, 6200), (84, 7600),
          (98, 9000), (110, 10500), (124, 13000), (141, 18000), (155, 26000), (166, 34000), (180, 36000)]
PITCH = [(0, 29), (30, 33), (60, 39), (100, 45), (140, 50), (180, 53)]
TARGET = [(0, 700, -150), (40, 500, -100), (90, 200, 200), (166, -300, 900), (180, -300, 900)]
HEADING = math.radians(68)
LENS = 35.0


def interp(keys, t, log_space=False):
    ts = [k[0] for k in keys]; vs = [k[1] for k in keys]
    if log_space:
        return float(np.exp(np.interp(t, ts, np.log(vs))))
    return float(np.interp(t, ts, vs))


world = bpy.data.worlds.new("World"); scene.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
bg = wn.nodes.new("ShaderNodeBackground"); wo = wn.nodes.new("ShaderNodeOutputWorld"); wn.links.new(bg.outputs[0], wo.inputs[0])
world.mist_settings.falloff = 'LINEAR'
cam_data = bpy.data.cameras.new("Camera"); cam_data.lens = LENS; cam_data.sensor_width = 36; cam_data.clip_start = 10; cam_data.clip_end = 300000
cam = bpy.data.objects.new("Camera", cam_data); link(cam, C_ENV); scene.camera = cam
target = bpy.data.objects.new("CamTarget", None); link(target, C_ENV)
con = cam.constraints.new('TRACK_TO'); con.target = target; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
hf = 2 * math.tan(math.atan(18 / LENS))
for f in range(1, FRAMES + 2, 5):
    t = (f - 1) / FPS
    W = interp(VIEW_W, t, True)
    pitch = math.radians(interp(PITCH, t))
    tx = float(np.interp(t, [k[0] for k in TARGET], [k[1] for k in TARGET]))
    ty = float(np.interp(t, [k[0] for k in TARGET], [k[2] for k in TARGET]))
    tz = h_at(tx, ty)
    dist = W / hf
    cx = tx - math.cos(HEADING) * dist * math.cos(pitch)
    cy = ty - math.sin(HEADING) * dist * math.cos(pitch)
    cz = tz + dist * math.sin(pitch)
    cam.location = (cx, cy, cz); cam.keyframe_insert("location", frame=f)
    target.location = (tx, ty, tz); target.keyframe_insert("location", frame=f)
    scene.world.mist_settings.start = dist * 0.85; scene.world.mist_settings.depth = dist * 1.7
    scene.world.mist_settings.keyframe_insert("start", frame=f); scene.world.mist_settings.keyframe_insert("depth", frame=f)
for o in (cam, target):
    for fc in o.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
log("camera")

# ------------------------------------------------------------------ light / world / render
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); link(sun, C_ENV)
sun.data.energy = 4.0; sun.data.angle = math.radians(1.5); sun.data.color = (1.0, 0.93, 0.80)
sun.rotation_euler = (math.radians(55), 0, math.radians(215))
bg.inputs[0].default_value = (0.66, 0.62, 0.54, 1); bg.inputs[1].default_value = 0.42
bpy.context.view_layer.use_pass_mist = True

scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 32
scene.eevee.use_shadows = True
scene.eevee.shadow_ray_count = 2
scene.eevee.shadow_step_count = 4
scene.eevee.use_raytracing = False
scene.eevee.use_volumetric_shadows = False
scene.render.resolution_x = 2560; scene.render.resolution_y = 1440; scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -0.45
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
scene.render.use_persistent_data = True

scene.use_nodes = True
ct = scene.node_tree; ct.nodes.clear()
rl = ct.nodes.new("CompositorNodeRLayers"); comp = ct.nodes.new("CompositorNodeComposite")
haze = ct.nodes.new("CompositorNodeMixRGB"); haze.blend_type = 'MIX'
haze.inputs[2].default_value = (0.40, 0.43, 0.30, 1.0)
mfac = ct.nodes.new("CompositorNodeMath"); mfac.operation = 'MULTIPLY'; mfac.inputs[1].default_value = 0.22
ct.links.new(rl.outputs["Mist"], mfac.inputs[0])
ct.links.new(mfac.outputs[0], haze.inputs[0]); ct.links.new(rl.outputs["Image"], haze.inputs[1])
hs = ct.nodes.new("CompositorNodeHueSat"); hs.inputs["Saturation"].default_value = 0.92; hs.inputs["Value"].default_value = 1.0
ct.links.new(haze.outputs[0], hs.inputs["Image"])
ct.links.new(hs.outputs[0], comp.inputs["Image"])

for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == "KITS":
        lc.exclude = True

bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT), compress=True)
log("saved", OUT)
