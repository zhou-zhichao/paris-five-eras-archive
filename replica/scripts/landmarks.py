"""Landmark builders (run inside Blender): procedural monuments + GLB imports with flat materials."""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix
import kits

GLB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "models")
GLB_FILES = {
    "notre_dame": "notre-dame-clean-200k.glb",
    "eiffel": "eiffel_tower_low_poly.glb",
    "louvre": "louvre.glb",
    "arc_de_triomphe": "arc_de_triomphe.glb",
    "gare_du_nord": "gare_du_nord.glb",
    "palais_garnier": "palais_garnier.glb",
    "sainte_chapelle": "sainte_chapelle.glb",
    "saint_germain_des_pres": "saint_germain_des_pres.glb",
    "tour_du_temple": "tour_du_temple.glb",
    "petit_pont_petit_chatelet": "petit_pont_petit_chatelet.glb",
}
# extra yaw (deg) so the model's long axis / facade sits right, and which axis is "long" in the file
GLB_YAW = {"louvre": 90, "gare_du_nord": 90, "saint_germain_des_pres": 90, "notre_dame": 180, "sainte_chapelle": 0}

STONE = (0.86, 0.82, 0.72)
STONE_DARK = (0.70, 0.66, 0.58)
ROOF_SLATE = (0.30, 0.31, 0.35)
ROOF_TILE = (0.72, 0.20, 0.11)
ROOF_LEAD = (0.45, 0.47, 0.50)
GOLD = (0.85, 0.65, 0.25)
WHITE = (0.93, 0.92, 0.88)
IRON = (0.25, 0.20, 0.17)
CONCRETE = (0.75, 0.74, 0.72)
GLASS = (0.55, 0.65, 0.72)
WOOD = (0.45, 0.33, 0.20)
GRASS = (0.42, 0.58, 0.25)
GRAVEL = (0.80, 0.74, 0.60)


def _mat(name, rgb):
    return kits.material("lm_" + name, rgb)


def _new_bm():
    return bmesh.new()


def _finish(bm, name, mats):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    return ob


B = kits._box
CYL = kits._cylinder
CONE = kits._cone
HIP = kits._hip_roof
GABLE = kits._gable_roof


def _dome(bm, cx, cy, z0, r, h, mat=1, seg=12, rings=5):
    prev = None
    for i in range(rings + 1):
        phi = (math.pi / 2) * i / rings
        rr = r * math.cos(phi); zz = z0 + h * math.sin(phi)
        ring = [bm.verts.new((cx + rr * math.cos(2 * math.pi * k / seg), cy + rr * math.sin(2 * math.pi * k / seg), zz)) for k in range(seg)]
        if prev is not None:
            for k in range(seg):
                if i == rings:
                    f = bm.faces.new([prev[k], prev[(k + 1) % seg], ring[k]])
                else:
                    f = bm.faces.new([prev[k], prev[(k + 1) % seg], ring[(k + 1) % seg], ring[k]])
                f.material_index = mat
        prev = ring


def _tower(bm, cx, cy, z0, r, h, roof_h, mat_wall=0, mat_roof=1, n=8):
    CYL(bm, cx, cy, z0, r, h, n=n, mat=mat_wall)
    CONE(bm, cx, cy, z0 + h, r * 1.15, roof_h, n=n, mat=mat_roof)


# ------------------------------------------------------------------ builders (all return object centred at origin, ground at z=0)

def wood_bridge(p):
    bm = _new_bm(); L = p.get("length", 100)
    B(bm, 0, 0, 3.0, 6, L, 1.0, mat=0)
    for i in range(int(L // 12)):
        y = -L / 2 + 6 + i * 12
        B(bm, -2, y, 0, 1.2, 1.2, 3.2, mat=0); B(bm, 2, y, 0, 1.2, 1.2, 3.2, mat=0)
    return _finish(bm, "lm_wood_bridge", [_mat("wood", WOOD)])


def roman_forum(p):
    bm = _new_bm(); w, d = p["w"], p["d"]
    B(bm, 0, 0, 0, w, d, 2.0, mat=0)                           # platform
    for sx in (-1, 1):                                          # porticoes
        B(bm, sx * (w / 2 - 6), 0, 2, 8, d - 10, 6, mat=0)
        GABLE(bm, sx * (w / 2 - 6), 0, 8, 8, d - 10, 2.5, along_x=False, mat=1)
    B(bm, 0, d / 2 - 20, 2, 26, 30, 4, mat=0)                   # temple podium
    B(bm, 0, d / 2 - 20, 6, 20, 26, 10, mat=0)
    GABLE(bm, 0, d / 2 - 20, 16, 20, 26, 4, along_x=False, mat=1)
    B(bm, 0, -d / 2 + 22, 2, 34, 26, 12, mat=0)                 # basilica
    GABLE(bm, 0, -d / 2 + 22, 14, 34, 26, 5, mat=1)
    return _finish(bm, "lm_forum", [_mat("stone", STONE), _mat("tile", ROOF_TILE)])


def roman_theatre(p):
    bm = _new_bm(); r = p["r"]
    n = 14
    for i in range(3):
        rr = r * (1 - i * 0.28); h = 4 + i * 3.5
        pts_o = [(rr * math.cos(math.pi * k / n), rr * math.sin(math.pi * k / n)) for k in range(n + 1)]
        pts_i = [(rr * 0.72 * math.cos(math.pi * k / n), rr * 0.72 * math.sin(math.pi * k / n)) for k in range(n + 1)]
        lo = [bm.verts.new((x, y, 0)) for x, y in pts_o + pts_i[::-1]]
        hi = [bm.verts.new((x, y, h)) for x, y in pts_o + pts_i[::-1]]
        m = len(lo)
        for k in range(m):
            f = bm.faces.new([lo[k], lo[(k + 1) % m], hi[(k + 1) % m], hi[k]]); f.material_index = 0
        f = bm.faces.new(hi); f.material_index = 0
    B(bm, 0, -6, 0, r * 1.6, 12, 10, mat=0)   # stage building
    GABLE(bm, 0, -6, 10, r * 1.6, 12, 3, mat=1)
    return _finish(bm, "lm_theatre", [_mat("stone", STONE), _mat("tile", ROOF_TILE)])


def roman_amphitheatre(p):
    bm = _new_bm(); a, b = p["a"], p["b"]
    n = 24
    for i in range(3):
        f_ = 1 - i * 0.22; h = 5 + i * 4
        outer = [(a * f_ * math.cos(2 * math.pi * k / n), b * f_ * math.sin(2 * math.pi * k / n)) for k in range(n)]
        inner = [(a * 0.55 * math.cos(2 * math.pi * k / n), b * 0.5 * math.sin(2 * math.pi * k / n)) for k in range(n)]
        lo_o = [bm.verts.new((x, y, 0)) for x, y in outer]; hi_o = [bm.verts.new((x, y, h)) for x, y in outer]
        lo_i = [bm.verts.new((x, y, 0)) for x, y in inner]; hi_i = [bm.verts.new((x, y, h)) for x, y in inner]
        for k in range(n):
            k2 = (k + 1) % n
            f = bm.faces.new([lo_o[k], lo_o[k2], hi_o[k2], hi_o[k]]); f.material_index = 0
            f = bm.faces.new([hi_i[k], hi_i[k2], lo_i[k2], lo_i[k]]); f.material_index = 0
            f = bm.faces.new([hi_o[k], hi_o[k2], hi_i[k2], hi_i[k]]); f.material_index = 0
    return _finish(bm, "lm_amphi", [_mat("stone", STONE)])


def roman_baths(p):
    bm = _new_bm(); w, d = p["w"], p["d"]
    B(bm, 0, 0, 0, w, d, 12, mat=0)
    B(bm, 0, 0, 12, w * 0.5, d * 0.5, 5, mat=0)
    _dome(bm, 0, 0, 17, min(w, d) * 0.22, 7, mat=1)
    GABLE(bm, -w * 0.3, 0, 12, w * 0.35, d, 4, along_x=False, mat=1)
    return _finish(bm, "lm_baths", [_mat("stone", STONE), _mat("tile", ROOF_TILE)])


def roman_temple(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p.get("h", 16)
    B(bm, 0, 0, 0, w + 6, d + 6, 3, mat=0)
    B(bm, 0, 0, 3, w * 0.8, d * 0.85, h - 6, mat=0)
    for i in range(int(w // 5)):
        for sy in (-1, 1):
            CYL(bm, -w / 2 + 2.5 + i * 5, sy * (d / 2 - 2), 3, 1.1, h - 6, n=6, mat=0)
    GABLE(bm, 0, 0, h - 3, w, d, 4, along_x=False, mat=1)
    return _finish(bm, "lm_temple", [_mat("stone", STONE), _mat("tile", ROOF_TILE)])


def basilica(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w, d, h * 0.7, mat=0)
    GABLE(bm, 0, 0, h * 0.7, w, d, h * 0.35, along_x=False, mat=1)
    B(bm, 0, d / 2 - 4, 0, w * 0.3, 8, h * 1.3, mat=0)
    CONE(bm, 0, d / 2 - 4, h * 1.3, w * 0.2, h * 0.5, n=4, mat=1)
    return _finish(bm, "lm_basilica", [_mat("stone", STONE), _mat("slate", ROOF_SLATE)])


def abbey(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w * 0.4, d, h, mat=0)
    GABLE(bm, 0, 0, h, w * 0.4, d, h * 0.45, along_x=False, mat=1)
    B(bm, 0, -d / 2 + 6, h, w * 0.25, 12, h * 0.6, mat=0)
    CONE(bm, 0, -d / 2 + 6, h * 1.6, w * 0.16, h * 0.6, n=4, mat=1)
    # cloister
    B(bm, w * 0.35, 0, 0, w * 0.3, d * 0.6, h * 0.5, mat=0)
    GABLE(bm, w * 0.35, 0, h * 0.5, w * 0.3, d * 0.6, h * 0.2, mat=1)
    return _finish(bm, "lm_abbey", [_mat("stone", STONE), _mat("slate", ROOF_SLATE)])


def cathedral(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w * 0.55, d, h, mat=0)
    GABLE(bm, 0, 0, h, w * 0.55, d, h * 0.4, along_x=False, mat=1)
    B(bm, 0, 0, 0, w, d * 0.35, h * 0.85, mat=0)      # transept
    GABLE(bm, 0, 0, h * 0.85, w, d * 0.35, h * 0.35, mat=1)
    for i in range(p.get("towers", 2)):
        x = (-1 if i == 0 else 1) * w * 0.18 if p.get("towers", 2) == 2 else 0
        B(bm, x, -d / 2 + w * 0.15, 0, w * 0.28, w * 0.28, h * 1.7, mat=0)
        if p.get("towers", 2) == 1:
            CONE(bm, x, -d / 2 + w * 0.15, h * 1.7, w * 0.18, h * 0.8, n=4, mat=1)
    CONE(bm, 0, 0, h * 1.2, 4, h * 0.9, n=4, mat=1)   # fleche
    return _finish(bm, "lm_cathedral", [_mat("stone", STONE), _mat("slate", ROOF_SLATE)])


def palace_block(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w, d, h, mat=0)
    kits._mansard(bm, 0, 0, h, w, d, h * 0.3, h * 0.12, min(w, d) * 0.12, mat=1)
    if w > 100 and d > 60:   # courtyard
        pass
    for sx in (-1, 1):
        B(bm, sx * (w / 2 - min(d, w) * 0.15), 0, 0, min(d, w) * 0.3, d, h * 1.25, mat=0)
        kits._mansard(bm, sx * (w / 2 - min(d, w) * 0.15), 0, h * 1.25, min(d, w) * 0.3, d, h * 0.3, h * 0.12, 3, mat=1)
    return _finish(bm, "lm_palace", [_mat("stone", STONE), _mat("slate", ROOF_SLATE)])


def square_ring(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    t = 18
    for cx, cy, ww, dd in ((0, -d / 2 + t / 2, w, t), (0, d / 2 - t / 2, w, t), (-w / 2 + t / 2, 0, t, d - 2 * t), (w / 2 - t / 2, 0, t, d - 2 * t)):
        B(bm, cx, cy, 0, ww, dd, h, mat=0)
        kits._mansard(bm, cx, cy, h, ww, dd, h * 0.35, h * 0.1, 3, mat=1)
    B(bm, 0, 0, 0, w - 2 * t - 6, d - 2 * t - 6, 0.4, mat=2)
    return _finish(bm, "lm_square", [_mat("brick", (0.70, 0.40, 0.30)), _mat("slate", ROOF_SLATE), _mat("grass", GRASS)])


def castle(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    keep = p.get("keep", 20)
    t = 5
    for cx, cy, ww, dd in ((0, -d / 2, w, t), (0, d / 2, w, t), (-w / 2, 0, t, d), (w / 2, 0, t, d)):
        B(bm, cx, cy, 0, ww, dd, h, mat=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _tower(bm, sx * w / 2, sy * d / 2, 0, 6, h * 1.4, 7, n=8)
    if w > 50:
        for sx in (-1, 1):
            _tower(bm, sx * w / 4, -d / 2, 0, 5, h * 1.3, 6, n=8)
            _tower(bm, sx * w / 4, d / 2, 0, 5, h * 1.3, 6, n=8)
    _tower(bm, 0, 0, 0, keep * 0.32, keep, keep * 0.35, n=10)
    return _finish(bm, "lm_castle", [_mat("stone_d", STONE_DARK), _mat("slate", ROOF_SLATE)])


def invalides(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    t = 26
    for cx, cy, ww, dd in ((0, d / 2 - t / 2, w, t), (-w / 2 + t / 2, 0, t, d), (w / 2 - t / 2, 0, t, d), (0, 0, w, t)):
        B(bm, cx, cy, 0, ww, dd, h, mat=0)
        kits._mansard(bm, cx, cy, h, ww, dd, 6, 2, 3, mat=1)
    dome = p.get("dome", 100)
    B(bm, 0, -d / 2 + 30, 0, 60, 60, 28, mat=0)
    CYL(bm, 0, -d / 2 + 30, 28, 22, 22, n=16, mat=0)
    _dome(bm, 0, -d / 2 + 30, 50, 21, 26, mat=2, seg=16)
    CYL(bm, 0, -d / 2 + 30, 74, 4, 12, n=8, mat=2)
    CONE(bm, 0, -d / 2 + 30, 86, 5, 14, n=8, mat=2)
    return _finish(bm, "lm_invalides", [_mat("stone", STONE), _mat("slate", ROOF_SLATE), _mat("gold", GOLD)])


def domed_church(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w * 0.6, d, h, mat=0)
    GABLE(bm, 0, 0, h, w * 0.6, d, h * 0.25, along_x=False, mat=1)
    B(bm, 0, 0, 0, w, d * 0.4, h, mat=0)
    GABLE(bm, 0, 0, h, w, d * 0.4, h * 0.25, mat=1)
    dome = p.get("dome", 50)
    CYL(bm, 0, 0, h, w * 0.25, dome * 0.35, n=16, mat=0)
    _dome(bm, 0, 0, h + dome * 0.35, w * 0.24, dome * 0.32, mat=1, seg=16)
    CONE(bm, 0, 0, h + dome * 0.67, 3, dome * 0.18, n=6, mat=1)
    return _finish(bm, "lm_domed", [_mat("stone", STONE), _mat("slate", ROOF_SLATE)])


def versailles(p):
    bm = _new_bm()
    # palace: central block + two long wings, facing +x (gardens to -x)
    B(bm, 0, 0, 0, 90, 150, 24, mat=0); kits._mansard(bm, 0, 0, 24, 90, 150, 6, 2, 4, mat=1)
    for sy in (-1, 1):
        B(bm, 20, sy * 190, 0, 70, 230, 20, mat=0); kits._mansard(bm, 20, sy * 190, 20, 70, 230, 5, 2, 4, mat=1)
        B(bm, 90, sy * 80, 0, 90, 30, 18, mat=0); kits._mansard(bm, 90, sy * 80, 18, 90, 30, 5, 2, 3, mat=1)
    # forecourt
    B(bm, 160, 0, 0, 160, 220, 0.3, mat=3)
    # gardens: parterres + grand canal
    B(bm, -170, 0, 0, 240, 360, 0.4, mat=2)
    for i in range(6):
        for j in range(4):
            B(bm, -80 - i * 40, -140 + j * 90, 0.4, 28, 60, 1.6, mat=4)
    B(bm, -420, 0, 0, 260, 700, 0.4, mat=2)
    B(bm, -900, 0, -0.2, 1500, 62, 0.3, mat=5)    # grand canal
    B(bm, -1100, 0, -0.2, 62, 1000, 0.3, mat=5)
    # tree rows (bosquets)
    for i in range(12):
        for sy in (-1, 1):
            B(bm, -330 - i * 40, sy * 200, 0, 30, 220, 9, mat=4)
    return _finish(bm, "lm_versailles", [_mat("stone", STONE), _mat("slate", ROOF_SLATE), _mat("grass", GRASS),
                                          _mat("gravel", GRAVEL), _mat("hedge", (0.16, 0.30, 0.12)), _mat("canal", (0.25, 0.45, 0.50))])


def station(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, d / 2 - 15, 0, w, 30, h, mat=0)
    kits._mansard(bm, 0, d / 2 - 15, h, w, 30, 6, 2, 3, mat=1)
    n = max(2, int(w // 45))
    for i in range(n):
        x = -w / 2 + (i + 0.5) * w / n
        B(bm, x, -15, 0, w / n - 2, d - 30, h * 0.5, mat=0)
        GABLE(bm, x, -15, h * 0.5, w / n - 2, d - 30, h * 0.45, along_x=False, mat=2)
    if p.get("tower"):
        B(bm, w / 2 - 12, d / 2 - 12, 0, 16, 16, p["tower"], mat=0)
        kits._mansard(bm, w / 2 - 12, d / 2 - 12, p["tower"], 16, 16, 5, 2, 3, mat=1)
    return _finish(bm, "lm_station", [_mat("stone", STONE), _mat("slate", ROOF_SLATE), _mat("glassroof", GLASS)])


def grand_palais(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w, d, h * 0.5, mat=0)
    GABLE(bm, 0, 0, h * 0.5, w * 0.9, d * 0.7, h * 0.35, mat=1)
    _dome(bm, 0, 0, h * 0.5, d * 0.32, h * 0.5, mat=1, seg=16)
    return _finish(bm, "lm_grandpalais", [_mat("stone", STONE), _mat("glassroof", GLASS)])


def sacre_coeur(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w, d, h * 0.4, mat=0)
    _dome(bm, 0, 0, h * 0.4, w * 0.26, h * 0.42, mat=0, seg=16)
    CONE(bm, 0, 0, h * 0.8, 4, h * 0.2, n=8, mat=0)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        CYL(bm, sx * w * 0.36, sy * d * 0.36, h * 0.4, w * 0.1, h * 0.15, n=10, mat=0)
        _dome(bm, sx * w * 0.36, sy * d * 0.36, h * 0.55, w * 0.1, h * 0.14, mat=0, seg=10)
    B(bm, 0, d / 2 + 6, 0, w * 0.3, 20, h * 1.0, mat=0)
    _dome(bm, 0, d / 2 + 6, h * 1.0, w * 0.12, h * 0.12, mat=0, seg=10)
    return _finish(bm, "lm_sacrecoeur", [_mat("white", WHITE)])


def stadium(p):
    bm = _new_bm(); a, b, h = p["a"], p["b"], p["h"]
    n = 24
    outer = [(a * math.cos(2 * math.pi * k / n), b * math.sin(2 * math.pi * k / n)) for k in range(n)]
    inner = [(a * 0.62 * math.cos(2 * math.pi * k / n), b * 0.55 * math.sin(2 * math.pi * k / n)) for k in range(n)]
    lo_o = [bm.verts.new((x, y, 0)) for x, y in outer]; hi_o = [bm.verts.new((x, y, h)) for x, y in outer]
    lo_i = [bm.verts.new((x, y, 0)) for x, y in inner]; hi_i = [bm.verts.new((x, y, h * 0.4)) for x, y in inner]
    for k in range(n):
        k2 = (k + 1) % n
        f = bm.faces.new([lo_o[k], lo_o[k2], hi_o[k2], hi_o[k]]); f.material_index = 0
        f = bm.faces.new([hi_i[k], hi_i[k2], lo_i[k2], lo_i[k]]); f.material_index = 0
        f = bm.faces.new([hi_o[k], hi_o[k2], hi_i[k2], hi_i[k]]); f.material_index = 1
    f = bm.faces.new(lo_i); f.material_index = 2
    return _finish(bm, "lm_stadium", [_mat("concrete", CONCRETE), _mat("roofgrey", (0.6, 0.6, 0.62)), _mat("pitch", GRASS)])


def tower(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w, d, h, mat=0)
    B(bm, 0, 0, h, w * 0.98, d * 0.98, 2, mat=1)
    return _finish(bm, "lm_tower", [_mat("glass_dark", (0.20, 0.22, 0.26)), _mat("roofgrey", (0.5, 0.5, 0.5))])


def arch_cube(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    t = 18
    B(bm, -w / 2 + t / 2, 0, 0, t, d, h, mat=0)
    B(bm, w / 2 - t / 2, 0, 0, t, d, h, mat=0)
    B(bm, 0, 0, h - t, w, d, t, mat=0)
    return _finish(bm, "lm_arche", [_mat("white", WHITE)])


def box(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w, d, h, mat=0)
    B(bm, 0, 0, h, w * 0.98, d * 0.98, 1.0, mat=1)
    return _finish(bm, "lm_box", [_mat("concrete", CONCRETE), _mat("roofgrey", (0.55, 0.55, 0.56))])


def bnf(p):
    bm = _new_bm(); w, d, h = p["w"], p["d"], p["h"]
    B(bm, 0, 0, 0, w, d, 3, mat=0)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        B(bm, sx * (w / 2 - 20), sy * (d / 2 - 20), 3, 40, 40, h, mat=1)
    B(bm, 0, 0, 3, w - 100, d - 100, 0.5, mat=2)
    return _finish(bm, "lm_bnf", [_mat("concrete", CONCRETE), _mat("glass_dark", (0.20, 0.22, 0.26)), _mat("grass", GRASS)])


def airport(p):
    bm = _new_bm()
    for L, off, ang in p["runways"]:
        a = math.radians(ang)
        # rotated slab: build along x then rotate verts
        verts = []
        for dx, dy in ((-L / 2, -25), (L / 2, -25), (L / 2, 25), (-L / 2, 25)):
            x = dx * math.cos(a) - dy * math.sin(a); y = dx * math.sin(a) + dy * math.cos(a) + off
            verts.append(bm.verts.new((x, y, 0.5)))
        f = bm.faces.new(verts); f.material_index = 0
    B(bm, 0, -300, 0, 500, 120, 14, mat=1)
    return _finish(bm, "lm_airport", [_mat("asphalt", (0.35, 0.35, 0.36)), _mat("concrete", CONCRETE)])


BUILDERS = {
    "wood_bridge": wood_bridge, "roman_forum": roman_forum, "roman_theatre": roman_theatre,
    "roman_amphitheatre": roman_amphitheatre, "roman_baths": roman_baths, "roman_temple": roman_temple,
    "basilica": basilica, "abbey": abbey, "cathedral": cathedral, "palace_block": palace_block,
    "square_ring": square_ring, "castle": castle, "invalides": invalides, "domed_church": domed_church,
    "versailles": versailles, "station": station, "grand_palais": grand_palais, "sacre_coeur": sacre_coeur,
    "stadium": stadium, "tower": tower, "arch_cube": arch_cube, "box": box, "bnf": bnf, "airport": airport,
}

GLB_COLORS = {
    "eiffel": (0.30, 0.22, 0.16),
    "notre_dame": (0.70, 0.66, 0.56),
    "louvre": (0.70, 0.66, 0.55),
    "arc_de_triomphe": (0.72, 0.69, 0.60),
    "gare_du_nord": (0.66, 0.62, 0.54),
    "palais_garnier": (0.68, 0.64, 0.54),
    "sainte_chapelle": (0.70, 0.67, 0.58),
    "saint_germain_des_pres": (0.68, 0.64, 0.56),
    "tour_du_temple": (0.64, 0.60, 0.53),
    "petit_pont_petit_chatelet": (0.64, 0.60, 0.53),
}

_glb_cache = {}


def load_glb(key, p):
    """Import GLB (cached mesh), flat material, scaled so that its longest horizontal extent = p['w'] and height ~ p['h']."""
    if key not in _glb_cache:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(GLB_DIR, GLB_FILES[key]))
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == 'MESH']
        # join into one mesh via bmesh
        bm = bmesh.new()
        for o in meshes:
            tmp = o.to_mesh() if False else o.data
            m = bmesh.new(); m.from_mesh(o.data); m.transform(o.matrix_world); bmesh.ops.remove_doubles(m, verts=m.verts, dist=1e-5)
            tm = bpy.data.meshes.new("tmp"); m.to_mesh(tm); m.free()
            bm.from_mesh(tm); bpy.data.meshes.remove(tm)
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
        me = bpy.data.meshes.new("glb_" + key)
        bm.to_mesh(me); bm.free()
        me.materials.clear()
        me.materials.append(_mat("glb_" + key, GLB_COLORS.get(key, STONE)))
        for pg in me.polygons:
            pg.material_index = 0
            pg.use_smooth = False
        _glb_cache[key] = me
    me = _glb_cache[key]
    ob = bpy.data.objects.new("lm_" + key, me)
    # normalise: compute bbox
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    dx, dy, dz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
    cx, cy, z0 = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)
    long_h = max(dx, dy)
    if key == "eiffel":
        s = p["h"] / dz
    else:
        s = p["w"] / long_h
    yaw = math.radians(GLB_YAW.get(key, 0) + (90 if dy > dx else 0))
    ob.matrix_world = Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Scale(s, 4) @ Matrix.Translation((-cx, -cy, -z0))
    return ob, s * dz


def build_landmark(entry, collection):
    name, x, y, rot, birth, death, builder, prm = entry
    if builder.startswith("glb:"):
        ob, h = load_glb(builder[4:], prm)
        base = ob.matrix_world.copy()
    else:
        ob = BUILDERS[builder](prm)
        base = Matrix.Identity(4)
    ob.name = "LM_" + name
    collection.objects.link(ob)
    return ob, base
