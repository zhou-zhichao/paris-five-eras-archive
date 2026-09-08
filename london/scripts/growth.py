"""City growth engine (London).

Reads  : data/geo.json, data/kit_footprints.json, history.py, terrain.py, timeline.py
Writes : cache/scene_data.npz, cache/rasters.npz, cache/scene_meta.json

Everything is computed on a 10 m raster covering 46 x 34 km around St Paul's.
Buildings are placed along streets (both sides) with an era-dependent spacing,
carry birth / death years, a kit id and a replacement chain (with the Great Fire,
the Blitz, dock building, slum clearance and estate regeneration as dated
destruction / rebuild events) so the city recolours and rebuilds itself over time.
"""
import json, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import constrained_delaunay_triangles

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timeline, terrain, history

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(HERE, "..", "cache")
os.makedirs(CACHE, exist_ok=True)

X0, X1, Y0, Y1 = -22000, 24000, -16000, 18000
CELL = 10
NX, NY = (X1 - X0) // CELL, (Y1 - Y0) // CELL
RNG = np.random.default_rng(7)
T0 = time.time()

ERA_NAMES = ["celtic", "roman", "saxon", "medieval", "tudor", "georgian", "victorian", "interwar", "postwar", "modern", "estate", "tower"]
ERA_ID = {n: i for i, n in enumerate(ERA_NAMES)}
# the reference film exaggerates building size ~2x relative to the map; we do the same
BUILD_SCALE = 2.0
SPACING = {k: v * BUILD_SCALE * 0.85 for k, v in {"celtic": 11.0, "roman": 12.0, "saxon": 12.0, "medieval": 6.0, "tudor": 6.5, "georgian": 9.5,
           "victorian": 9.5, "interwar": 14.0, "postwar": 20.0, "modern": 22.0, "estate": 60.0, "tower": 70.0}.items()}
HALF_WIDTH = {"motorway": 20, "trunk": 14, "primary": 11, "secondary": 8.5, "tertiary": 6.5, "residential": 5.0,
              "unclassified": 5.0, "living_street": 4.0, "pedestrian": 3.5, "roman": 5.0, "path": 2.5, "route": 6.5}
ROAD_WIDTH = {"motorway": 26, "trunk": 20, "primary": 15, "secondary": 11, "tertiary": 8.5, "residential": 6.5,
              "unclassified": 6.0, "living_street": 5.5, "pedestrian": 5.0, "roman": 11.0, "path": 4.0, "route": 9.0}
CLASS_RANK = {"motorway": 0, "route": 1, "trunk": 1, "primary": 2, "secondary": 3, "tertiary": 4, "roman": 4, "residential": 5,
              "unclassified": 5, "living_street": 6, "pedestrian": 6, "path": 7}


def log(*a):
    print(f"[{time.time()-T0:6.1f}s]", *a, flush=True)


# ------------------------------------------------------------------ raster helpers
def to_px(x, y):
    return ((x - X0) / CELL, (Y1 - y) / CELL)


def cell(x, y):
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
        geoms = list(p.geoms) if isinstance(p, MultiPolygon) else [p]
        for g in geoms:
            if g.is_empty or not hasattr(g, "exterior"):
                continue
            d.polygon([to_px(x, y) for x, y in g.exterior.coords], fill=value)
            for h in g.interiors:
                d.polygon([to_px(x, y) for x, y in h.coords], fill=0)
    return im


def mask_of(polys):
    return np.array(draw_polys(polys), dtype=bool)


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


water_items = [(jpoly(w), w) for w in geo["water"]]
water_items = [(p, w) for p, w in water_items if p is not None and not p.is_empty]
river_polys = [p for p, w in water_items if w["kind"] == "river"]
other_polys = [p for p, w in water_items if w["kind"] != "river"]
canal_polys = [LineString(c["pts"]).buffer(c["width"] / 2) for c in geo["canals"] if len(c["pts"]) >= 2]
river = mask_of(river_polys)
water_perm = mask_of(river_polys + other_polys + canal_polys)          # water that exists today
# historical water: appears (docks) / disappears (lost rivers, foreshore)
water_until = np.zeros((NY, NX), dtype=np.float32)      # cells are water until this year (0 = never temporary)
water_from = np.full((NY, NX), 9999.0, dtype=np.float32)  # cells become water at this year (docks)
water_events_json = []
for w in history.WATER_EVENTS:
    if "line" in w:
        g = w["line"].buffer(w["width"] / 2)
    else:
        g = w["poly"]
    m = mask_of([g])
    if w["birth"] <= -9000:
        water_until[m] = np.maximum(water_until[m], w["death"])
    else:
        water_from[m] = np.minimum(water_from[m], w["birth"])
        if w["death"] < 9000:
            water_until[m] = np.maximum(water_until[m], w["death"])
    gg = g.simplify(2)
    for part in (gg.geoms if isinstance(gg, MultiPolygon) else [gg]):
        water_events_json.append({"name": w["name"], "birth": w["birth"], "death": w["death"],
                                  "outer": [[round(x, 1), round(y, 1)] for x, y in part.exterior.coords],
                                  "holes": [[[round(x, 1), round(y, 1)] for x, y in h.coords] for h in part.interiors]})
water_hist = (water_until > 0) & ~water_perm            # historic water that is land today
water_any = water_perm | water_hist
log("water masks", int(water_perm.sum()), "historic", int(water_hist.sum()))

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
park_polys = [p for p, k, n in green if k not in ("forest",)]
forest = mask_of(forest_polys)
park = mask_of(park_polys)
log("green masks", int(forest.sum()), int(park.sum()))

london_full = jpoly(geo["london"]) if geo.get("london") else box(X0, Y0, X1, Y1)
inner = history.INNER
inner_mask = mask_of([inner])
london_mask = mask_of([london_full])
city_mask = mask_of([history.CITY])
log("inner area km2", round(inner.area / 1e6, 1))

# landmark footprints -> blocked while the landmark stands (houses may exist before it is built and are
# cleared for it; the site is free again after its demolition)
blocked_polys = []
blocked_birth = np.full((NY, NX), 9999.0, dtype=np.float32)
blocked_death = np.full((NY, NX), -9999.0, dtype=np.float32)
for name, x, y, rot, b, d, builder, prm in history.LANDMARKS:
    if builder == "airport":
        w, dd = 4200, 1400
    elif builder == "stadium":
        w, dd = prm.get("a", 60) * 2.3 + 12, prm.get("b", 60) * 2.3 + 12
    else:
        w, dd = prm.get("w", 60) * 1.25 + 12, prm.get("d", 60) * 1.25 + 12
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in ((-w / 2, -dd / 2), (w / 2, -dd / 2), (w / 2, dd / 2), (-w / 2, dd / 2))]
    pg = Polygon(pts)
    blocked_polys.append(pg)
    m = mask_of([pg])
    blocked_birth[m] = np.minimum(blocked_birth[m], b)
    blocked_death[m] = np.maximum(blocked_death[m], d if d < 9000 else 9999.0)
blocked = mask_of(blocked_polys)
log("blocked", int(blocked.sum()))


def site_free(r, c, year):
    """Can a house be born at cell (r, c) in `year`?  Returns (ok, cap): cap = year the site is cleared for a landmark."""
    if not blocked[r, c]:
        return True, 9999.0
    b, d = blocked_birth[r, c], blocked_death[r, c]
    if year < b - 1:
        return True, b
    if year > d:
        return True, 9999.0
    return False, 9999.0

d_water = ndimage.distance_transform_edt(~water_perm).astype(np.float32)
# shore band (sand) only around water bodies that are actually drawn (matches build_scene's 15000 m2 filter)
big_water = mask_of(river_polys + [p for p, w in water_items if w["kind"] != "river" and w["area"] >= 15000] + canal_polys)
big_water &= ~(water_from < 9000)          # no shore band around docks / reservoirs / later lakes
d_water_draw = ndimage.distance_transform_edt(~big_water).astype(np.float32)
log("water edt")

# ------------------------------------------------------------------ growth field
birth = np.full((NY, NX), 9999.0, dtype=np.float32)
zone_kit = np.full((NY, NX), -1, dtype=np.int8)
noise = smooth_noise(20, 1)
prev = np.zeros((NY, NX), dtype=bool)
zone_index = {}
ZONES = list(history.ZONES)
if history.RESEARCH_ZONES:
    # researched district polygons refine the hand-authored rings; everything is applied in start-year order
    # so the "distance from what is already built" gradient stays meaningful (earlier year wins per cell)
    ZONES = sorted(ZONES + history.RESEARCH_ZONES, key=lambda z: z[2])
    log("zones: hand", len(history.ZONES), "researched", len(history.RESEARCH_ZONES))
interwar_mask = None
for zi, (name, poly, ys, ye, kit) in enumerate(ZONES):
    if isinstance(poly, tuple):
        if poly[0] == "INTERWAR_BUFFER":
            base = unary_union([Polygon(p) if not hasattr(p, "exterior") else p for n, p, a, b, k in ZONES if n == "interwar"])
            Pg = base.buffer(poly[1]).intersection(london_full.buffer(1500))
        else:
            continue
    else:
        Pg = poly
    mask = mask_of([Pg]) & ~water_any
    zone_index[name] = zi
    if not prev.any():
        seed = np.zeros_like(prev)
        r, c = cell(Pg.centroid.x, Pg.centroid.y)
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
    zone_kit[sel] = ERA_ID.get(kit, ERA_ID["victorian"])
    prev |= mask
    if name == "interwar":
        interwar_mask = mask.copy()
    log("zone", name, "cells", int(mask.sum()), "years", ys, ye)

# villages
yy, xx = np.mgrid[0:NY, 0:NX]
XX = X0 + (xx + 0.5) * CELL
YY = Y1 - (yy + 0.5) * CELL
village_core = np.zeros((NY, NX), dtype=bool)
for name, vx, vy, vr, ys, ye in history.VILLAGES:
    r0, c0 = cell(vx, vy)
    R = int(vr / CELL) + 2
    rs, re = max(r0 - R, 0), min(r0 + R, NY)
    cs, ce = max(c0 - R, 0), min(c0 + R, NX)
    dx = XX[rs:re, cs:ce] - vx; dy = YY[rs:re, cs:ce] - vy
    dd = np.sqrt(dx * dx + dy * dy) / vr
    y = ys + (ye - ys) * np.clip(dd, 0, 1) ** 1.3 + noise[rs:re, cs:ce] * (ye - ys) * 0.08
    sub = birth[rs:re, cs:ce]
    sel = (dd <= 1.0) & (y < sub) & ~water_any[rs:re, cs:ce]
    sub[sel] = y[sel]
    zone_kit[rs:re, cs:ce][sel] = -1
    village_core[rs:re, cs:ce] |= dd <= 0.6
log("villages applied", len(history.VILLAGES))

# historic water delays building; docks dug later are handled as events
delay = water_hist & (birth < water_until)
birth[delay] = np.maximum(birth[delay], water_until[delay] + 2.0)

# density (probability that a candidate building is kept)
d_inner = ndimage.distance_transform_edt(~inner_mask).astype(np.float32) * CELL
density = np.where(d_inner <= 0, 1.0, np.clip(1.05 - (d_inner - 1500) / 22000, 0.45, 1.0)).astype(np.float32)
density *= (0.85 + 0.15 * np.clip(smooth_noise(30, 2), -1, 1))
density[~london_mask] *= 0.75
density = np.maximum(density, np.where(village_core, 0.9, 0.0))
log("density")

# ------------------------------------------------------------------ roads
CENTER = np.array(history.CENTER, dtype=np.float64)
ROAD_YEAR_KEYS = [(k.lower(), v) for k, v in history.ROAD_YEARS.items()]


def named_year(name):
    if not name:
        return None
    n = name.lower()
    best = None
    for k, v in ROAD_YEAR_KEYS:
        if k in n and (best is None or v < best):
            best = v
    return best


def road_year_at(x, y, cls, name, is_periph, field, named):
    d = math.hypot(x - CENTER[0], y - CENTER[1])
    if is_periph:
        ang = math.atan2(x - CENTER[0], y - CENTER[1])
        return 1975 + 11 * ((ang + math.pi) / (2 * math.pi))
    if cls == "motorway":
        return 1959 + d / 1000 * 0.9 if named is None else named
    if cls in ("trunk", "primary"):
        cand = 1100 + d * 0.045
    elif cls == "secondary":
        cand = 1300 + d * 0.05
    elif cls == "tertiary":
        cand = 1500 + d * 0.06
    else:
        cand = 9999
    if named is not None:
        cand = min(cand, named)
    return min(field, cand)


# Roman street grid inside the walled city
RG = history.ROMAN_GRID
ROMAN_POLY = history.CITY.difference(unary_union(river_polys))
CARDO = math.radians(90 - RG["bearing"])
ux, uy = math.cos(CARDO), math.sin(CARDO)
vx_, vy_ = math.cos(CARDO - math.pi / 2), math.sin(CARDO - math.pi / 2)
roman_roads = []
origin = np.array(RG["origin"], dtype=np.float64)
for k in range(-14, 15):
    for axis in (0, 1):
        step = RG["block"]
        if axis == 0:
            p0 = origin + k * step * np.array([vx_, vy_]) - 1500 * np.array([ux, uy]); p1 = origin + k * step * np.array([vx_, vy_]) + 1500 * np.array([ux, uy])
        else:
            p0 = origin + k * step * np.array([ux, uy]) - 1500 * np.array([vx_, vy_]); p1 = origin + k * step * np.array([ux, uy]) + 1500 * np.array([vx_, vy_])
        ln = LineString([tuple(p0), tuple(p1)]).intersection(ROMAN_POLY)
        for g in (ln.geoms if hasattr(ln, "geoms") else [ln]):
            if isinstance(g, LineString) and g.length > 60:
                roman_roads.append(g)
log("roman grid roads", len(roman_roads))

roads = []
for r in geo["roads"]:
    if r.get("tunnel") or len(r["pts"]) < 2:
        continue
    ln = LineString(r["pts"])
    if ln.length < 8:
        continue
    nm = r.get("name", "")
    roads.append({"line": ln, "cls": r["cls"], "name": nm, "bridge": r["bridge"], "periph": (r.get("ref", "") == "M25"),
                  "death": 9999.0, "synthetic": False, "named": named_year(nm)})
for g in roman_roads:
    roads.append({"line": g, "cls": "roman", "name": "", "bridge": False, "periph": False, "death": 450.0, "synthetic": True, "named": None})
roads.sort(key=lambda r: (CLASS_RANK.get(r["cls"], 9), -r["line"].length))
log("roads", len(roads))

# researched road lines (Roman roads, turnpikes, arterials, motorways): pieces within 45 m take their year
ROAD_LINE_GEOMS = [g for g, yr, nm in history.ROAD_LINES]
road_line_tree = STRtree(ROAD_LINE_GEOMS) if ROAD_LINE_GEOMS else None


def researched_road_year(x, y):
    if road_line_tree is None:
        return None
    pt = Point(x, y)
    idx = road_line_tree.query(pt.buffer(45))
    best = None
    for i in idx:
        g, yr, nm = history.ROAD_LINES[int(i)]
        if g.distance(pt) <= 45 and (best is None or yr < best):
            best = yr
    return best


RAIL_LINE_GEOMS = [g for g, yr, nm in history.RAIL_LINES]
rail_line_tree = STRtree(RAIL_LINE_GEOMS) if RAIL_LINE_GEOMS else None


def researched_rail_year(x, y):
    if rail_line_tree is None:
        return None
    pt = Point(x, y)
    idx = rail_line_tree.query(pt.buffer(400))
    best = None
    for i in idx:
        g, yr, nm = history.RAIL_LINES[int(i)]
        if g.distance(pt) <= 400 and (best is None or yr < best):
            best = yr
    return best


roman_mask = mask_of([ROMAN_POLY])

PIECE = 40.0
road_pieces = []   # x0,y0,x1,y1,width,birth,death,over_water,cls_rank
for rd in roads:
    ln = rd["line"]
    coords = np.array(ln.coords)
    v = coords[-1] - coords[0]
    mid = coords.mean(axis=0)
    nv = np.linalg.norm(v)
    r0, c0 = cell(mid[0], mid[1])
    in_roman = roman_mask[r0, c0] and not rd["synthetic"]
    grid_aligned = False
    if in_roman and nv > 1:
        ang = math.atan2(v[1], v[0])
        rel = (ang - CARDO) % (math.pi / 2)
        grid_aligned = min(rel, math.pi / 2 - rel) < math.radians(12)
    n = max(1, int(math.ceil(ln.length / PIECE)))
    pts = [ln.interpolate(i / n, normalized=True) for i in range(n + 1)]
    rd["pieces"] = []
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        mx, my = (a.x + b.x) / 2, (a.y + b.y) / 2
        r, c = cell(mx, my)
        if river[r, c]:
            continue                       # Thames / Lea crossings are hand-authored bridges
        over_water = 1.0 if water_perm[r, c] else 0.0
        field = float(birth[r, c])
        y = road_year_at(mx, my, rd["cls"], rd["name"], rd["periph"], field, rd["named"])
        if CLASS_RANK.get(rd["cls"], 9) <= 3 and not rd["synthetic"]:
            ry_ = researched_road_year(mx, my)
            if ry_ is not None:
                y = min(y, ry_) if rd["cls"] != "motorway" else ry_
        if rd["synthetic"]:
            y = 50 + math.hypot(mx - origin[0], my - origin[1]) / 12.0
        elif in_roman and not grid_aligned and y < 450 and CLASS_RANK[rd["cls"]] >= 3:
            y = max(y, 886.0 + RNG.uniform(0, 150))
        elif in_roman and y < 450:
            y = max(y, 50.0)
        if water_hist[r, c] and y < water_until[r, c]:
            y = water_until[r, c] + 1
        if y >= 9000:
            continue
        y -= 12.0   # streets slightly precede their houses
        rd["pieces"].append((a.x, a.y, b.x, b.y, y))
        road_pieces.append((a.x, a.y, b.x, b.y, ROAD_WIDTH.get(rd["cls"], 6), y, rd["death"], over_water, CLASS_RANK.get(rd["cls"], 9)))
road_pieces = np.array(road_pieces, dtype=np.float32)
log("road pieces", len(road_pieces))

road_year_img = Image.new("F", (NX, NY), 9999.0)
dr = ImageDraw.Draw(road_year_img)
order = np.argsort(-road_pieces[:, 5])
for i in order:
    x0, y0, x1, y1, w, y, dth, ow, rk = road_pieces[i]
    dr.line([to_px(x0, y0), to_px(x1, y1)], fill=float(y), width=max(1, int(w / CELL) + 1))
road_year = np.array(road_year_img, dtype=np.float32)
road_mask = road_year < 9000
d_road = ndimage.distance_transform_edt(~road_mask).astype(np.float32) * CELL
log("road rasters")

# ------------------------------------------------------------------ events (destruction / rebuild)
def event_duration(ev):
    """Years over which an event's destruction is spread (instant catastrophes vs slow decline)."""
    n = ev["name"].lower()
    if any(k in n for k in ("fire", "burn", "blitz", "bomb", "explosion", "revolt", "ira", "boudica", "boudican", "tooley")):
        return 0.9
    if "black death" in n or "contraction" in n:
        return 60.0
    if "dissolution" in n:
        return 12.0
    if "v-1" in n or "v-2" in n or "flying" in n:
        return 1.5
    if ev.get("rebuild"):
        return max(1.0, float(ev["rebuild"][0]) - float(ev["year"]))      # clearances: spread until rebuilding starts
    return 10.0


def event_wave(ev):
    """(origin x, origin y, max distance) for fires that spread across their zone; None otherwise."""
    n = ev["name"].lower()
    if "fire" not in n and "burn" not in n and "boudica" not in n:
        return None
    try:
        b = ev["poly"].bounds
    except Exception:
        return None
    if "great fire of london" in n:
        ox, oy = history.ll(-0.0855, 51.5095)          # Pudding Lane
    else:
        cpt = ev["poly"].centroid; ox, oy = cpt.x, cpt.y
    dmax = max(math.hypot(b[0] - ox, b[1] - oy), math.hypot(b[2] - ox, b[1] - oy), math.hypot(b[0] - ox, b[3] - oy), math.hypot(b[2] - ox, b[3] - oy))
    return (ox, oy, max(dmax, 50.0))


EVENTS = []
for ev in history.EVENTS:
    if ev["fraction"] <= 0:
        continue
    EVENTS.append({"mask": mask_of([ev["poly"]]), "duration": event_duration(ev), "wave": event_wave(ev), **ev})
# docks: cells flooded at `water_from` -> buildings die, land returns when filled
dock_cells = water_from < 9000
if dock_cells.any():
    for yr in np.unique(water_from[dock_cells]):
        m = water_from == yr
        until = water_until[m]
        fill = float(np.median(until[until > 0])) if (until > 0).any() else 9999.0
        EVENTS.append({"name": f"dock_{int(yr)}", "mask": m, "year": float(yr), "fraction": 1.0, "rebuild": None,
                       "resettle": ((fill + 3, fill + 25) if fill < 9000 else None)})
EVENTS.sort(key=lambda e: e["year"])
log("events", [(e["name"], e["year"]) for e in EVENTS])

# ------------------------------------------------------------------ building placement
occ_death = np.full((NY, NX), -1e9, dtype=np.float32)
inner_buf = mask_of([inner.buffer(2500)])
core_mask = np.zeros((NY, NX), dtype=bool)
for zn in ("londinium_peak", "medieval_city", "medieval_suburbs", "southwark_medieval", "strand_ribbon", "westminster_medieval", "tudor", "stuart"):
    if zn in zone_index:
        core_mask |= mask_of([ZONES[zone_index[zn]][1]])
estate_mask = np.zeros((NY, NX), dtype=np.float32)
estate_year = np.zeros((NY, NX, 2), dtype=np.float32)
for ex, ey, er, ys, ye in history.ESTATES:
    m = mask_of([Point(ex, ey).buffer(er)])
    estate_mask[m] = 1.0
    estate_year[m, 0] = ys; estate_year[m, 1] = ye
tower_mask = np.zeros((NY, NX), dtype=np.float32)
tower_info = np.zeros((NY, NX, 3), dtype=np.float32)
for tx, ty, tr, ys, ye, th in history.TOWERS:
    m = mask_of([Point(tx, ty).buffer(tr)])
    tower_mask[m] = 1.0
    tower_info[m, 0] = ys; tower_info[m, 1] = ye; tower_info[m, 2] = th
log("estate / tower masks", int((estate_mask > 0).sum()), int((tower_mask > 0).sum()))

YEARS = np.arange(-400, 2100)
DUR = np.array([timeline.sprout_years(float(y)) for y in YEARS], dtype=np.float32)
def dur_of(y):
    return float(DUR[min(max(int(y + 400), 0), len(DUR) - 1)])

B = {k: [] for k in ("x", "y", "rot", "sx", "sy", "sz", "birth", "death", "era", "kit")}
rand = np.random.default_rng(11)


def kit_for(year, r, c):
    zk = int(zone_kit[r, c])
    if year < 43:
        return "celtic"
    if year < 450:
        return "roman"
    if year < 1066:
        return "saxon"
    if year < 1500:
        return "medieval"
    if year < 1670:
        return "tudor"
    if year < 1837:
        return "georgian"
    if year < 1919:
        return "victorian"
    if year < 1945:
        return "interwar" if (zk == ERA_ID["interwar"] or not inner_mask[r, c]) else "victorian"
    if tower_mask[r, c] > 0 and year >= tower_info[r, c, 0] and rand.random() < 0.7:
        return "tower"
    if year < 1982:
        if estate_mask[r, c] > 0 and estate_year[r, c, 0] - 3 <= year <= estate_year[r, c, 1] + 3 and rand.random() < 0.75:
            return "estate"
        return "postwar" if inner_buf[r, c] else "interwar"
    return "modern"


def natural_death(e, year, r, c):
    """(death year, next kit or None) for an ordinary building of era e born in `year`."""
    u = rand.random()
    if e == "celtic":
        return rand.uniform(45, 70), "roman"
    if e == "roman":
        return rand.uniform(340, 450), None
    if e == "saxon":
        return rand.uniform(1080, 1260), "medieval"
    if e == "medieval":
        if core_mask[r, c]:
            return rand.uniform(1480, 1700), "tudor"
        return rand.uniform(1720, 1900), "georgian"
    if e == "tudor":
        if u < 0.85:
            return rand.uniform(1700, 1850), "georgian"
        return rand.uniform(1850, 1900), "victorian"
    if e == "georgian":
        if u < 0.40:
            return rand.uniform(1850, 1910), "victorian"
        if u < 0.55:
            return rand.uniform(1950, 2005), "modern"
        return 9999.0, None
    if e == "victorian":
        if inner_buf[r, c] and u < 0.22:
            return rand.uniform(1955, 2015), "modern"
        return 9999.0, None
    if e == "interwar":
        if u < 0.05:
            return rand.uniform(1990, 2020), "modern"
        return 9999.0, None
    if e == "postwar":
        if u < 0.25:
            return rand.uniform(2000, 2022), "modern"
        return 9999.0, None
    if e == "estate":
        if u < 0.30:
            return rand.uniform(1998, 2022), "modern"
        return 9999.0, None
    return 9999.0, None


def chain(era, year, r, c, cap=9999.0):
    """[(era, birth, death)] generations for a building first built in `year` at cell (r, c).
    `cap`: the site is cleared for a landmark in that year (no later generations)."""
    gens = []
    e, y = era, year
    for _ in range(8):
        if e is None or y >= 9000 or y >= cap:
            break
        d, nxt = natural_death(e, y, r, c)
        ny = d
        if d > cap:
            d = cap + rand.uniform(-1.0, 0.5); nxt = None
        # dated events between y and d
        for ev in EVENTS:
            if ev["year"] <= y + 0.5 or ev["year"] >= d:
                continue
            if not ev["mask"][r, c] or rand.random() > ev["fraction"]:
                continue
            # no catastrophe simulation: an event only says that the houses here get replaced, one by one,
            # at random moments of the rebuilding period, each new house taking the old one's place at once
            if ev["rebuild"]:
                rs, re, k = ev["rebuild"]
                d = rand.uniform(max(rs, ev["year"]), max(re, rs + 1)); ny = d; nxt = k
            elif ev["resettle"]:
                d = ev["year"] + rand.uniform(0, 30.0)          # slow abandonment
                rs, re = ev["resettle"]
                ny = rand.uniform(rs, re); nxt = kit_for(ny, r, c)
            else:
                d = ev["year"] + rand.uniform(0, ev.get("duration", 10.0))
                nxt = None
            break
        gens.append((e, y, d))
        if nxt is None or d >= 9000:
            break
        if nxt == "estate" and not (estate_mask[r, c] > 0):
            nxt = "postwar"
        if nxt == "modern" and ny >= 1985 and tower_mask[r, c] > 0 and rand.random() < 0.6:
            nxt = "tower"
        e, y = nxt, max(ny, d + 0.5)
    return gens


def place(x, y, rot, era, year, r, c, target_w, cap=9999.0, depth_scale=1.0):
    gens = chain(era, year, r, c, cap)
    if not gens:
        return
    final_death = gens[-1][2]
    occ_death[r, c] = max(occ_death[r, c], final_death)
    for e, b, d in gens:
        k = int(rand.integers(0, 10))
        fw, fd, fh = FOOT[e][k]
        if e in ("estate", "tower", "celtic"):
            sx = BUILD_SCALE
        else:
            sx = float(np.clip(target_w / (fw * BUILD_SCALE), 0.7, 1.6)) * BUILD_SCALE
        sy = float(rand.uniform(0.9, 1.25)) * BUILD_SCALE * depth_scale
        sz = float(rand.uniform(0.9, 1.15)) * BUILD_SCALE
        if e == "tower":
            th = max(tower_info[r, c, 2], 60.0)
            sz = float(np.clip(rand.uniform(0.6, 1.5) * th / fh, 0.5, 4.0)) * 1.0
            sx = sy = rand.uniform(1.2, 1.8)
        B["x"].append(x); B["y"].append(y); B["rot"].append(rot)
        B["sx"].append(sx); B["sy"].append(sy); B["sz"].append(sz)
        B["birth"].append(b); B["death"].append(d); B["era"].append(ERA_ID[e]); B["kit"].append(k)


placed_by_class = {}
for rd in roads:
    if not rd.get("pieces"):
        continue
    cls = rd["cls"]
    hw = HALF_WIDTH.get(cls, 5.0)
    if cls == "motorway" or rd["periph"]:
        continue
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
            if cls in ("trunk", "primary", "secondary") and year < 1600 and not core_mask[r, c] and not village_core[r, c]:
                keep *= 0.15 if year < 1200 else 0.3    # ribbon hamlets along the roads only
            for side in (-1, 1):
                if rand.random() > keep or rand.random() < 0.08:
                    continue
                fw, fd, fh = FOOT[era][0]
                depth = fd * 1.05 * BUILD_SCALE
                b_year = year + rand.uniform(-6, 22)
                placed = False
                for dscale in (1.0, 0.6):
                    dep = depth * dscale
                    off = hw + dep / 2 + 1.5
                    cx, cy = px + nx_ * off * side, py + ny_ * off * side
                    r1, c1 = cell(cx, cy)
                    r2, c2 = cell(cx + nx_ * dep / 2 * side, cy + ny_ * dep / 2 * side)
                    if water_perm[r1, c1] or water_perm[r2, c2] or park[r1, c1] or forest[r1, c1]:
                        break
                    ok1, cap1 = site_free(r1, c1, b_year); ok2, cap2 = site_free(r2, c2, b_year)
                    if not (ok1 and ok2):
                        break
                    if water_hist[r1, c1] and b_year < water_until[r1, c1]:
                        b_year = water_until[r1, c1] + rand.uniform(1, 15)
                    if occ_death[r1, c1] > b_year or occ_death[r2, c2] > b_year:
                        break
                    if road_mask[r2, c2] and road_year[r2, c2] < b_year:
                        continue          # the back of the house would sit on another street: try a shallower house
                    occ_death[r2, c2] = max(occ_death[r2, c2], 9999.0)
                    rot = ang + (math.pi if side > 0 else 0.0)
                    place(cx, cy, rot, era, b_year, r1, c1, sp * 0.92, cap=min(cap1, cap2), depth_scale=dscale)
                    placed = True
                    break
                if not placed:
                    continue
                placed_by_class[cls] = placed_by_class.get(cls, 0) + 1
            s += sp * rand.uniform(1.0, 1.18)
log("street buildings", len(B["x"]), placed_by_class)

# fill-mode A: dense historic core - block interiors get houses too
core_fill = 0
step = 11
gx = np.arange(-4000 + step / 2, 4000, step)
gy = np.arange(-3000 + step / 2, 3000, step)
GX, GY = np.meshgrid(gx, gy)
GX = GX.ravel() + rand.uniform(-step * 0.4, step * 0.4, GX.size)
GY = GY.ravel() + rand.uniform(-step * 0.4, step * 0.4, GY.size)
rr, cc = cells(GX, GY)
ok = core_mask[rr, cc] & (~water_any[rr, cc]) & (~park[rr, cc]) & (birth[rr, cc] < 1700) & (d_road[rr, cc] > 9)
idx = np.nonzero(ok)[0]
rand.shuffle(idx)
for i in idx:
    x, y = float(GX[i]), float(GY[i])
    r, c = rr[i], cc[i]
    year = float(birth[r, c]) + rand.uniform(0, 25)
    if occ_death[r, c] > year:
        continue
    okb, cap = site_free(r, c, year)
    if not okb:
        continue
    if year < 43 and rand.random() < 0.6:
        continue
    era = kit_for(year, r, c)
    sp = SPACING[era]
    ang = CARDO if roman_mask[r, c] and year < 450 else rand.uniform(0, math.pi)
    place(x, y, ang, era, year, r, c, sp * 0.9, cap=cap)
    core_fill += 1
log("core fill buildings", core_fill)

# fill-mode B: suburban interiors where OSM minor streets are missing
major_segs = []
for rd in roads:
    if CLASS_RANK.get(rd["cls"], 9) <= 5 and rd.get("pieces"):
        for (ax, ay, bx, by, ry) in rd["pieces"]:
            major_segs.append(LineString([(ax, ay), (bx, by)]))
tree_idx = STRtree(major_segs)
log("segs for orientation", len(major_segs))

fill_count = 0
step = 38
gx = np.arange(X0 + step / 2, X1, step)
gy = np.arange(Y0 + step / 2, Y1, step)
GX, GY = np.meshgrid(gx, gy)
GX = GX.ravel() + rand.uniform(-step * 0.35, step * 0.35, GX.size)
GY = GY.ravel() + rand.uniform(-step * 0.35, step * 0.35, GY.size)
rr, cc = cells(GX, GY)
ok = (~water_any[rr, cc]) & (~park[rr, cc]) & (~forest[rr, cc]) & (d_road[rr, cc] > 40) & (birth[rr, cc] >= 1800) & (birth[rr, cc] < 9000)
ok &= rand.random(GX.size) < density[rr, cc] * 0.8
idx = np.nonzero(ok)[0]
log("fill candidates", len(idx))
near = tree_idx.nearest(list(Point(GX[i], GY[i]) for i in idx)) if len(idx) else []
for j, i in enumerate(idx):
    x, y = float(GX[i]), float(GY[i])
    r, c = rr[i], cc[i]
    year = float(birth[r, c]) + rand.uniform(0, 30)
    if occ_death[r, c] > year:
        continue
    okb, cap = site_free(r, c, year)
    if not okb:
        continue
    seg = major_segs[int(near[j])]
    (ax, ay), (bx, by) = seg.coords[0], seg.coords[-1]
    ang = math.atan2(by - ay, bx - ax) + rand.uniform(-0.12, 0.12)
    era = kit_for(year, r, c)
    if era in ("georgian", "medieval", "tudor"):
        era = "victorian"
    place(x, y, ang, era, year, r, c, SPACING[era] * 0.9, cap=cap)
    fill_count += 1
log("fill buildings", fill_count)

# tower clusters: explicit big towers (City, Canary Wharf, Vauxhall, ...)
for tx, ty, tr, ys, ye, th in history.TOWERS:
    n = int(np.clip(tr * tr / 14000, 5, 26))
    for _ in range(n):
        a = rand.uniform(0, 2 * math.pi); rr_ = tr * math.sqrt(rand.uniform(0.05, 1))
        x, y = tx + rr_ * math.cos(a), ty + rr_ * math.sin(a)
        r, c = cell(x, y)
        if water_perm[r, c] or blocked[r, c] or park[r, c]:
            continue
        yr = rand.uniform(ys, ye)
        k = int(rand.integers(0, 10))
        fw, fd, fh = FOOT["tower"][k]
        B["x"].append(x); B["y"].append(y); B["rot"].append(rand.uniform(0, math.pi))
        s = rand.uniform(1.0, 1.6)
        B["sx"].append(s); B["sy"].append(s); B["sz"].append(float(np.clip(rand.uniform(0.7, 1.4) * th / fh, 0.5, 4.0)))
        B["birth"].append(yr); B["death"].append(9999.0); B["era"].append(ERA_ID["tower"]); B["kit"].append(k)
        occ_death[r, c] = 9999.0
log("total buildings", len(B["x"]))

for k in B:
    B[k] = np.array(B[k], dtype=np.float32 if k not in ("era", "kit") else np.int16)
B["dur"] = np.array([dur_of(y) for y in B["birth"]], dtype=np.float32)

# ------------------------------------------------------------------ trees
built_year = np.full((NY, NX), 9999.0, dtype=np.float32)
rb, cb = cells(B["x"], B["y"])
np.minimum.at(built_year, (rb, cb), B["birth"])
built_year = ndimage.minimum_filter(built_year, size=5)
log("built_year raster")

Tr = {k: [] for k in ("x", "y", "rot", "s", "death", "kind")}
clump = np.clip(0.55 + 0.6 * smooth_noise(12, 5), 0.15, 1.0).astype(np.float32)


def scatter(step, keep, mask_fn, kinds, death_fn, jitter=0.45, clumpy=False):
    gx = np.arange(X0 + step / 2, X1, step)
    gy = np.arange(Y0 + step / 2, Y1, step)
    GX, GY = np.meshgrid(gx, gy)
    GX = GX.ravel() + rand.uniform(-step * jitter, step * jitter, GX.size)
    GY = GY.ravel() + rand.uniform(-step * jitter, step * jitter, GY.size)
    rr, cc = cells(GX, GY)
    p = keep * (clump[rr, cc] if clumpy else 1.0)
    ok = mask_fn(rr, cc) & (rand.random(GX.size) < p)
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
    d = np.minimum(d, np.where(marsh[rr, cc], marsh_year[rr, cc] - rand.uniform(0, 30, n), 9999.0))
    d = np.minimum(d, np.where(road_mask[rr, cc], road_year[rr, cc] - 3, 9999.0))
    survive = (built_year[rr, cc] >= 1880) & (rand.random(n) < 0.30) & ~inner_mask[rr, cc]
    return np.where(survive, 9999.0, d)


marsh = np.zeros((NY, NX), dtype=bool)
marsh_year = np.full((NY, NX), 9999.0, dtype=np.float32)
for poly, ceased in history.PRE_MARSHES:
    m = mask_of([poly]) & ~water_any
    marsh |= m
    marsh_year[m] = np.minimum(marsh_year[m], ceased)

# pre-urban woodland (Forest of Middlesex, Epping...): dense trees that vanish when cleared or when the city arrives
pre_forest = np.zeros((NY, NX), dtype=bool)
pre_forest_year = np.full((NY, NX), 9999.0, dtype=np.float32)
for poly, ceased in history.PRE_FORESTS:
    m = mask_of([poly]) & ~forest & ~water_any
    pre_forest |= m
    pre_forest_year[m] = np.minimum(pre_forest_year[m], ceased)
if pre_forest.any():
    n0 = scatter(24, 0.85, lambda rr, cc: pre_forest[rr, cc] & (~blocked[rr, cc]) & (d_water[rr, cc] * CELL > 12),
                 [0, 1, 3, 4, 2, 5, 0, 1],
                 lambda rr, cc, n: np.minimum(death_city(rr, cc, n), pre_forest_year[rr, cc] - rand.uniform(0, 120, n)), clumpy=False)
    log("pre-urban forest trees", n0)
n1 = scatter(32, 0.95, lambda rr, cc: (~water_any[rr, cc]) & (~forest[rr, cc]) & (~blocked[rr, cc]) & (d_water[rr, cc] * CELL > 12),
             [0, 1, 3, 4, 0, 1, 3, 4, 2], death_city, clumpy=True)
n2 = scatter(22, 0.9, lambda rr, cc: forest[rr, cc] & (~water_any[rr, cc]), [0, 1, 3, 4, 2, 5, 0, 1], lambda rr, cc, n: np.full(n, 9999.0))
n3 = scatter(24, 0.5, lambda rr, cc: park[rr, cc] & (~water_any[rr, cc]) & (~forest[rr, cc]), [0, 1, 3, 4, 0, 1], lambda rr, cc, n: np.full(n, 9999.0))
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
damp = np.clip(dw / 500.0, 0, 1) ** 1.5
hmap = np.maximum((raw + 5.0) * damp, 0.0).astype(np.float32)
log("heightmap", hmap.shape, float(hmap.max()))


def sample_h(xs, ys):
    fx = (xs - X0) / TSTEP; fy = (ys - Y0) / TSTEP
    i = np.clip(fx.astype(int), 0, hmap.shape[1] - 2); j = np.clip(fy.astype(int), 0, hmap.shape[0] - 2)
    u = fx - i; v = fy - j
    return ((1 - u) * (1 - v) * hmap[j, i] + u * (1 - v) * hmap[j, i + 1] + (1 - u) * v * hmap[j + 1, i] + u * v * hmap[j + 1, i + 1]).astype(np.float32)


B["z"] = sample_h(B["x"], B["y"])
Tr["z"] = sample_h(Tr["x"], Tr["y"])

# ------------------------------------------------------------------ rail
import rail as railmod
rail_pieces, platform_pieces, station_list = railmod.build_rail(geo, history, cell, river, water_perm, CENTER, rand, log)

# ------------------------------------------------------------------ walls
wall_pieces = []
for name, ring, b, d, h in history.WALLS:
    for i in range(len(ring) - 1):
        (ax, ay), (bx, by) = ring[i], ring[i + 1]
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(math.ceil(L / 30)))
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            x0, y0 = ax + (bx - ax) * t0, ay + (by - ay) * t0
            x1, y1 = ax + (bx - ax) * t1, ay + (by - ay) * t1
            r, c = cell((x0 + x1) / 2, (y0 + y1) / 2)
            if water_perm[r, c]:
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
        if kind in ("forest", "heath"):
            yr = -9999
        elif kind == "cemetery":
            yr = 1840 if inner_mask[r, c] else 1900
        elif kind == "golf":
            yr = 1920
        else:
            yr = 1880 if inner_mask[r, c] else 1930
    ps = p.simplify(6)
    for g in (ps.geoms if isinstance(ps, MultiPolygon) else [ps]):
        if g.area < 5000:
            continue
        parks_json.append({"kind": kind, "name": name, "birth": yr,
                           "outer": [[round(x, 1), round(y, 1)] for x, y in g.exterior.coords],
                           "holes": [[[round(x, 1), round(y, 1)] for x, y in h.coords] for h in g.interiors]})

def tri_json(poly):
    out = []
    try:
        tris = constrained_delaunay_triangles(poly)
        for t in tris.geoms:
            c = list(t.exterior.coords)[:3]
            out.append([[round(x, 1), round(y, 1)] for x, y in c])
    except Exception as ex:  # noqa
        print("[growth] triangulation failed", ex)
    return out


water_tris = []
for p, w in water_items:
    if w["kind"] != "river" and w["area"] < 15000:
        continue
    water_tris.append({"kind": w["kind"], "name": w.get("name", ""), "outer": w["outer"], "tris": tri_json(p)})
water_event_tris = []
for we in water_events_json:
    try:
        pg = Polygon(we["outer"], we.get("holes", []))
        if not pg.is_valid:
            pg = pg.buffer(0)
        parts = list(pg.geoms) if isinstance(pg, MultiPolygon) else [pg]
        tris = []
        for part in parts:
            tris += tri_json(part)
        water_event_tris.append({"name": we["name"], "birth": we["birth"], "death": we["death"], "tris": tris})
    except Exception as ex:  # noqa
        print("[growth] water event tri failed", we["name"], ex)
log("water triangulated", sum(len(w["tris"]) for w in water_tris), sum(len(w["tris"]) for w in water_event_tris))

meta = {
    "raster": {"x0": X0, "x1": X1, "y0": Y0, "y1": Y1, "cell": CELL},
    "water_tris": water_tris,
    "water_event_tris": water_event_tris,
    "terrain": {"x0": X0, "y0": Y0, "step": TSTEP, "nx": hmap.shape[1], "ny": hmap.shape[0]},
    "parks": parks_json,
    "water": geo["water"],
    "canals": geo["canals"],
    "water_events": water_events_json,
    "bridges": history.BRIDGES,
    "stations": station_list,
    "airports": geo.get("airports", {}),
    "city": [[round(x, 1), round(y, 1)] for x, y in history.CITY.exterior.coords],
    "inner": [[round(x, 1), round(y, 1)] for x, y in inner.exterior.coords],
    "london": [[round(x, 1), round(y, 1)] for x, y in london_full.simplify(30).exterior.coords] if hasattr(london_full, "exterior") else [],
    "counts": {"buildings": int(len(B["x"])), "trees": int(len(Tr["x"])), "road_pieces": int(len(road_pieces))},
    "eras": ERA_NAMES,
}
json.dump(meta, open(os.path.join(CACHE, "scene_meta.json"), "w"))

# ------------------------------------------------------------------ baked rasters for shaders (10 m)
shore_land = (255 * np.clip(1.0 - (d_water_draw * CELL - 2.0) / 9.0, 0, 1)).astype(np.uint8)   # narrower rim
d_land = ndimage.distance_transform_edt(water_perm).astype(np.float32) * CELL
water_depth = (255 * np.clip(d_land / 60.0, 0, 1)).astype(np.uint8)
park_year_img = Image.new("L", (NX, NY), 0)
kind_img = Image.new("L", (NX, NY), 0)
dp = ImageDraw.Draw(park_year_img); dk = ImageDraw.Draw(kind_img)
for pj in sorted(parks_json, key=lambda p: -Polygon(p["outer"]).area):
    yr = pj["birth"]
    enc = int(np.clip((yr + 300) / 2400 * 254 + 1, 1, 255)) if yr < 9000 else 255
    kv = {"forest": 255, "heath": 200, "park": 128, "golf": 100, "cemetery": 64}.get(pj["kind"], 128)
    dp.polygon([to_px(x, y) for x, y in pj["outer"]], fill=enc)
    dk.polygon([to_px(x, y) for x, y in pj["outer"]], fill=kv)
    for h in pj["holes"]:
        dp.polygon([to_px(x, y) for x, y in h], fill=0)
        dk.polygon([to_px(x, y) for x, y in h], fill=0)
park_year_r = np.array(park_year_img, dtype=np.uint8)
kind_r = np.array(kind_img, dtype=np.uint8)
if marsh.any():
    sel = marsh & (kind_r == 0)
    enc = np.clip((marsh_year + 300) / 2400 * 254 + 1, 1, 255).astype(np.uint8)
    park_year_r[sel] = enc[sel]
    kind_r[sel] = 30
water_dil = ndimage.binary_dilation(water_perm, iterations=1)
# water bodies that are dug / created later (docks, reservoirs, park lakes): the terrain under them stays
# almost level until they appear, and they get no sandy shore band
water_late = ndimage.binary_dilation(water_perm & (water_from < 9000), iterations=1)
np.savez_compressed(os.path.join(CACHE, "rasters.npz"), shore_land=shore_land, water_depth=water_depth,
                    park_year=park_year_r, kind=kind_r, water=water_dil, water_late=water_late, birth=birth.astype(np.float16),
                    water_until=water_until.astype(np.float16))
log("rasters saved")

np.savez_compressed(os.path.join(CACHE, "scene_data.npz"),
                    b_x=B["x"], b_y=B["y"], b_z=B["z"], b_rot=B["rot"], b_sx=B["sx"], b_sy=B["sy"], b_sz=B["sz"],
                    b_birth=B["birth"], b_death=B["death"], b_dur=B["dur"], b_era=B["era"], b_kit=B["kit"],
                    t_x=Tr["x"], t_y=Tr["y"], t_z=Tr["z"], t_rot=Tr["rot"], t_s=Tr["s"], t_death=Tr["death"], t_kind=Tr["kind"],
                    roads=road_pieces, rail=rail_pieces, platforms=platform_pieces, walls=wall_pieces, hmap=hmap)
log("saved", meta["counts"])

# QA maps
qa = np.clip((birth - (-100)) / 2150.0, 0, 1)
qa[birth >= 9000] = np.nan
img = np.zeros((NY, NX, 3), dtype=np.uint8)
img[..., 1] = 90; img[..., 0] = 70; img[..., 2] = 40
v = np.nan_to_num(qa, nan=0)
col = (np.stack([255 * (1 - v), 255 * v, 120 * (1 - v)], axis=-1)).astype(np.uint8)
img[~np.isnan(qa)] = col[~np.isnan(qa)]
img[water_perm] = (60, 120, 140)
Image.fromarray(img[::4, ::4]).save(os.path.join(CACHE, "qa_birth.png"))
img2 = np.zeros((NY, NX, 3), dtype=np.uint8); img2[...] = (110, 130, 80); img2[water_perm] = (60, 120, 140)
era_col = np.array([(200, 160, 90), (220, 60, 40), (150, 110, 60), (210, 110, 70), (180, 90, 60), (200, 190, 170), (170, 120, 100),
                    (230, 180, 150), (170, 170, 170), (220, 200, 190), (120, 120, 140), (90, 120, 170)], dtype=np.uint8)
last = B["death"] >= 9000
img2[rb[last], cb[last]] = era_col[B["era"][last]]
Image.fromarray(img2[::3, ::3]).save(os.path.join(CACHE, "qa_buildings.png"))


def snapshot(year, path):
    alive = (B["birth"] <= year) & (B["death"] > year)
    im = np.zeros((NY, NX, 3), dtype=np.uint8); im[...] = (110, 130, 80); im[water_perm] = (60, 120, 140)
    im[rb[alive], cb[alive]] = era_col[B["era"][alive]]
    Image.fromarray(im[::3, ::3]).save(path)


for yr in (120, 1000, 1300, 1600, 1700, 1800, 1850, 1900, 1939, 1975, 2025):
    snapshot(yr, os.path.join(CACHE, f"qa_{yr}.png"))
log("done")
