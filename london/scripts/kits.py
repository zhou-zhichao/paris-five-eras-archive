"""Procedural low-poly building / tree kits for London (run inside Blender).

Every kit variant is a single mesh object (metres, origin at ground centre)
with material slots [wall, roof, accent].  Kits are grouped per era:

   0 celtic     round thatched huts + longhouses
   1 roman      terracotta-roofed domus / insulae, cream walls
   2 saxon      timber halls, thatched, steep roofs, dark timber
   3 medieval   narrow steep-gabled timber-framed houses, jettied
   4 tudor      timber-framed with brick chimneys, steep gables (1485-1670)
   5 georgian   brick terraces, 3-4 storeys, parapets, party-wall chimneys (1670-1837)
   6 victorian  stock-brick terraces with bays, slate roofs, warehouses, mansion blocks
   7 interwar   semi-detached pairs, hipped clay-tile roofs, bay windows
   8 postwar    3-5 storey brick / concrete flats, flat roofs (1945-1980)
   9 modern     4-9 storey glass / brick blocks, flat roofs (1980-2025)
  10 estate     11-storey slabs and 20-storey point blocks (council estates)
  11 tower      glass office / apartment towers (City, Docklands, Vauxhall...)

Palette values are linear RGB.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

ERA_NAMES = ["celtic", "roman", "saxon", "medieval", "tudor", "georgian", "victorian", "interwar", "postwar", "modern", "estate", "tower"]
VARIANTS = 10

# Palette history: 2026-09-08 lightened (walls ~0.75, roofs ~0.45) because dark slate + mid-brown walls read as a
# grey mush against the olive ground in the wide views; 2026-09-10 the user found the post-1666 city "pure white",
# so the Georgian / Victorian mass is back to sooty yellow stock brick (~0.55) and mid-dark slate (~0.38), with the
# red-brick share raised and cream stucco kept to one variant in five (only the Regency West End was stuccoed).
STOCK = [(0.58, 0.50, 0.36), (0.52, 0.46, 0.34), (0.64, 0.56, 0.41), (0.46, 0.41, 0.31)]     # weathered London stock brick
REDBRICK = [(0.62, 0.34, 0.25), (0.56, 0.31, 0.23), (0.68, 0.38, 0.28), (0.52, 0.29, 0.22)]
STUCCO = [(0.86, 0.83, 0.72), (0.80, 0.77, 0.66)]                                             # cream, not white
SLATE = [(0.38, 0.37, 0.37), (0.34, 0.33, 0.34), (0.42, 0.41, 0.40)]                          # Welsh slate
TILE = [(0.66, 0.34, 0.22), (0.58, 0.36, 0.26), (0.72, 0.40, 0.26)]                           # clay tiles (interwar suburbia)
PALETTE = {
    "celtic": ([(0.55, 0.42, 0.28), (0.60, 0.48, 0.32), (0.50, 0.40, 0.26)],
               [(0.36, 0.30, 0.18), (0.42, 0.34, 0.20), (0.32, 0.27, 0.17)]),
    "roman": ([(0.86, 0.78, 0.62), (0.90, 0.84, 0.70), (0.82, 0.70, 0.52), (0.88, 0.80, 0.66)],
              [(0.72, 0.18, 0.10), (0.78, 0.22, 0.12), (0.66, 0.16, 0.09), (0.80, 0.28, 0.15)]),
    "saxon": ([(0.50, 0.38, 0.24), (0.56, 0.44, 0.28), (0.46, 0.35, 0.22)],
              [(0.42, 0.34, 0.19), (0.38, 0.31, 0.18), (0.46, 0.37, 0.21)]),
    "medieval": ([(0.78, 0.66, 0.46), (0.72, 0.58, 0.40), (0.82, 0.70, 0.50), (0.68, 0.55, 0.38)],
                 [(0.62, 0.30, 0.18), (0.50, 0.24, 0.14), (0.66, 0.36, 0.20), (0.42, 0.26, 0.16), (0.58, 0.28, 0.16)]),
    "tudor": ([(0.84, 0.78, 0.62), (0.80, 0.72, 0.56), (0.62, 0.36, 0.26), (0.86, 0.80, 0.66)],
              [(0.58, 0.28, 0.18), (0.36, 0.30, 0.26), (0.52, 0.26, 0.16), (0.40, 0.34, 0.30)]),
    "georgian": (REDBRICK[:2] + STOCK[:2] + STUCCO[:1], SLATE + [(0.50, 0.30, 0.20)]),   # 1666 rebuild in red brick, stock later
    "victorian": (STOCK[:3] + REDBRICK[:2] + STUCCO[1:2], SLATE + [(0.52, 0.30, 0.22)]),
    "interwar": ([(0.72, 0.42, 0.32), (0.88, 0.84, 0.74), (0.66, 0.40, 0.30), (0.84, 0.78, 0.66)], TILE + [(0.54, 0.36, 0.26)]),
    "postwar": ([(0.78, 0.76, 0.72), (0.64, 0.48, 0.38), (0.82, 0.80, 0.76), (0.70, 0.56, 0.44)],
                [(0.52, 0.50, 0.46), (0.48, 0.47, 0.45), (0.56, 0.54, 0.50)]),
    "modern": ([(0.60, 0.68, 0.76), (0.84, 0.80, 0.74), (0.70, 0.54, 0.42), (0.66, 0.70, 0.74)],
               [(0.55, 0.56, 0.58), (0.50, 0.52, 0.54), (0.60, 0.60, 0.60)]),
    "estate": ([(0.78, 0.76, 0.74), (0.66, 0.60, 0.54), (0.74, 0.72, 0.68), (0.62, 0.62, 0.60)],
               [(0.50, 0.50, 0.52), (0.46, 0.46, 0.48)]),
    "tower": ([(0.36, 0.46, 0.56), (0.30, 0.38, 0.46), (0.44, 0.52, 0.58), (0.52, 0.56, 0.60), (0.40, 0.50, 0.52)],
              [(0.30, 0.32, 0.34), (0.36, 0.38, 0.40)]),
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
    mw = material(f"{era}_wall_{variant % len(walls)}", w, rough=0.9 if era != "tower" else 0.35, spec=0.2 if era != "tower" else 0.5)
    mr = material(f"{era}_roof_{variant % len(roofs)}", r, rough=0.8)
    ma = material(f"{era}_accent", tuple(c * 0.55 for c in w), rough=0.9)
    return mw, mr, ma


# ---------------------------------------------------------------- primitives

def _box(bm, cx, cy, z0, w, d, h, mat=0):
    verts = []
    for dz in (z0, z0 + h):
        for dx, dy in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
            verts.append(bm.verts.new((cx + dx, cy + dy, dz)))
    faces = []
    for idx in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        face = bm.faces.new([verts[i] for i in idx])
        face.material_index = mat
        faces.append(face)
    return faces


def _gable_roof(bm, cx, cy, z0, w, d, h, overhang=0.35, mat=1, along_x=True):
    if not along_x:
        w, d = d, w
    ow, od = w / 2 + overhang, d / 2 + overhang
    pts = [(-ow, -od, 0), (ow, -od, 0), (ow, od, 0), (-ow, od, 0), (-ow, 0, h), (ow, 0, h)]
    if not along_x:
        pts = [(y, x, z) for (x, y, z) in pts]
    vs = [bm.verts.new((cx + x, cy + y, z0 + z)) for (x, y, z) in pts]
    for idx in [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4), (3, 2, 1, 0)]:
        face = bm.faces.new([vs[i] for i in idx])
        face.material_index = mat if len(idx) == 4 and idx != (3, 2, 1, 0) else (0 if len(idx) == 3 else mat)
    return vs


def _hip_roof(bm, cx, cy, z0, w, d, h, ridge_frac=0.5, overhang=0.3, mat=1):
    ow, od = w / 2 + overhang, d / 2 + overhang
    rl = max(0.0, (w - d) * 0.5 * ridge_frac) if w >= d else 0.0
    rd = max(0.0, (d - w) * 0.5 * ridge_frac) if d > w else 0.0
    pts = [(-ow, -od, 0), (ow, -od, 0), (ow, od, 0), (-ow, od, 0), (-rl, -rd, h), (rl, rd, h)]
    if w >= d:
        pts[4] = (-rl, 0, h); pts[5] = (rl, 0, h)
    else:
        pts[4] = (0, -rd, h); pts[5] = (0, rd, h)
    vs = [bm.verts.new((cx + x, cy + y, z0 + z)) for (x, y, z) in pts]
    idx = [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4), (3, 2, 1, 0)] if w >= d else [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5), (3, 2, 1, 0)]
    for i in idx:
        face = bm.faces.new([vs[j] for j in i])
        face.material_index = mat
    return vs


def _mansard(bm, cx, cy, z0, w, d, h_low, h_top, inset, mat=1):
    ow, od = w / 2 + 0.15, d / 2 + 0.15
    iw, idp = ow - inset, od - inset
    base = [(-ow, -od, 0), (ow, -od, 0), (ow, od, 0), (-ow, od, 0)]
    mid = [(-iw, -idp, h_low), (iw, -idp, h_low), (iw, idp, h_low), (-iw, idp, h_low)]
    top = [(-iw * 0.55, -idp * 0.4, h_low + h_top), (iw * 0.55, -idp * 0.4, h_low + h_top), (iw * 0.55, idp * 0.4, h_low + h_top), (-iw * 0.55, idp * 0.4, h_low + h_top)]
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
    if v % 3 == 2:
        w, d, h = rng.uniform(9, 13), rng.uniform(4.5, 6), 2.2
        _box(bm, 0, 0, 0, w, d, h)
        _gable_roof(bm, 0, 0, h, w, d, rng.uniform(3.5, 4.5), overhang=0.6)
    else:
        r = rng.uniform(3.0, 4.5)
        _cylinder(bm, 0, 0, 0, r, 1.8, n=9)
        _cone(bm, 0, 0, 1.8, r + 0.7, rng.uniform(3.2, 4.5), n=9)
    return (8, 8)


def build_roman(bm, v, rng):
    if v % 4 == 3:
        w, d = rng.uniform(14, 18), rng.uniform(12, 16)
        h, t = 4.0, 3.6
        _box(bm, 0, -d / 2 + t / 2, 0, w, t, h); _box(bm, 0, d / 2 - t / 2, 0, w, t, h)
        _box(bm, -w / 2 + t / 2, 0, 0, t, d - 2 * t, h); _box(bm, w / 2 - t / 2, 0, 0, t, d - 2 * t, h)
        _gable_roof(bm, 0, -d / 2 + t / 2, h, w, t, 1.6, overhang=0.4); _gable_roof(bm, 0, d / 2 - t / 2, h, w, t, 1.6, overhang=0.4)
        _gable_roof(bm, -w / 2 + t / 2, 0, h, t, d - 2 * t, 1.6, overhang=0.4, along_x=False)
        _gable_roof(bm, w / 2 - t / 2, 0, h, t, d - 2 * t, 1.6, overhang=0.4, along_x=False)
        return (w, d)
    if v % 4 == 2:
        w, d, h = rng.uniform(10, 14), rng.uniform(8, 11), rng.uniform(8, 10)
        _box(bm, 0, 0, 0, w, d, h); _hip_roof(bm, 0, 0, h, w, d, 1.8)
        return (w, d)
    w, d, h = rng.uniform(7, 11), rng.uniform(5, 8), rng.uniform(3.2, 4.5)
    _box(bm, 0, 0, 0, w, d, h)
    _gable_roof(bm, 0, 0, h, w, d, rng.uniform(1.6, 2.2), overhang=0.5)
    if rng.random() < 0.5:
        aw, ad = w * 0.5, d * 0.6
        _box(bm, w / 2 + aw / 2 - 0.2, -d / 2 + ad / 2, 0, aw, ad, h * 0.7)
        _gable_roof(bm, w / 2 + aw / 2 - 0.2, -d / 2 + ad / 2, h * 0.7, aw, ad, 1.2, overhang=0.3, along_x=False)
    return (w, d)


def build_saxon(bm, v, rng):
    if v % 4 == 3:    # sunken hut
        w, d = rng.uniform(4, 5.5), rng.uniform(3, 4)
        _box(bm, 0, 0, 0, w, d, 0.8)
        _gable_roof(bm, 0, 0, 0.8, w, d, rng.uniform(2.2, 2.8), overhang=0.6)
        return (w + 1, d + 1)
    w, d, h = rng.uniform(9, 15), rng.uniform(5, 7), rng.uniform(1.8, 2.6)
    _box(bm, 0, 0, 0, w, d, h)
    _gable_roof(bm, 0, 0, h, w, d, rng.uniform(3.6, 5.0), overhang=0.7)
    return (w + 1, d + 1)


def build_medieval(bm, v, rng):
    w, d = rng.uniform(5, 7.5), rng.uniform(6, 9)
    floors = rng.choice([2, 2, 3, 3, 4])
    h = floors * 2.6
    _box(bm, 0, 0, 0, w, d, h * 0.42)
    _box(bm, 0, 0, h * 0.42, w + 0.5, d + 0.3, h * 0.58)
    along_x = (v % 2 == 0)
    rh = rng.uniform(0.75, 1.0) * (d if along_x else w) * 0.9
    _gable_roof(bm, 0, 0, h, w + 0.5, d + 0.3, rh, overhang=0.35, along_x=along_x)
    _chimney(bm, rng.uniform(-w * 0.25, w * 0.25), rng.uniform(-d * 0.25, d * 0.25), h + rh * 0.35)
    return (w + 0.5, d + 0.3)


def build_tudor(bm, v, rng):
    w, d = rng.uniform(6, 9), rng.uniform(7, 11)
    floors = rng.choice([2, 3, 3, 4])
    h = floors * 2.7
    _box(bm, 0, 0, 0, w, d, h * 0.38)
    _box(bm, 0, 0, h * 0.38, w + 0.6, d + 0.4, h * 0.32)
    _box(bm, 0, 0, h * 0.70, w + 1.0, d + 0.6, h * 0.30)
    along_x = (v % 3 != 0)
    rh = rng.uniform(0.8, 1.05) * (d if along_x else w) * 0.8
    _gable_roof(bm, 0, 0, h, w + 1.0, d + 0.6, rh, overhang=0.35, along_x=along_x)
    for _ in range(rng.choice([1, 2])):
        _chimney(bm, rng.uniform(-w * 0.3, w * 0.3), rng.uniform(-d * 0.3, d * 0.3), h + rh * 0.3, s=0.9, h=rh * 0.75 + 1.0)
    return (w + 1.0, d + 0.6)


def build_georgian(bm, v, rng):
    # a run of 2-3 terrace houses as one instance: flat parapet, shallow hidden roof, party-wall chimney stacks
    n = rng.choice([2, 2, 3])
    hw = rng.uniform(5.5, 7.5)
    w, d = n * hw, rng.uniform(10, 13)
    h = rng.choice([3, 3, 4]) * 3.2
    _box(bm, 0, 0, 0, w, d, h)
    _box(bm, 0, 0, h, w, d, 0.9, mat=0)                                  # parapet
    _hip_roof(bm, 0, 0, h + 0.9, w - 0.6, d - 0.6, 2.2, ridge_frac=0.7, overhang=0.0)
    for i in range(n + 1):
        x = -w / 2 + i * hw
        _chimney(bm, x, rng.uniform(-d * 0.2, d * 0.2), h + 0.9, s=1.0, h=2.6)
    if v % 3 == 0:     # stucco ground floor / porch band
        _box(bm, 0, -d / 2 - 0.3, 0, w, 0.6, 3.2, mat=2)
    return (w, d)


def build_victorian(bm, v, rng):
    if v % 5 == 4:     # warehouse / mansion block
        w, d = rng.uniform(16, 26), rng.uniform(12, 18)
        h = rng.choice([4, 5, 6]) * 3.4
        _box(bm, 0, 0, 0, w, d, h)
        _box(bm, 0, 0, h, w, d, 0.8, mat=0)
        _hip_roof(bm, 0, 0, h + 0.8, w - 0.6, d - 0.6, 2.5, ridge_frac=0.6, overhang=0.0)
        n = int(w // 8)
        for i in range(n):
            _chimney(bm, -w / 2 + (i + 0.5) * w / n, rng.uniform(-d * 0.25, d * 0.25), h + 0.8, s=1.0, h=2.4)
        return (w, d)
    n = rng.choice([2, 3, 3, 4])
    hw = rng.uniform(4.6, 6.0)
    w, d = n * hw, rng.uniform(9, 12)
    h = rng.choice([2, 2, 3]) * 3.1
    _box(bm, 0, 0, 0, w, d, h)
    _gable_roof(bm, 0, 0, h, w, d, rng.uniform(3.0, 3.8), overhang=0.3, along_x=True)
    for i in range(n + 1):
        x = -w / 2 + i * hw
        _chimney(bm, x, 0, h + 1.2, s=0.9, h=3.2)
    for i in range(n):        # bay windows on the street side
        x = -w / 2 + (i + 0.5) * hw
        _box(bm, x, -d / 2 - 0.9, 0, hw * 0.55, 1.8, min(h, 6.2), mat=0)
    return (w, d + 1.8)


def build_interwar(bm, v, rng):
    if v % 4 == 3:     # short terrace / detached
        w, d = rng.uniform(8, 11), rng.uniform(8, 10)
    else:              # semi-detached pair
        w, d = rng.uniform(13, 16), rng.uniform(8.5, 10.5)
    h = 2 * 2.8
    _box(bm, 0, 0, 0, w, d, h)
    _hip_roof(bm, 0, 0, h, w, d, rng.uniform(3.2, 4.0), ridge_frac=0.55, overhang=0.5)
    for sx in (-1, 1):
        _box(bm, sx * w * 0.25, -d / 2 - 0.7, 0, w * 0.22, 1.4, 5.0, mat=0)    # bays
        _hip_roof(bm, sx * w * 0.25, -d / 2 - 0.7, 5.0, w * 0.22, 1.4, 1.0, overhang=0.2)
    _chimney(bm, 0, 0, h + 1.8, s=0.9, h=2.4)
    return (w, d + 1.4)


def build_postwar(bm, v, rng):
    if v % 3 == 2:     # low terrace
        w, d, h = rng.uniform(18, 28), rng.uniform(8, 10), 2 * 2.7
        _box(bm, 0, 0, 0, w, d, h)
        _gable_roof(bm, 0, 0, h, w, d, 2.4, overhang=0.3)
        return (w, d)
    w, d = rng.uniform(22, 36), rng.uniform(10, 14)
    h = rng.choice([3, 4, 4, 5]) * 2.9
    _box(bm, 0, 0, 0, w, d, h)
    _box(bm, 0, 0, h, w * 0.98, d * 0.98, 0.6, mat=1)
    for i in range(int(h // 2.9)):     # balcony bands
        _box(bm, 0, -d / 2 - 0.5, 2.9 * i + 1.0, w * 0.9, 1.0, 0.25, mat=2)
    return (w, d + 1.0)


def build_modern(bm, v, rng):
    w, d = rng.uniform(16, 30), rng.uniform(12, 18)
    h = rng.choice([4, 5, 6, 7, 9]) * 3.1
    _box(bm, 0, 0, 0, w, d, h)
    _box(bm, 0, 0, h, w * 0.96, d * 0.96, 0.6, mat=1)
    if v % 3 == 0:
        _box(bm, rng.uniform(-w * 0.2, w * 0.2), rng.uniform(-d * 0.2, d * 0.2), h + 0.6, 5, 4, 3.0, mat=2)
    if v % 2 == 0:     # stepped upper floor
        _box(bm, 0, d * 0.1, h, w * 0.7, d * 0.7, 3.0, mat=0)
    return (w, d)


def build_estate(bm, v, rng):
    if v % 3 == 0:     # point block
        w, d = rng.uniform(22, 28), rng.uniform(22, 28)
        h = rng.uniform(55, 70)
        _box(bm, 0, 0, 0, w, d, h)
        _box(bm, 0, 0, h, w * 0.97, d * 0.97, 0.8, mat=1)
        _box(bm, w * 0.2, d * 0.2, h + 0.8, 6, 6, 3.5, mat=2)
    else:              # slab
        w, d = rng.uniform(55, 85), rng.uniform(12, 15)
        h = rng.uniform(28, 40)
        _box(bm, 0, 0, 0, w, d, h)
        _box(bm, 0, 0, h, w * 0.97, d * 0.97, 0.8, mat=1)
        for i in range(int(h // 2.8)):
            _box(bm, 0, -d / 2 - 0.5, 2.8 * i + 1.0, w * 0.92, 1.0, 0.3, mat=2)
    return (w, d)


def build_tower(bm, v, rng):
    kind = v % 4
    if kind == 0:      # plain glass box
        w, d = rng.uniform(32, 45), rng.uniform(28, 40)
        h = rng.uniform(90, 140)
        _box(bm, 0, 0, 0, w, d, h)
        _box(bm, 0, 0, h, w * 0.6, d * 0.6, 4, mat=1)
    elif kind == 1:    # tapered / stepped
        w, d = rng.uniform(36, 48), rng.uniform(30, 40)
        h = rng.uniform(100, 150)
        _box(bm, 0, 0, 0, w, d, h * 0.55)
        _box(bm, 0, 0, h * 0.55, w * 0.8, d * 0.8, h * 0.3)
        _box(bm, 0, 0, h * 0.85, w * 0.6, d * 0.6, h * 0.15)
    elif kind == 2:    # rounded drum
        r = rng.uniform(16, 22)
        h = rng.uniform(90, 130)
        _cylinder(bm, 0, 0, 0, r, h, n=16)
        _cylinder(bm, 0, 0, h, r * 0.5, 4, n=16, mat=1)
        w = d = r * 2
    else:              # slab with a podium
        w, d = rng.uniform(40, 55), rng.uniform(18, 26)
        h = rng.uniform(80, 120)
        _box(bm, 0, 0, 0, w * 1.4, d * 1.6, 12, mat=2)
        _box(bm, 0, 0, 12, w, d, h - 12)
        _box(bm, 0, 0, h, w * 0.96, d * 0.96, 2, mat=1)
        w, d = w * 1.4, d * 1.6
    return (w, d)


BUILDERS = {
    "celtic": build_celtic, "roman": build_roman, "saxon": build_saxon, "medieval": build_medieval, "tudor": build_tudor,
    "georgian": build_georgian, "victorian": build_victorian, "interwar": build_interwar, "postwar": build_postwar,
    "modern": build_modern, "estate": build_estate, "tower": build_tower,
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
    if variant % 3 == 2:
        _cylinder(bm, 0, 0, 0, 0.35, 2.0, n=5, mat=0)
        _cone(bm, 0, 0, 1.6, rng.uniform(2.2, 3.0), rng.uniform(7, 10), n=7, mat=1)
    else:
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
