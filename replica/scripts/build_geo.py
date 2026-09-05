"""Convert raw Overpass output into clean local-metric geometry.

Input : replica/data/osm_raw.json
Output: replica/data/geo.json   (all coordinates in metres, origin Notre-Dame,
        x east, y north; rounded to 0.1 m)

Layers written:
  water     : list of polygons {outer:[[x,y]..], holes:[[..]..], name, kind}
  canals    : list of polylines {pts, width}
  roads     : list of {cls, pts, bridge, name, ref}
  rail      : list of {pts}
  green     : list of polygons {outer, holes, kind, name}
  landmarks : list of {name, x, y, angle, w, d, area}
  paris     : polygon (commune boundary)
  periph    : polylines
"""
import json, math, os, sys
from shapely.geometry import Polygon, LineString, MultiPolygon, Point
from shapely.ops import unary_union, linemerge, polygonize
from shapely import simplify as shp_simplify

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "osm_raw.json")
OUT = os.path.join(HERE, "..", "data", "geo.json")

LAT0, LON0 = 48.852968, 2.349902
M_PER_DEG_LAT = 111320.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(LAT0))


def proj(lon, lat):
    return ((lon - LON0) * M_PER_DEG_LON, (lat - LAT0) * M_PER_DEG_LAT)


def way_coords(el):
    return [proj(p["lon"], p["lat"]) for p in el.get("geometry", []) if "lon" in p]


def chain_rings(members):
    """Join relation member ways (with geometry) into closed rings."""
    segs = []
    for m in members:
        if m.get("type") != "way" or "geometry" not in m:
            continue
        pts = [proj(p["lon"], p["lat"]) for p in m["geometry"] if "lon" in p]
        if len(pts) >= 2:
            segs.append(LineString(pts))
    if not segs:
        return []
    merged = linemerge(segs)
    lines = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
    rings = []
    for ln in lines:
        c = list(ln.coords)
        if len(c) >= 4 and (abs(c[0][0] - c[-1][0]) < 1.0 and abs(c[0][1] - c[-1][1]) < 1.0):
            rings.append(c)
    return rings


def element_polygons(el):
    """Return list of shapely Polygons for a way/relation element."""
    polys = []
    if el["type"] == "way":
        c = way_coords(el)
        if len(c) >= 4 and c[0] == c[-1] or (len(c) >= 4 and math.dist(c[0], c[-1]) < 1.0):
            try:
                p = Polygon(c)
                if p.is_valid and p.area > 0:
                    polys.append(p)
                else:
                    polys.append(p.buffer(0))
            except Exception:
                pass
    elif el["type"] == "relation":
        outers = [m for m in el.get("members", []) if m.get("role", "outer") in ("outer", "")]
        inners = [m for m in el.get("members", []) if m.get("role") == "inner"]
        outer_rings = chain_rings(outers)
        inner_rings = chain_rings(inners)
        holes = [Polygon(r) for r in inner_rings if len(r) >= 4]
        for r in outer_rings:
            try:
                p = Polygon(r)
                if not p.is_valid:
                    p = p.buffer(0)
                for h in holes:
                    if p.contains(h.representative_point()):
                        p = p.difference(h)
                if p.area > 0:
                    if isinstance(p, MultiPolygon):
                        polys.extend(list(p.geoms))
                    else:
                        polys.append(p)
            except Exception:
                pass
    return polys


def poly_to_json(p, tol=2.0):
    p = shp_simplify(p, tol, preserve_topology=True)
    if p.is_empty:
        return None
    if isinstance(p, MultiPolygon):
        p = max(p.geoms, key=lambda g: g.area)
    return {
        "outer": [[round(x, 1), round(y, 1)] for x, y in p.exterior.coords],
        "holes": [[[round(x, 1), round(y, 1)] for x, y in h.coords] for h in p.interiors if Polygon(h).area > 400],
    }


def main():
    raw = json.load(open(RAW, encoding="utf-8"))
    out = {"origin": [LON0, LAT0], "attribution": "(c) OpenStreetMap contributors, ODbL 1.0"}

    # ---- water
    water_polys, canal_lines = [], []
    for el in raw["water"]:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        if el["type"] == "way" and tags.get("waterway") == "canal":
            c = way_coords(el)
            if len(c) >= 2:
                canal_lines.append({"pts": [[round(x, 1), round(y, 1)] for x, y in c], "width": 25.0, "name": name})
            continue
        for p in element_polygons(el):
            if p.area >= 2500:
                kind = "river" if ("Seine" in name or "Marne" in name or tags.get("water") == "river") else tags.get("water", "water")
                water_polys.append((p, name, kind))
    # union the river bodies so the Seine is one clean multipolygon
    river = unary_union([p for p, n, k in water_polys if k == "river"])
    river_polys = list(river.geoms) if isinstance(river, MultiPolygon) else [river]
    water_json = []
    for p in river_polys:
        j = poly_to_json(p, 1.5)
        if j:
            j["kind"] = "river"; j["name"] = "Seine"; j["area"] = round(p.area)
            water_json.append(j)
    for p, n, k in water_polys:
        if k != "river" and p.area >= 4000:
            j = poly_to_json(p, 1.5)
            if j:
                j["kind"] = k; j["name"] = n; j["area"] = round(p.area)
                water_json.append(j)
    out["water"] = water_json
    out["canals"] = canal_lines
    print("water polys", len(water_json), "river parts", len(river_polys), "canals", len(canal_lines))

    # ---- islands (only names/centroids, holes come from the river polygon)
    isl = []
    for el in raw.get("islands", []):
        for p in element_polygons(el):
            if p.area > 1000:
                c = p.centroid
                isl.append({"name": el.get("tags", {}).get("name", ""), "x": round(c.x, 1), "y": round(c.y, 1), "area": round(p.area)})
    out["islands"] = isl

    # ---- roads
    roads = []
    for el in raw["roads_major"] + raw["roads_minor"]:
        if el["type"] != "way":
            continue
        tags = el.get("tags", {})
        c = way_coords(el)
        if len(c) < 2:
            continue
        ln = shp_simplify(LineString(c), 2.0)
        cls = tags.get("highway", "")
        cls = cls.replace("_link", "")
        roads.append({
            "cls": cls,
            "pts": [[round(x, 1), round(y, 1)] for x, y in ln.coords],
            "bridge": tags.get("bridge") in ("yes", "viaduct"),
            "tunnel": tags.get("tunnel") in ("yes",),
            "name": tags.get("name", ""),
            "ref": tags.get("ref", ""),
        })
    out["roads"] = roads
    print("roads", len(roads))

    # ---- rail
    rail = []
    for el in raw["rail"]:
        if el["type"] != "way":
            continue
        tags = el.get("tags", {})
        if tags.get("tunnel") == "yes" or tags.get("service"):
            continue
        c = way_coords(el)
        if len(c) >= 2:
            ln = shp_simplify(LineString(c), 3.0)
            rail.append({"pts": [[round(x, 1), round(y, 1)] for x, y in ln.coords], "bridge": tags.get("bridge") == "yes"})
    out["rail"] = rail
    print("rail", len(rail))

    # ---- green
    green = []
    for el in raw["green"]:
        tags = el.get("tags", {})
        kind = "forest" if (tags.get("landuse") == "forest" or tags.get("natural") == "wood") else (
            "cemetery" if tags.get("landuse") == "cemetery" else "park")
        for p in element_polygons(el):
            if p.area >= (15000 if kind == "park" else 30000):
                j = poly_to_json(p, 3.0)
                if j:
                    j["kind"] = kind; j["name"] = tags.get("name", ""); j["area"] = round(p.area)
                    green.append(j)
    out["green"] = green
    print("green", len(green))

    # ---- admin / periph
    paris = None
    periph = []
    for el in raw.get("admin", []):
        tags = el.get("tags", {})
        if el["type"] == "relation":
            polys = [p for p in element_polygons(el) if abs(p.centroid.x) < 20000 and abs(p.centroid.y) < 20000]
            if polys:
                cand = max(polys, key=lambda p: p.area)
                if paris is None or cand.area > paris.area:
                    paris = cand
        elif el["type"] == "way":
            c = way_coords(el)
            if len(c) >= 2:
                periph.append([[round(x, 1), round(y, 1)] for x, y in shp_simplify(LineString(c), 3.0).coords])
    if paris is not None:
        out["paris"] = poly_to_json(paris, 5.0)
        print("paris area km2", round(paris.area / 1e6, 1))
    out["periph"] = periph
    print("periph ways", len(periph))

    # ---- landmarks
    lm = []
    for el in raw.get("landmarks", []):
        tags = el.get("tags", {})
        polys = element_polygons(el)
        if not polys:
            continue
        p = max(polys, key=lambda q: q.area)
        rect = p.minimum_rotated_rectangle
        rc = list(rect.exterior.coords)
        e1 = math.dist(rc[0], rc[1]); e2 = math.dist(rc[1], rc[2])
        if e1 >= e2:
            ang = math.atan2(rc[1][1] - rc[0][1], rc[1][0] - rc[0][0]); w, d = e1, e2
        else:
            ang = math.atan2(rc[2][1] - rc[1][1], rc[2][0] - rc[1][0]); w, d = e2, e1
        c = p.centroid
        lm.append({"name": tags.get("name", ""), "x": round(c.x, 1), "y": round(c.y, 1), "angle": round(ang, 4),
                   "w": round(w, 1), "d": round(d, 1), "area": round(p.area), "height": tags.get("height", "")})
    out["landmarks"] = lm
    print("landmarks", len(lm))
    for l in sorted(lm, key=lambda l: -l["area"])[:60]:
        print("   ", l["name"], l["x"], l["y"], l["w"], l["d"], l["height"])

    json.dump(out, open(OUT, "w", encoding="utf-8"))
    print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
