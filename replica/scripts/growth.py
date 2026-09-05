"""City growth engine.

Reads  : data/geo.json, data/kit_footprints.json, history.py, terrain.py, timeline.py
Writes : cache/scene_data.npz  (+ cache/scene_meta.json)

Everything is computed on a 10 m raster covering 36 x 28 km around Notre-Dame.
Buildings are placed along streets (both sides) with an era-dependent spacing,
carry birth / death years, a kit id and a replacement chain so the city
recolours itself over time exactly like the reference film.
"""
import json, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timeline, terrain, history

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(HERE, "..", "cache")
os.makedirs(CACHE, exist_ok=True)

X0, X1, Y0, Y1 = -18000, 18000, -14000, 14000
CELL = 10
NX, NY = (X1 - X0) // CELL, (Y1 - Y0) // CELL
RNG = np.random.default_rng(7)
T0 = time.time()

ERA_ID = {n: i for i, n in enumerate(["celtic", "roman", "medieval", "classical", "haussmann", "modern", "suburb", "slab"])}
# the reference film exaggerates building size ~2x relative to the map; we do the same
BUILD_SCALE = 2.0
SPACING = {k: v * BUILD_SCALE * 0.85 for k, v in {"celtic": 11.0, "roman": 12.5, "medieval": 7.5, "classical": 15.0, "haussmann": 24.0,
           "modern": 21.0, "suburb": 16.0, "slab": 60.0}.items()}
HALF_WIDTH = {"motorway": 20, "trunk": 14, "primary": 11, "secondary": 8.5, "tertiary": 6.5, "residential": 5.0,
              "unclassified": 5.0, "living_street": 4.0, "pedestrian": 3.5, "roman": 5.0, "path": 2.5, "route": 6.5}
ROAD_WIDTH = {"motorway": 26, "trunk": 20, "primary": 15, "secondary": 11, "tertiary": 8.5, "residential": 6.5,
              "unclassified": 6.0, "living_street": 5.5, "pedestrian": 5.0, "roman": 7.0, "path": 4.0, "route": 9.0}
CLASS_RANK = {"motorway": 0, "route": 1, "trunk": 1, "primary": 2, "secondary": 3, "tertiary": 4, "roman": 4, "residential": 5,
              "unclassified": 5, "living_street": 6, "pedestrian": 6, "path": 7}


def log(*a):
    print(f"[{time.time()-T0:6.1f}s]", *a, flush=True)


# ------------------------------------------------------------------ raster helpers
def to_px(x, y):
    return ((x - X0) / CELL, (Y1 - y) / CELL)


def cell(x, y):
    """(row, col) clipped."""
    c = int((x - X0) / CELL); r = int((Y1 - y) / CELL)
    return (min(max(r, 0), NY - 1), min(max(c, 0), NX - 1))


def cells(xs, ys):
    c = np.clip(((xs - X0) / CELL).astype(np.int64), 0, NX - 1)
    r = np.clip(((Y1 - ys) / CELL).astype(np.int64), 0, NY - 1)
    return r, c


def draw_polys(polys, value=1, mode="L", base=None):
    im = base if base is not None else Image.new(mode, (NX, NY), 0)
    d = ImageDraw.Draw(im)
    for p in polys:
        if isinstance(p, MultiPolygon):
            geoms = list(p.geoms)
        else:
            geoms = [p]
        for g in geoms:
            if g.is_empty:
                continue
            d.polygon([to_px(x, y) for x, y in g.exterior.coords], fill=value)
            for h in g.interiors:
                d.polygon([to_px(x, y) for x, y in h.coords], fill=0)
    return im


def smooth_noise(sigma_cells, seed):
    r = np.random.default_rng(seed).standard_normal((NY // 8 + 1, NX // 8 + 1)).astype(np.float32)
    r = ndimage.gaussian_filter(r, sigma_cells / 8.0)
    r = ndimage.zoom(r, 8, order=1)[:NY, :NX]
    r /= (r.std() + 1e-6)
    return r


# ------------------------------------------------------------------ load
geo = json.load(open(os.path.join(DATA, "geo.json"), encoding="utf-8"))
FOOT = json.load(open(os.path.join(DATA, "kit_footprints.json")))
log("geo loaded")


def jpoly(j):
    try:
        p = Polygon(j["outer"], j.get("holes", []))
        if not p.is_valid:
            p = p.buffer(0)
        return p
    except Exception:
        return None


water_polys = [p for p in (jpoly(w) for w in geo["water"]) if p is not None and not p.is_empty]
river = [p for w, p in zip(geo["water"], water_polys) if w["kind"] == "river"]
seine = max(river, key=lambda p: p.area)
canal_lines = [LineString(c["pts"]).buffer(c["width"] / 2) for c in geo["canals"] if len(c["pts"]) >= 2]
water_union_polys = water_polys + canal_lines
water_img = draw_polys(water_union_polys)
water = np.array(water_img, dtype=bool)
log("water mask", water.sum())

# islands as polygons from the river holes
holes = [Polygon(h) for h in seine.interiors]
def hole_containing(x, y):
    pt = Point(x, y)
    for h in holes:
        if h.contains(pt):
            return h
    return None
cite = hole_containing(-200, 190)
st_louis = hole_containing(495, -138)
assert cite is not None, "Ile de la Cite not found among river holes"
log("cite area", round(cite.area), "st louis", round(st_louis.area) if st_louis else None)

green = []
for g in geo["green"]:
    p = jpoly(g)
    if p is None or p.is_empty:
        continue
    kind = g["kind"]
    if kind == "park" and p.area > 3e6:
        kind = "forest"
    green.append((p, kind, g.get("name", "")))
forest_polys = [p for p, k, n in green if k == "forest"]
park_polys = [p for p, k, n in green if k != "forest"]
forest = np.array(draw_polys(forest_polys), dtype=bool)
park = np.array(draw_polys(park_polys), dtype=bool)
log("green masks", forest.sum(), park.sum())

paris_full = jpoly(geo["paris"])
bois = [p for p, k, n in green if ("Boulogne" in n or "Vincennes" in n) and p.area > 3e6]
paris = paris_full.difference(unary_union(bois).buffer(150)) if bois else paris_full
if isinstance(paris, MultiPolygon):
    paris = max(paris.geoms, key=lambda p: p.area)
paris = paris.simplify(30)
log("paris (minus bois) area km2", round(paris.area / 1e6, 1))

# landmark footprints -> blocked
blocked_polys = []
for name, x, y, rot, b, d, builder, prm in history.LANDMARKS:
    if builder == "versailles":
        w, dd = 1400, 3000
    elif builder == "airport":
        w, dd = 4200, 1400
    else:
        w, dd = prm.get("w", 60) * 1.15 + 12, prm.get("d", 60) * 1.15 + 12
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for dx, dy in ((-w / 2, -dd / 2), (w / 2, -dd / 2), (w / 2, dd / 2), (-w / 2, dd / 2)):
        pts.append((x + dx * ca - dy * sa, y + dx * sa + dy * ca))
    blocked_polys.append(Polygon(pts))
blocked = np.array(draw_polys(blocked_polys), dtype=bool)
log("blocked", blocked.sum())

# distance to water (cells) and terrain
d_water = ndimage.distance_transform_edt(~water).astype(np.float32)
log("water edt")

# ------------------------------------------------------------------ growth field
birth = np.full((NY, NX), 9999.0, dtype=np.float32)
zone_kit = np.full((NY, NX), -1, dtype=np.int8)
noise = smooth_noise(20, 1)
prev = np.zeros((NY, NX), dtype=bool)
ZONE_KIT_ID = {"celtic": 0, "roman": 1, "medieval": 2, "classical": 3, "haussmann": 4, "modern": 5, "suburb": 6}
zone_index = {}
for zi, (name, poly, ys, ye, kit) in enumerate(history.ZONES):
    if poly is None:
        P = cite
    elif poly == "PARIS":
        P = paris
    elif isinstance(poly, tuple):
        P = paris.buffer(poly[1])
    else:
        P = Polygon(poly)
    mask = np.array(draw_polys([P]), dtype=bool) & ~water
    zone_index[name] = zi
    if not prev.any():
        seed = np.zeros_like(prev)
        r, c = cell(P.centroid.x, P.centroid.y)
        seed[r, c] = True
        d = ndimage.distance_transform_edt(~seed)
    else:
        d = ndimage.distance_transform_edt(~prev)
    dm = d[mask]
    if dm.size == 0:
        log("empty zone", name); continue
    norm = max(np.percentile(dm, 92), 1.0)
    g = np.clip(d / norm, 0, 1) ** 0.9
    span = ye - ys
    y = ys + span * g + noise * span * 0.10
    sel = mask & (y < birth)
    birth[sel] = y[sel]
    zone_kit[sel] = ZONE_KIT_ID[kit]
    prev |= mask
    log("zone", name, "cells", int(mask.sum()), "years", ys, ye)

# villages
yy, xx = np.mgrid[0:NY, 0:NX]
XX = X0 + (xx + 0.5) * CELL
YY = Y1 - (yy + 0.5) * CELL
for name, vx, vy, vr, ys, ye in history.VILLAGES:
    r0, c0 = cell(vx, vy)
    R = int(vr / CELL) + 2
    rs, re = max(r0 - R, 0), min(r0 + R, NY)
    cs, ce = max(c0 - R, 0), min(c0 + R, NX)
    dx = XX[rs:re, cs:ce] - vx; dy = YY[rs:re, cs:ce] - vy
    dd = np.sqrt(dx * dx + dy * dy) / vr
    y = ys + (ye - ys) * np.clip(dd, 0, 1) ** 1.3 + noise[rs:re, cs:ce] * (ye - ys) * 0.08
    sub = birth[rs:re, cs:ce]
    sel = (dd <= 1.0) & (y < sub) & ~water[rs:re, cs:ce]
    sub[sel] = y[sel]
    zone_kit[rs:re, cs:ce][sel] = ZONE_KIT_ID["medieval"] if ye <= 1600 else ZONE_KIT_ID["suburb"]
log("villages applied")

# density (probability that a candidate building is kept)
paris_mask = np.array(draw_polys([paris]), dtype=bool)
d_paris = ndimage.distance_transform_edt(~paris_mask).astype(np.float32) * CELL
density = np.where(d_paris <= 0, 1.0, np.clip(1.1 - (d_paris - 3000) / 14000, 0.35, 1.0)).astype(np.float32)
density *= (0.85 + 0.15 * np.clip(smooth_noise(30, 2), -1, 1))
# village cores are dense
for name, vx, vy, vr, ys, ye in history.VILLAGES:
    r0, c0 = cell(vx, vy); R = int(vr * 1.6 / CELL)
    rs, re = max(r0 - R, 0), min(r0 + R, NY); cs, ce = max(c0 - R, 0), min(c0 + R, NX)
    density[rs:re, cs:ce] = np.maximum(density[rs:re, cs:ce], 0.9)
log("density")

# ------------------------------------------------------------------ roads
CENTER = np.array([-300.0, 300.0])


def road_year_at(x, y, cls, radial, name, is_bridge, is_periph, field):
    d = math.hypot(x - CENTER[0], y - CENTER[1])
    if is_periph:
        ang = math.atan2(x - CENTER[0], y - CENTER[1])  # from north, clockwise
        return 1960 + 13 * ((ang + math.pi) / (2 * math.pi))
    if is_bridge:
        for k, v in history.BRIDGE_YEARS.items():
            if k.lower() in name.lower():
                return v
        if cls == "motorway":
            return 1962 + d / 1000 * 1.6
        return max(field, history.BRIDGE_DEFAULT_YEAR) if field < 1880 else field
    if cls == "motorway":
        return 1962 + d / 1000 * 1.6
    if cls in ("trunk", "primary"):
        cand = 1150 + d * 0.05
    elif cls == "secondary":
        cand = 1350 + d * 0.06
    elif cls == "tertiary":
        cand = 1550 + d * 0.07
    else:
        cand = 9999
    return min(field, cand)


# hand-defined long-distance routes (bearing deg clockwise from north, first year)
ROUTES = [
    (5, -20), (195, -25), (150, 40), (70, 90), (325, 130), (245, 170), (110, 220), (350, 300),
    (30, 880), (90, 900), (170, 950), (215, 980), (280, 1000), (130, 1050), (265, 1100), (20, 1150),
    (50, 1250), (160, 1300), (230, 1350), (300, 1380), (335, 1400), (100, 1450), (180, 1500), (205, 1520),
    (60, 1560), (120, 1600), (255, 1620), (310, 1650), (40, 1680), (140, 1700), (225, 1720), (290, 1740),
]


def make_route(bearing, seed):
    rs = np.random.default_rng(seed)
    th = math.radians(bearing)
    dx, dy = math.sin(th), math.cos(th)
    px, py = -dy, dx
    amp = rs.uniform(250, 700); f1 = rs.uniform(0.6, 1.4); ph = rs.uniform(0, 6.28); amp2 = rs.uniform(80, 200)
    pts = []
    for s in np.arange(0, 23000, 60):
        lat = amp * math.sin(s / 23000 * math.pi * f1 + ph) * (s / 23000) ** 0.7 + amp2 * math.sin(s / 1900 + ph * 2)
        pts.append((-200 + dx * s + px * lat, 200 + dy * s + py * lat))
    return LineString(pts)


# Roman grid inside roman_left
ROMAN_POLY = Polygon(history.ZONES[1][1]).difference(unary_union(water_polys[:0] + [seine]))
CARDO = math.radians(97.5)
ux, uy = math.cos(CARDO), math.sin(CARDO)          # north-ish
vx_, vy_ = math.cos(CARDO - math.pi / 2), math.sin(CARDO - math.pi / 2)   # east-ish
roman_roads = []
origin = np.array([-330.0, -300.0])
for k in range(-12, 13):
    for axis in (0, 1):
        if axis == 0:   # lines along u (cardines), offset along v
            p0 = origin + k * 135 * np.array([vx_, vy_]) - 2000 * np.array([ux, uy])
            p1 = origin + k * 135 * np.array([vx_, vy_]) + 2000 * np.array([ux, uy])
        else:
            p0 = origin + k * 135 * np.array([ux, uy]) - 2000 * np.array([vx_, vy_])
            p1 = origin + k * 135 * np.array([ux, uy]) + 2000 * np.array([vx_, vy_])
        ln = LineString([tuple(p0), tuple(p1)]).intersection(ROMAN_POLY)
        geoms = list(ln.geoms) if hasattr(ln, "geoms") else [ln]
        for g in geoms:
            if isinstance(g, LineString) and g.length > 60:
                roman_roads.append(g)
log("roman grid roads", len(roman_roads))

roads = []   # dicts: line, cls, name, bridge, tunnel, periph, death
for r in geo["roads"]:
    if r.get("tunnel"):
        continue
    if len(r["pts"]) < 2:
        continue
    ln = LineString(r["pts"])
    if ln.length < 8:
        continue
    roads.append({"line": ln, "cls": r["cls"], "name": r["name"], "bridge": r["bridge"],
                  "periph": "riph" in r["name"], "death": 9999.0, "synthetic": False})
for g in roman_roads:
    roads.append({"line": g, "cls": "roman", "name": "", "bridge": False, "periph": False, "death": 520.0, "synthetic": True})
for i, (bearing, yr) in enumerate(ROUTES):
    roads.append({"line": make_route(bearing, 100 + i), "cls": "route", "name": "", "bridge": False, "periph": False,
                  "death": 9999.0, "synthetic": False, "route_year": yr})
roads.sort(key=lambda r: (CLASS_RANK.get(r["cls"], 9), -r["line"].length))
log("roads", len(roads))

roman_mask = np.array(draw_polys([ROMAN_POLY]), dtype=bool)

# per-road base attributes and per-piece years
PIECE = 40.0
road_pieces = []   # x0,y0,x1,y1,width,birth,death,bridge,cls_rank
for rd in roads:
    ln = rd["line"]
    coords = np.array(ln.coords)
    # radial test: direction of the whole way vs direction to centre
    v = coords[-1] - coords[0]
    mid = coords.mean(axis=0)
    to_c = CENTER - mid
    nv, nc = np.linalg.norm(v), np.linalg.norm(to_c)
    radial = False
    if nv > 1 and nc > 1:
        cosang = abs(np.dot(v, to_c) / (nv * nc))
        radial = cosang > math.cos(math.radians(32))
    # roman zone: irregular OSM streets get pushed to medieval unless grid-aligned
    r0, c0 = cell(mid[0], mid[1])
    in_roman = roman_mask[r0, c0] and not rd["synthetic"]
    grid_aligned = False
    if in_roman and nv > 1:
        ang = math.atan2(v[1], v[0])
        rel = (ang - CARDO) % (math.pi / 2)
        grid_aligned = min(rel, math.pi / 2 - rel) < math.radians(10)
    n = max(1, int(math.ceil(ln.length / PIECE)))
    pts = [ln.interpolate(i / n, normalized=True) for i in range(n + 1)]
    rd["pieces"] = []
    rd["birth_min"] = 9999.0
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        mx, my = (a.x + b.x) / 2, (a.y + b.y) / 2
        r, c = cell(mx, my)
        is_bridge = rd["bridge"]
        if water[r, c] and not is_bridge:
            if rd["cls"] == "route":
                is_bridge = True
            else:
                continue
        field = float(birth[r, c])
        if rd["cls"] == "route":
            y = rd["route_year"] + math.hypot(mx + 200, my - 200) / 1000 * 2.2
        else:
            y = road_year_at(mx, my, rd["cls"], radial, rd["name"], rd["bridge"], rd["periph"], field)
        if rd["synthetic"]:
            y = 55 + math.hypot(mx + 330, my + 300) / 5.0
        elif in_roman and not grid_aligned and y < 480 and CLASS_RANK[rd["cls"]] >= 3:
            y = max(y, 1000.0 + RNG.uniform(0, 120))
        if y >= 9000:
            continue
        y -= 12.0   # streets slightly precede their houses
        rd["pieces"].append((a.x, a.y, b.x, b.y, y))
        rd["birth_min"] = min(rd["birth_min"], y)
        road_pieces.append((a.x, a.y, b.x, b.y, ROAD_WIDTH.get(rd["cls"], 6), y, rd["death"],
                            1.0 if is_bridge else 0.0, CLASS_RANK.get(rd["cls"], 9)))
road_pieces = np.array(road_pieces, dtype=np.float32)
log("road pieces", len(road_pieces))

# road year raster (min) and road mask, for trees and fill placement
road_year_img = Image.new("F", (NX, NY), 9999.0)
dr = ImageDraw.Draw(road_year_img)
order = np.argsort(-road_pieces[:, 5])
for i in order:
    x0, y0, x1, y1, w, y, dth, br, rk = road_pieces[i]
    dr.line([to_px(x0, y0), to_px(x1, y1)], fill=float(y), width=max(1, int(w / CELL) + 1))
road_year = np.array(road_year_img, dtype=np.float32)
road_mask = road_year < 9000
d_road = ndimage.distance_transform_edt(~road_mask).astype(np.float32) * CELL
log("road rasters")

# ------------------------------------------------------------------ building placement
occ_death = np.full((NY, NX), -1e9, dtype=np.float32)   # cell free again after this year
paris_buf2500 = np.array(draw_polys([paris.buffer(2500)]), dtype=bool)
fermiers_mask = np.array(draw_polys([Polygon(history.ZONES[zone_index["fermiers"]][1])]), dtype=bool)
core_mask = np.zeros((NY, NX), dtype=bool)    # medieval core that gets rebuilt in stone 1500-1650
for zn in ("pa_right", "pa_left", "charles_v", "faubourg_med", "louis_xiii", "fbg_st_germain", "celtic_cite", "frank_cite", "frank_right", "frank_left"):
    zi = zone_index[zn]
    poly = history.ZONES[zi][1]
    P = cite if poly is None else Polygon(poly)
    core_mask |= np.array(draw_polys([P]), dtype=bool)
cite_mask = np.array(draw_polys([cite]), dtype=bool)
slab_mask = np.zeros((NY, NX), dtype=np.float32)
for sx_, sy_, sr, ys, ye in history.SLAB_ZONES:
    Image.Image  # noqa
    im = draw_polys([Point(sx_, sy_).buffer(sr)], mode="L")
    slab_mask = np.maximum(slab_mask, np.array(im, dtype=np.float32))

# sprout duration lookup
YEARS = np.arange(-400, 2100)
DUR = np.array([timeline.sprout_years(float(y)) for y in YEARS], dtype=np.float32)
def dur_of(y):
    return float(DUR[min(max(int(y + 400), 0), len(DUR) - 1)])

B = {k: [] for k in ("x", "y", "rot", "sx", "sy", "sz", "birth", "death", "era", "kit")}
rand = np.random.default_rng(11)


def kit_for(year, r, c):
    """era name for a building born in `year` at raster cell."""
    zk = int(zone_kit[r, c])
    if year < -52:
        return "celtic"
    if year < 480:
        return "roman"
    if year < 1500:
        return "medieval"
    if year < 1790:
        return "classical"
    if year < 1914:
        return "haussmann" if (fermiers_mask[r, c] or paris_mask[r, c] or zk in (4, 5)) else "suburb"
    if slab_mask[r, c] > 0 and 1955 <= year <= 1980 and rand.random() < 0.55:
        return "slab"
    if paris_buf2500[r, c] or zk == 5:
        return "modern"
    return "suburb"


def chain(era, year, r, c):
    """Return list of (era, birth, death) generations for a building first built in `year`."""
    gens = []
    y = year
    e = era
    for _ in range(6):
        d = 9999.0
        nxt = None
        u = rand.random()
        if e == "celtic":
            d = rand.uniform(-52, -25); nxt = "roman"
        elif e == "roman":
            if cite_mask[r, c]:
                d = rand.uniform(470, 720); nxt = "medieval"
            elif u < 0.85:
                d = float(np.clip(rand.normal(430, 40), 360, 520))
            else:
                d = rand.uniform(600, 1000)
        elif e == "medieval":
            if core_mask[r, c]:
                if u < 0.88:
                    d = rand.uniform(1500, 1650)
                else:
                    d = rand.uniform(1650, 1800)
                nxt = "classical"
            elif u < 0.6:
                d = rand.uniform(1840, 1960); nxt = "suburb" if not paris_mask[r, c] else "haussmann"
        elif e == "classical":
            if u < 0.62:
                d = rand.uniform(1840, 1905); nxt = "haussmann"
        elif e == "haussmann":
            if u < 0.30:
                d = rand.uniform(1950, 2005); nxt = "modern"
        elif e == "suburb":
            if paris_buf2500[r, c] and u < 0.5:
                d = rand.uniform(1930, 1990); nxt = "modern"
        gens.append((e, y, d))
        if nxt is None or d >= 9000:
            break
        e, y = nxt, d
    return gens


def place(x, y, rot, era, year, r, c, target_w):
    gens = chain(era, year, r, c)
    final_death = gens[-1][2]
    occ_death[r, c] = max(occ_death[r, c], final_death)
    for e, b, d in gens:
        k = int(rand.integers(0, 10))
        fw, fd, fh = FOOT[e][k]
        sx = float(np.clip(target_w / (fw * BUILD_SCALE), 0.7, 1.6)) * BUILD_SCALE if e not in ("slab", "celtic") else BUILD_SCALE
        sy = float(rand.uniform(0.9, 1.25)) * BUILD_SCALE
        sz = float(rand.uniform(0.9, 1.15)) * BUILD_SCALE
        B["x"].append(x); B["y"].append(y); B["rot"].append(rot)
        B["sx"].append(sx); B["sy"].append(sy); B["sz"].append(sz)
        B["birth"].append(b); B["death"].append(d); B["era"].append(ERA_ID[e]); B["kit"].append(k)


placed_by_class = {}
for rd in roads:
    if not rd.get("pieces"):
        continue
    cls = rd["cls"]
    hw = HALF_WIDTH.get(cls, 5.0)
    if cls == "motorway":
        continue   # nobody builds along motorways
    for (ax, ay, bx, by, ry) in rd["pieces"]:
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        if L < 4:
            continue
        tx, ty = dx / L, dy / L
        nx_, ny_ = -ty, tx
        ang = math.atan2(ty, tx)
        s = rand.uniform(2, 8)
        while s < L - 2:
            px, py = ax + tx * s, ay + ty * s
            r, c = cell(px, py)
            field = float(birth[r, c])
            year = max(field, ry + 2.0)
            if year >= 9000 or year >= rd["death"] - 30:
                s += 20; continue
            era = kit_for(year, r, c)
            sp = SPACING[era]
            keep = density[r, c]
            if cls in ("trunk", "primary", "secondary") and year < 1500 and not core_mask[r, c]:
                keep *= 0.35   # scattered roadside hamlets only
            for side in (-1, 1):
                if rand.random() > keep:
                    continue
                if rand.random() < 0.08:
                    continue
                fw, fd, fh = FOOT[era][0]
                depth = fd * 1.05 * BUILD_SCALE
                off = hw + depth / 2 + 1.5
                cx, cy = px + nx_ * off * side, py + ny_ * off * side
                r1, c1 = cell(cx, cy)
                r2, c2 = cell(cx + nx_ * depth / 2 * side, cy + ny_ * depth / 2 * side)
                if water[r1, c1] or water[r2, c2] or park[r1, c1] or forest[r1, c1] or blocked[r1, c1] or blocked[r2, c2]:
                    continue
                b_year = year + rand.uniform(-6, 22)
                if occ_death[r1, c1] > b_year or occ_death[r2, c2] > b_year:
                    continue
                if road_mask[r2, c2] and road_year[r2, c2] < b_year:
                    continue
                occ_death[r2, c2] = max(occ_death[r2, c2], 9999.0)
                rot = ang + (math.pi if side > 0 else 0.0)
                place(cx, cy, rot, era, b_year, r1, c1, sp * 0.92)
                placed_by_class[cls] = placed_by_class.get(cls, 0) + 1
            s += sp * rand.uniform(1.0, 1.18)
log("street buildings", len(B["x"]), placed_by_class)

# fill-mode: suburban interiors (no minor streets in OSM outside Paris), slabs, La Defense
major_segs = []
for rd in roads:
    if CLASS_RANK.get(rd["cls"], 9) <= 4 and rd.get("pieces"):
        for (ax, ay, bx, by, ry) in rd["pieces"]:
            major_segs.append(LineString([(ax, ay), (bx, by)]))
tree_idx = STRtree(major_segs)
log("major segs", len(major_segs))

fill_count = 0
step = 40
gx = np.arange(X0 + step / 2, X1, step)
gy = np.arange(Y0 + step / 2, Y1, step)
GX, GY = np.meshgrid(gx, gy)
GX = GX.ravel() + rand.uniform(-step * 0.35, step * 0.35, GX.size)
GY = GY.ravel() + rand.uniform(-step * 0.35, step * 0.35, GY.size)
rr, cc = cells(GX, GY)
ok = (~water[rr, cc]) & (~park[rr, cc]) & (~forest[rr, cc]) & (~blocked[rr, cc]) & (d_road[rr, cc] > 38) & (birth[rr, cc] >= 1840) & (birth[rr, cc] < 9000)
ok &= (~paris_mask[rr, cc]) | (birth[rr, cc] >= 1900)
ok &= rand.random(GX.size) < density[rr, cc] * 0.75
idx = np.nonzero(ok)[0]
log("fill candidates", len(idx))
near = tree_idx.nearest(list(Point(GX[i], GY[i]) for i in idx)) if len(idx) else []
for j, i in enumerate(idx):
    x, y = float(GX[i]), float(GY[i])
    r, c = rr[i], cc[i]
    year = float(birth[r, c]) + rand.uniform(0, 30)
    if occ_death[r, c] > year:
        continue
    seg = major_segs[int(near[j])]
    (ax, ay), (bx, by) = seg.coords[0], seg.coords[-1]
    ang = math.atan2(by - ay, bx - ax) + rand.uniform(-0.12, 0.12)
    era = kit_for(year, r, c)
    if era in ("haussmann", "classical", "medieval"):
        era = "suburb"
    place(x, y, ang, era, year, r, c, SPACING[era] * 0.9)
    fill_count += 1
log("fill buildings", fill_count)

# La Defense towers
ldx, ldy, ldr, ys, ye = history.LA_DEFENSE
for _ in range(38):
    a = rand.uniform(0, 2 * math.pi); rr_ = ldr * math.sqrt(rand.uniform(0.05, 1))
    x, y = ldx + rr_ * math.cos(a), ldy + rr_ * math.sin(a)
    r, c = cell(x, y)
    if water[r, c] or blocked[r, c]:
        continue
    yr = rand.uniform(ys, ye)
    k = int(rand.integers(0, 10)); k -= k % 3     # tower variants are k%3==0
    fw, fd, fh = FOOT["slab"][k]
    B["x"].append(x); B["y"].append(y); B["rot"].append(math.radians(7))
    B["sx"].append(rand.uniform(0.9, 1.3) * 1.5); B["sy"].append(rand.uniform(0.9, 1.3) * 1.5); B["sz"].append(rand.uniform(1.0, 1.9) * 1.5)
    B["birth"].append(yr); B["death"].append(9999.0); B["era"].append(ERA_ID["slab"]); B["kit"].append(k)
    occ_death[r, c] = 9999.0
log("total buildings", len(B["x"]))

for k in B:
    B[k] = np.array(B[k], dtype=np.float32 if k not in ("era", "kit") else np.int16)
B["dur"] = np.array([dur_of(y) for y in B["birth"]], dtype=np.float32)

# ------------------------------------------------------------------ trees
# raster of earliest building birth per cell (dilated) => trees die when the city arrives
built_year = np.full((NY, NX), 9999.0, dtype=np.float32)
rb, cb = cells(B["x"], B["y"])
np.minimum.at(built_year, (rb, cb), B["birth"])
built_year = ndimage.minimum_filter(built_year, size=5)
log("built_year raster")

Tr = {k: [] for k in ("x", "y", "rot", "s", "death", "kind")}


def scatter(step, keep, mask_fn, kinds, death_fn, jitter=0.45):
    gx = np.arange(X0 + step / 2, X1, step)
    gy = np.arange(Y0 + step / 2, Y1, step)
    GX, GY = np.meshgrid(gx, gy)
    GX = GX.ravel() + rand.uniform(-step * jitter, step * jitter, GX.size)
    GY = GY.ravel() + rand.uniform(-step * jitter, step * jitter, GY.size)
    rr, cc = cells(GX, GY)
    ok = mask_fn(rr, cc) & (rand.random(GX.size) < keep)
    GX, GY, rr, cc = GX[ok], GY[ok], rr[ok], cc[ok]
    n = len(GX)
    Tr["x"].append(GX.astype(np.float32)); Tr["y"].append(GY.astype(np.float32))
    Tr["rot"].append(rand.uniform(0, 2 * math.pi, n).astype(np.float32))
    Tr["s"].append(rand.uniform(0.8, 1.35, n).astype(np.float32))
    Tr["kind"].append(rand.choice(kinds, n).astype(np.int16))
    Tr["death"].append(death_fn(rr, cc, n).astype(np.float32))
    return n


def death_city(rr, cc, n):
    d = built_year[rr, cc] - rand.uniform(0, 18, n)
    # roads kill trees too
    d = np.minimum(d, np.where(road_mask[rr, cc], road_year[rr, cc] - 3, 9999.0))
    # a share of suburban garden trees survives
    survive = (built_year[rr, cc] >= 1880) & (rand.random(n) < 0.28) & ~paris_mask[rr, cc]
    d = np.where(survive, 9999.0, d)
    # farmland: trees also disappear in the ring around the growing city (fields), keep fewer
    return d


n1 = scatter(34, 0.72, lambda rr, cc: (~water[rr, cc]) & (~forest[rr, cc]) & (~blocked[rr, cc]) & (d_water[rr, cc] * CELL > 12),
             [0, 1, 3, 4, 0, 1, 3, 4, 2], death_city)
n2 = scatter(22, 0.9, lambda rr, cc: forest[rr, cc] & (~water[rr, cc]), [0, 1, 3, 4, 2, 5, 0, 1],
             lambda rr, cc, n: np.full(n, 9999.0))
n3 = scatter(24, 0.55, lambda rr, cc: park[rr, cc] & (~water[rr, cc]) & (~forest[rr, cc]), [0, 1, 3, 4, 0, 1],
             lambda rr, cc, n: np.full(n, 9999.0))
for k in Tr:
    Tr[k] = np.concatenate(Tr[k])
log("trees", n1, n2, n3, len(Tr["x"]))

# ------------------------------------------------------------------ terrain heightmap (50 m)
TSTEP = 50
tx = np.arange(X0, X1 + 1, TSTEP); ty = np.arange(Y0, Y1 + 1, TSTEP)
TX, TY = np.meshgrid(tx, ty)
raw = terrain.height(TX, TY)
rt, ct = cells(TX.ravel(), TY.ravel())
dw = (d_water[rt, ct] * CELL).reshape(TX.shape)
damp = np.clip(dw / 450.0, 0, 1) ** 1.6
hmap = np.maximum((raw + 6.0) * damp, 0.0).astype(np.float32)
log("heightmap", hmap.shape, float(hmap.max()))


def sample_h(xs, ys):
    fx = (xs - X0) / TSTEP; fy = (ys - Y0) / TSTEP
    i = np.clip(fx.astype(int), 0, hmap.shape[1] - 2); j = np.clip(fy.astype(int), 0, hmap.shape[0] - 2)
    u = fx - i; v = fy - j
    return ((1 - u) * (1 - v) * hmap[j, i] + u * (1 - v) * hmap[j, i + 1] + (1 - u) * v * hmap[j + 1, i] + u * v * hmap[j + 1, i + 1]).astype(np.float32)


B["z"] = sample_h(B["x"], B["y"])
Tr["z"] = sample_h(Tr["x"], Tr["y"])

# ------------------------------------------------------------------ rail
rail_pieces = []
for r in geo["rail"]:
    ln = LineString(r["pts"])
    if ln.length < 10:
        continue
    n = max(1, int(math.ceil(ln.length / 60)))
    pts = [ln.interpolate(i / n, normalized=True) for i in range(n + 1)]
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        d = math.hypot((a.x + b.x) / 2 - CENTER[0], (a.y + b.y) / 2 - CENTER[1])
        rail_pieces.append((a.x, a.y, b.x, b.y, 1838 + d / 1000 * 1.3 + rand.uniform(0, 6), 1.0 if r.get("bridge") else 0.0))
rail_pieces = np.array(rail_pieces, dtype=np.float32)
log("rail pieces", len(rail_pieces))

# ------------------------------------------------------------------ walls
wall_pieces = []
for name, pl, b, d, h in history.WALLS:
    if pl is None:
        ring = list(cite.buffer(-12).simplify(15).exterior.coords)
    elif pl == "PARIS":
        ring = list(paris.buffer(-350).simplify(60).exterior.coords)
    else:
        ring = pl
    for i in range(len(ring) - 1):
        (ax, ay), (bx, by) = ring[i], ring[i + 1]
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(math.ceil(L / 30)))
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            x0, y0 = ax + (bx - ax) * t0, ay + (by - ay) * t0
            x1, y1 = ax + (bx - ax) * t1, ay + (by - ay) * t1
            r, c = cell((x0 + x1) / 2, (y0 + y1) / 2)
            if water[r, c]:
                continue
            wall_pieces.append((x0, y0, x1, y1, b + rand.uniform(0, 12), d + rand.uniform(-10, 10), h, 1.0 if k % 3 == 0 else 0.0))
wall_pieces = np.array(wall_pieces, dtype=np.float32)
log("wall pieces", len(wall_pieces))

# ------------------------------------------------------------------ parks (json for Blender)
parks_json = []
for p, kind, name in green:
    yr = None
    for key, v in history.PARK_YEARS.items():
        if key.lower() in name.lower():
            yr = v; break
    if yr is None:
        r, c = cell(p.centroid.x, p.centroid.y)
        yr = 9999 if kind == "forest" and not paris_mask[r, c] else (history.PARK_DEFAULT_YEAR if paris_mask[r, c] else 1950)
        if kind == "forest":
            yr = -9999
    ps = p.simplify(6)
    geoms = list(ps.geoms) if isinstance(ps, MultiPolygon) else [ps]
    for g in geoms:
        if g.area < 5000:
            continue
        parks_json.append({"kind": kind, "name": name, "birth": yr,
                           "outer": [[round(x, 1), round(y, 1)] for x, y in g.exterior.coords],
                           "holes": [[[round(x, 1), round(y, 1)] for x, y in h.coords] for h in g.interiors]})

water_json = []
for w in geo["water"]:
    water_json.append(w)
canals_json = geo["canals"]

meta = {
    "raster": {"x0": X0, "x1": X1, "y0": Y0, "y1": Y1, "cell": CELL},
    "terrain": {"x0": X0, "y0": Y0, "step": TSTEP, "nx": hmap.shape[1], "ny": hmap.shape[0]},
    "parks": parks_json,
    "water": water_json,
    "canals": canals_json,
    "cite": [[round(x, 1), round(y, 1)] for x, y in cite.exterior.coords],
    "paris": [[round(x, 1), round(y, 1)] for x, y in paris.exterior.coords],
    "counts": {"buildings": int(len(B["x"])), "trees": int(len(Tr["x"])), "road_pieces": int(len(road_pieces))},
}
json.dump(meta, open(os.path.join(CACHE, "scene_meta.json"), "w"))

# ------------------------------------------------------------------ baked rasters for shaders (10 m)
shore_land = (255 * np.clip(1.0 - (d_water * CELL - 2.0) / 16.0, 0, 1)).astype(np.uint8)
d_land = ndimage.distance_transform_edt(water).astype(np.float32) * CELL
water_depth = (255 * np.clip(d_land / 45.0, 0, 1)).astype(np.uint8)
park_year_img = Image.new("L", (NX, NY), 0)
kind_img = Image.new("L", (NX, NY), 0)
dp = ImageDraw.Draw(park_year_img); dk = ImageDraw.Draw(kind_img)
for pj in sorted(parks_json, key=lambda p: -Polygon(p["outer"]).area):
    yr = pj["birth"]
    enc = int(np.clip((yr + 300) / 2400 * 254 + 1, 1, 255)) if yr < 9000 else 255
    kv = {"forest": 255, "park": 128, "cemetery": 64}[pj["kind"]]
    dp.polygon([to_px(x, y) for x, y in pj["outer"]], fill=enc)
    dk.polygon([to_px(x, y) for x, y in pj["outer"]], fill=kv)
    for h in pj["holes"]:
        dp.polygon([to_px(x, y) for x, y in h], fill=0)
        dk.polygon([to_px(x, y) for x, y in h], fill=0)
park_year_r = np.array(park_year_img, dtype=np.uint8)
kind_r = np.array(kind_img, dtype=np.uint8)
water_dil = ndimage.binary_dilation(water, iterations=1)
np.savez_compressed(os.path.join(CACHE, "rasters.npz"), shore_land=shore_land, water_depth=water_depth,
                    park_year=park_year_r, kind=kind_r, water=water_dil, birth=birth.astype(np.float16))
log("rasters saved")

np.savez_compressed(os.path.join(CACHE, "scene_data.npz"),
                    b_x=B["x"], b_y=B["y"], b_z=B["z"], b_rot=B["rot"], b_sx=B["sx"], b_sy=B["sy"], b_sz=B["sz"],
                    b_birth=B["birth"], b_death=B["death"], b_dur=B["dur"], b_era=B["era"], b_kit=B["kit"],
                    t_x=Tr["x"], t_y=Tr["y"], t_z=Tr["z"], t_rot=Tr["rot"], t_s=Tr["s"], t_death=Tr["death"], t_kind=Tr["kind"],
                    roads=road_pieces, rail=rail_pieces, walls=wall_pieces, hmap=hmap)
log("saved", meta["counts"])

# quick QA map of birth years
qa = np.clip((birth - (-300)) / 2400.0, 0, 1)
qa[birth >= 9000] = np.nan
img = np.zeros((NY, NX, 3), dtype=np.uint8)
img[..., 1] = 90; img[..., 0] = 70; img[..., 2] = 40
v = np.nan_to_num(qa, nan=0)
col = (np.stack([255 * (1 - v), 255 * v, 120 * (1 - v)], axis=-1)).astype(np.uint8)
img[~np.isnan(qa)] = col[~np.isnan(qa)]
img[water] = (60, 120, 140)
Image.fromarray(img[::4, ::4]).save(os.path.join(CACHE, "qa_birth.png"))
# building map
img2 = np.zeros((NY, NX, 3), dtype=np.uint8); img2[...] = (110, 130, 80); img2[water] = (60, 120, 140)
era_col = np.array([(200, 160, 90), (220, 60, 40), (210, 110, 70), (200, 200, 200), (190, 175, 150), (220, 190, 180), (230, 150, 150), (120, 120, 140)], dtype=np.uint8)
last = B["death"] >= 9000
img2[rb[last], cb[last]] = era_col[B["era"][last]]
Image.fromarray(img2[::3, ::3]).save(os.path.join(CACHE, "qa_buildings.png"))
log("done")
