"""Procedural low-poly building / tree kits (run inside Blender).

Every kit variant is a single mesh object (metres, origin at ground centre)
with material slots [wall, roof, accent].  Kits are grouped per era:

  0 celtic     round thatched huts + longhouses
  1 roman      terracotta-roofed domus / insulae, cream walls
  2 medieval   narrow steep-gabled houses, salmon/brown roofs
  3 classical  3-4 storey slate-roofed hotels, off-white walls  (1500-1790)
  4 haussmann  5-6 storey beige blocks with zinc mansards       (1790-1914)
  5 modern     dense pink-beige blocks, flat roofs               (1914-2025)
  6 suburb     small hipped-roof pavillons, red/brown roofs
  7 slab       tall modern slabs / towers (outskirts, La Defense)

Palette values are linear RGB.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

ERA_NAMES = ["celtic", "roman", "medieval", "classical", "haussmann", "modern", "suburb", "slab"]
VARIANTS = 10

PALETTE = {
    # era: (wall colours, roof colours)
    "celtic": ([(0.55, 0.42, 0.28), (0.60, 0.48, 0.32), (0.50, 0.40, 0.26)],
               [(0.36, 0.30, 0.18), (0.42, 0.34, 0.20), (0.32, 0.27, 0.17)]),
    "roman": ([(0.86, 0.78, 0.62), (0.90, 0.84, 0.70), (0.82, 0.70, 0.52), (0.88, 0.80, 0.66)],
              [(0.72, 0.18, 0.10), (0.78, 0.22, 0.12), (0.66, 0.16, 0.09), (0.80, 0.28, 0.15)]),
    "medieval": ([(0.78, 0.62, 0.42), (0.72, 0.55, 0.36), (0.82, 0.66, 0.46), (0.68, 0.52, 0.36)],
                 [(0.70, 0.24, 0.10), (0.60, 0.19, 0.08), (0.78, 0.30, 0.12), (0.52, 0.17, 0.08), (0.74, 0.27, 0.11)]),
    "classical": ([(0.88, 0.84, 0.74), (0.92, 0.88, 0.78), (0.84, 0.80, 0.70), (0.90, 0.85, 0.72)],
                  [(0.46, 0.45, 0.45), (0.40, 0.40, 0.41), (0.50, 0.49, 0.48), (0.36, 0.36, 0.37)]),
    "haussmann": ([(0.88, 0.76, 0.60), (0.84, 0.72, 0.56), (0.92, 0.80, 0.64), (0.82, 0.70, 0.54)],
                  [(0.52, 0.47, 0.44), (0.46, 0.42, 0.40), (0.56, 0.50, 0.46), (0.42, 0.38, 0.36)]),
    "modern": ([(0.86, 0.70, 0.60), (0.82, 0.66, 0.56), (0.90, 0.74, 0.64), (0.78, 0.64, 0.56)],
               [(0.64, 0.52, 0.46), (0.58, 0.48, 0.42), (0.68, 0.56, 0.48), (0.54, 0.44, 0.40)]),
    "suburb": ([(0.88, 0.76, 0.64), (0.92, 0.80, 0.68), (0.84, 0.72, 0.60)],
               [(0.66, 0.32, 0.20), (0.56, 0.30, 0.20), (0.58, 0.44, 0.36), (0.70, 0.40, 0.26)]),
    "slab": ([(0.78, 0.74, 0.70), (0.72, 0.70, 0.68), (0.66, 0.66, 0.66), (0.80, 0.76, 0.72)],
             [(0.50, 0.48, 0.46), (0.44, 0.44, 0.44)]),
}

_MATS = {}


TONE = 0.72   # global albedo multiplier: the film's palette is muted


def material(name, rgb, rough=0.85, spec=0.2):
    if name in _MATS:
        return _MATS[name]
    rgb = tuple(c * TONE for c in rgb)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        nt.nodes.clear()
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        outn = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs[0], outn.inputs[0])
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = spec
    m.diffuse_color = (*rgb, 1.0)
    _MATS[name] = m
    return m


def era_materials(era, variant, rng):
    walls, roofs = PALETTE[era]
    w = walls[variant % len(walls)]
    r = roofs[variant % len(roofs)]
    mw = material(f"{era}_wall_{variant % len(walls)}", w)
    mr = material(f"{era}_roof_{variant % len(roofs)}", r, rough=0.8)
    ma = material(f"{era}_accent", tuple(c * 0.55 for c in w), rough=0.9)
    return mw, mr, ma


# ---------------------------------------------------------------- primitives

def _box(bm, cx, cy, z0, w, d, h, mat=0):
    """Axis aligned box, returns list of faces."""
    verts = []
    for dz in (z0, z0 + h):
        for dx, dy in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
            verts.append(bm.verts.new((cx + dx, cy + dy, dz)))
    f = [
        (0, 3, 2, 1), (4, 5, 6, 7),
        (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    faces = []
    for idx in f:
        face = bm.faces.new([verts[i] for i in idx])
        face.material_index = mat
        faces.append(face)
    return faces


def _gable_roof(bm, cx, cy, z0, w, d, h, overhang=0.35, mat=1, along_x=True):
    """Prism roof.  Ridge runs along X if along_x else along Y."""
    if not along_x:
        w, d = d, w
    ow, od = w / 2 + overhang, d / 2 + overhang
    pts = [(-ow, -od, 0), (ow, -od, 0), (ow, od, 0), (-ow, od, 0),
           (-ow, 0, h), (ow, 0, h)]
    if not along_x:
        pts = [(y, x, z) for (x, y, z) in pts]
    vs = [bm.verts.new((cx + x, cy + y, z0 + z)) for (x, y, z) in pts]
    faces_idx = [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4), (3, 2, 1, 0)]
    for idx in faces_idx:
        face = bm.faces.new([vs[i] for i in idx])
        face.material_index = mat if len(idx) == 4 and idx != (3, 2, 1, 0) else (0 if len(idx) == 3 else mat)
    return vs


def _hip_roof(bm, cx, cy, z0, w, d, h, ridge_frac=0.5, overhang=0.3, mat=1):
    ow, od = w / 2 + overhang, d / 2 + overhang
    rl = max(0.0, (w - d) * 0.5 * ridge_frac) if w >= d else 0.0
    rd = max(0.0, (d - w) * 0.5 * ridge_frac) if d > w else 0.0
    pts = [(-ow, -od, 0), (ow, -od, 0), (ow, od, 0), (-ow, od, 0),
           (-rl, -rd, h), (rl, rd, h)]
    if w >= d:
        pts[4] = (-rl, 0, h); pts[5] = (rl, 0, h)
    else:
        pts[4] = (0, -rd, h); pts[5] = (0, rd, h)
    vs = [bm.verts.new((cx + x, cy + y, z0 + z)) for (x, y, z) in pts]
    if w >= d:
        idx = [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4), (3, 2, 1, 0)]
    else:
        idx = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5), (3, 2, 1, 0)]
    for i in idx:
        face = bm.faces.new([vs[j] for j in i])
        face.material_index = mat
    return vs


def _mansard(bm, cx, cy, z0, w, d, h_low, h_top, inset, mat=1):
    """Mansard: steep lower slope (inset) then shallow top."""
    ow, od = w / 2 + 0.15, d / 2 + 0.15
    iw, idp = ow - inset, od - inset
    base = [(-ow, -od, 0), (ow, -od, 0), (ow, od, 0), (-ow, od, 0)]
    mid = [(-iw, -idp, h_low), (iw, -idp, h_low), (iw, idp, h_low), (-iw, idp, h_low)]
    top = [(-iw * 0.55, -idp * 0.4, h_low + h_top), (iw * 0.55, -idp * 0.4, h_low + h_top),
           (iw * 0.55, idp * 0.4, h_low + h_top), (-iw * 0.55, idp * 0.4, h_low + h_top)]
    vs = [bm.verts.new((cx + x, cy + y, z0 + z)) for (x, y, z) in base + mid + top]
    for i in range(4):
        j = (i + 1) % 4
        f = bm.faces.new([vs[i], vs[j], vs[4 + j], vs[4 + i]]); f.material_index = mat
        f = bm.faces.new([vs[4 + i], vs[4 + j], vs[8 + j], vs[8 + i]]); f.material_index = mat
    f = bm.faces.new([vs[8], vs[9], vs[10], vs[11]]); f.material_index = mat
    f = bm.faces.new([vs[3], vs[2], vs[1], vs[0]]); f.material_index = mat


def _cone(bm, cx, cy, z0, r, h, n=8, mat=1):
    ring = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z0)) for i in range(n)]
    apex = bm.verts.new((cx, cy, z0 + h))
    for i in range(n):
        f = bm.faces.new([ring[i], ring[(i + 1) % n], apex]); f.material_index = mat
    f = bm.faces.new(list(reversed(ring))); f.material_index = mat
    return ring


def _cylinder(bm, cx, cy, z0, r, h, n=8, mat=0):
    lo = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z0)) for i in range(n)]
    hi = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z0 + h)) for i in range(n)]
    for i in range(n):
        f = bm.faces.new([lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]]); f.material_index = mat
    f = bm.faces.new(hi); f.material_index = mat
    f = bm.faces.new(list(reversed(lo))); f.material_index = mat


def _chimney(bm, x, y, z, s=0.6, h=1.4):
    _box(bm, x, y, z, s, s, h, mat=2)


# ---------------------------------------------------------------- kit builders

def build_celtic(bm, v, rng):
    if v % 3 == 2:   # longhouse
        w, d, h = rng.uniform(9, 13), rng.uniform(4.5, 6), 2.2
        _box(bm, 0, 0, 0, w, d, h)
        _gable_roof(bm, 0, 0, h, w, d, rng.uniform(3.5, 4.5), overhang=0.6)
    else:
        r = rng.uniform(3.0, 4.5)
        _cylinder(bm, 0, 0, 0, r, 1.8, n=9)
        _cone(bm, 0, 0, 1.8, r + 0.7, rng.uniform(3.2, 4.5), n=9)
    return (8, 8)


def build_roman(bm, v, rng):
    if v % 4 == 3:   # atrium domus
        w, d = rng.uniform(14, 18), rng.uniform(12, 16)
        h = 4.0
        t = 3.6
        # ring of four wings around courtyard
        _box(bm, 0, -d / 2 + t / 2, 0, w, t, h)
        _box(bm, 0, d / 2 - t / 2, 0, w, t, h)
        _box(bm, -w / 2 + t / 2, 0, 0, t, d - 2 * t, h)
        _box(bm, w / 2 - t / 2, 0, 0, t, d - 2 * t, h)
        rh = 1.6
        _gable_roof(bm, 0, -d / 2 + t / 2, h, w, t, rh, overhang=0.4)
        _gable_roof(bm, 0, d / 2 - t / 2, h, w, t, rh, overhang=0.4)
        _gable_roof(bm, -w / 2 + t / 2, 0, h, t, d - 2 * t, rh, overhang=0.4, along_x=False)
        _gable_roof(bm, w / 2 - t / 2, 0, h, t, d - 2 * t, rh, overhang=0.4, along_x=False)
        return (w, d)
    if v % 4 == 2:   # insula, 3 floors
        w, d, h = rng.uniform(10, 14), rng.uniform(8, 11), rng.uniform(8, 10)
        _box(bm, 0, 0, 0, w, d, h)
        _hip_roof(bm, 0, 0, h, w, d, 1.8)
        return (w, d)
    w, d, h = rng.uniform(7, 11), rng.uniform(5, 8), rng.uniform(3.2, 4.5)
    _box(bm, 0, 0, 0, w, d, h)
    _gable_roof(bm, 0, 0, h, w, d, rng.uniform(1.6, 2.2), overhang=0.5)
    if rng.random() < 0.5:   # small annex
        aw, ad = w * 0.5, d * 0.6
        _box(bm, w / 2 + aw / 2 - 0.2, -d / 2 + ad / 2, 0, aw, ad, h * 0.7)
        _gable_roof(bm, w / 2 + aw / 2 - 0.2, -d / 2 + ad / 2, h * 0.7, aw, ad, 1.2, overhang=0.3, along_x=False)
    return (w, d)


def build_medieval(bm, v, rng):
    w, d = rng.uniform(5, 7.5), rng.uniform(6, 9)
    floors = rng.choice([2, 2, 3, 3, 4])
    h = floors * 2.6
    _box(bm, 0, 0, 0, w, d, h * 0.42)
    # jettied upper floors
    _box(bm, 0, 0, h * 0.42, w + 0.5, d + 0.3, h * 0.58)
    along_x = (v % 2 == 0)
    rh = rng.uniform(0.75, 1.0) * (d if along_x else w) * 0.9
    _gable_roof(bm, 0, 0, h, w + 0.5, d + 0.3, rh, overhang=0.35, along_x=along_x)
    _chimney(bm, rng.uniform(-w * 0.25, w * 0.25), rng.uniform(-d * 0.25, d * 0.25), h + rh * 0.35)
    return (w + 0.5, d + 0.3)


def build_classical(bm, v, rng):
    w, d = rng.uniform(11, 18), rng.uniform(9, 13)
    h = rng.choice([3, 4]) * 3.0
    _box(bm, 0, 0, 0, w, d, h)
    if v % 3 == 0:
        _mansard(bm, 0, 0, h, w, d, 2.6, 1.0, 1.2)
    else:
        _hip_roof(bm, 0, 0, h, w, d, rng.uniform(3.0, 4.2), ridge_frac=0.55)
    for _ in range(2):
        _chimney(bm, rng.uniform(-w * 0.35, w * 0.35), rng.uniform(-d * 0.3, d * 0.3), h + 2.2, s=0.7, h=1.6)
    return (w, d)


def build_haussmann(bm, v, rng):
    w, d = rng.uniform(16, 28), rng.uniform(12, 16)
    h = rng.choice([5, 6, 6]) * 3.1
    _box(bm, 0, 0, 0, w, d, h)
    _mansard(bm, 0, 0, h, w, d, 2.4, 1.2, 1.5)
    n = int(w // 7)
    for i in range(n):
        _chimney(bm, -w / 2 + (i + 0.5) * w / n, rng.uniform(-d * 0.3, d * 0.3), h + 2.0, s=0.8, h=1.8)
    return (w, d)


def build_modern(bm, v, rng):
    w, d = rng.uniform(14, 24), rng.uniform(11, 16)
    h = rng.choice([5, 6, 7, 8]) * 3.0
    _box(bm, 0, 0, 0, w, d, h)
    if v % 3 == 0:
        _mansard(bm, 0, 0, h, w, d, 2.2, 1.0, 1.4)
    else:
        _box(bm, 0, 0, h, w * 0.96, d * 0.96, 0.6, mat=1)
        if rng.random() < 0.6:
            _box(bm, rng.uniform(-w * 0.2, w * 0.2), rng.uniform(-d * 0.2, d * 0.2), h + 0.6, 4, 3, 2.6, mat=2)
    return (w, d)


def build_suburb(bm, v, rng):
    w, d = rng.uniform(8, 12), rng.uniform(7, 10)
    h = rng.choice([1, 2, 2]) * 3.0
    _box(bm, 0, 0, 0, w, d, h)
    if v % 2:
        _hip_roof(bm, 0, 0, h, w, d, rng.uniform(2.4, 3.4), ridge_frac=0.5)
    else:
        _gable_roof(bm, 0, 0, h, w, d, rng.uniform(2.4, 3.2), overhang=0.5, along_x=w >= d)
    _chimney(bm, rng.uniform(-w * 0.3, w * 0.3), 0, h + 1.5, s=0.6, h=1.2)
    return (w, d)


def build_slab(bm, v, rng):
    if v % 3 == 0:   # tower
        w, d = rng.uniform(22, 30), rng.uniform(22, 30)
        h = rng.uniform(60, 110)
    else:            # slab
        w, d = rng.uniform(40, 70), rng.uniform(12, 16)
        h = rng.uniform(28, 45)
    _box(bm, 0, 0, 0, w, d, h)
    _box(bm, 0, 0, h, w * 0.97, d * 0.97, 0.8, mat=1)
    return (w, d)


BUILDERS = {
    "celtic": build_celtic, "roman": build_roman, "medieval": build_medieval,
    "classical": build_classical, "haussmann": build_haussmann, "modern": build_modern,
    "suburb": build_suburb, "slab": build_slab,
}


def make_kit_object(era, variant, collection):
    rng = random.Random(hash((era, variant)) & 0xFFFF)
    bm = bmesh.new()
    fw, fd = BUILDERS[era](bm, variant, rng)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    me = bpy.data.meshes.new(f"kit_{era}_{variant:02d}")
    bm.to_mesh(me); bm.free()
    mw, mr, ma = era_materials(era, variant, rng)
    me.materials.append(mw); me.materials.append(mr); me.materials.append(ma)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(me.name, me)
    ob["footprint_w"] = fw
    ob["footprint_d"] = fd
    collection.objects.link(ob)
    return ob


def build_all_kits(parent_collection):
    """Returns {era: [objects]} and creates one sub-collection per era."""
    kits = {}
    for era in ERA_NAMES:
        col = bpy.data.collections.new(f"KIT_{era}")
        parent_collection.children.link(col)
        kits[era] = [make_kit_object(era, v, col) for v in range(VARIANTS)]
    return kits


# ---------------------------------------------------------------- trees

TREE_GREENS = [(0.10, 0.22, 0.09), (0.13, 0.27, 0.11), (0.08, 0.19, 0.08), (0.15, 0.30, 0.12), (0.11, 0.24, 0.10)]


def make_tree(variant, collection):
    rng = random.Random(1000 + variant)
    bm = bmesh.new()
    trunk = material("tree_trunk", (0.25, 0.17, 0.10))
    leaf = material(f"tree_leaf_{variant % len(TREE_GREENS)}", TREE_GREENS[variant % len(TREE_GREENS)], rough=0.95)
    if variant % 3 == 2:    # conifer
        _cylinder(bm, 0, 0, 0, 0.35, 2.0, n=5, mat=0)
        _cone(bm, 0, 0, 1.6, rng.uniform(2.2, 3.0), rng.uniform(7, 10), n=7, mat=1)
    else:                    # broadleaf blob: low-poly icosphere squashed
        _cylinder(bm, 0, 0, 0, 0.4, 2.5, n=5, mat=0)
        r = rng.uniform(2.6, 3.6)
        res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        for vt in res["verts"]:
            vt.co.z = vt.co.z * rng.uniform(0.85, 1.1) + 2.5 + r * 0.8
            vt.co.x *= rng.uniform(0.9, 1.1); vt.co.y *= rng.uniform(0.9, 1.1)
        for f in bm.faces:
            if f.material_index == 0 and any(v in res["verts"] for v in f.verts):
                f.material_index = 1
    me = bpy.data.meshes.new(f"tree_{variant:02d}")
    bm.to_mesh(me); bm.free()
    me.materials.append(trunk); me.materials.append(leaf)
    ob = bpy.data.objects.new(me.name, me)
    collection.objects.link(ob)
    return ob


def build_trees(parent_collection, n=6):
    col = bpy.data.collections.new("KIT_trees")
    parent_collection.children.link(col)
    return [make_tree(v, col) for v in range(n)]
