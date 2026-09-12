"""Convert raw Overpass output into clean local-metric geometry (London).

Input : london/data/osm_raw.json
Output: london/data/geo.json   (all coordinates in metres, origin St Paul's,
        x east, y north; rounded to 0.1 m)

Layers written:
  water     : list of polygons {outer, holes, name, kind(river|dock|reservoir|lake), area}
              (non-overlapping: everything is unioned per kind and docks are cut out of the river)
  canals    : list of polylines {pts, width, name}
  roads     : list of {cls, pts, bridge, tunnel, name, ref}
  rail      : list of {pts, bridge, light}
  green     : list of polygons {outer, holes, kind, name, area}
  bridges   : list of named bridge ways {name, x, y, pts}
  landmarks : list of {name, x, y, angle, w, d, area, height}
  london    : polygon (Greater London boundary), city: polygon (City of London)
  periph    : polylines (M25)
  airports  : runways {pts, name} and aerodrome polygons
"""
import json, math, os, sys
from shapely.geometry import Polygon, LineString, MultiPolygon, Point
from shapely.ops import unary_union, linemerge
from shapely import simplify as shp_simplify

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from terrain import LAT0, LON0, M_PER_DEG_LAT, M_PER_DEG_LON

RAW = os.path.join(HERE, "..", "data", "osm_raw.json")
OUT = os.path.join(HERE, "..", "data", "geo.json")


def proj(lon, lat):
    return ((lon - LON0) * M_PER_DEG_LON, (lat - LAT0) * M_PER_DEG_LAT)


def way_coords(el):
    return [proj(p["lon"], p["lat"]) for p in el.get("geometry", []) if "lon" in p]


def chain_rings(members):
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
    polys = []
    if el["type"] == "way":
        c = way_coords(el)
        if len(c) >= 4 and (c[0] == c[-1] or math.dist(c[0], c[-1]) < 1.0):
            try:
                p = Polygon(c)
                if not (p.is_valid and p.area > 0):
                    p = p.buffer(0)
                if not p.is_empty:
                    polys.append(p)
            except Exception:
                pass
    elif el["type"] == "relation":
        outers = [m for m in el.get("members", []) if m.get("role", "outer") in ("outer", "")]
        inners = [m for m in el.get("members", []) if m.get("role") == "inner"]
        holes = [Polygon(r) for r in chain_rings(inners) if len(r) >= 4]
        for r in chain_rings(outers):
            try:
                p = Polygon(r)
                if not p.is_valid:
                    p = p.buffer(0)
                for h in holes:
                    if p.contains(h.representative_point()):
                        p = p.difference(h)
                if p.area > 0:
                    polys.extend(list(p.geoms) if isinstance(p, MultiPolygon) else [p])
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


def geoms(g):
    return list(g.geoms) if hasattr(g, "geoms") else [g]


def main():
    raw = json.load(open(RAW, encoding="utf-8"))
    out = {"origin": [LON0, LAT0], "attribution": "(c) OpenStreetMap contributors, ODbL 1.0"}

    # ---- water
    river, dock, reservoir, lake, canal_lines, river_lines = [], [], [], [], [], []
    for el in raw["water"]:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        if el["type"] == "way" and tags.get("waterway") in ("canal", "river"):
            c = way_coords(el)
            if len(c) >= 2:
                if tags.get("tunnel") == "yes" or tags.get("tunnel") == "culvert":
                    continue
                w = 22.0 if tags.get("waterway") == "canal" else 12.0
                (canal_lines if tags.get("waterway") == "canal" else river_lines).append(
                    {"pts": [[round(x, 1), round(y, 1)] for x, y in c], "width": w, "name": name})
            continue
        wtype = tags.get("water", "")
        for p in element_polygons(el):
            if p.area < 1500:
                continue
            if "Thames" in name or "Lea" in name or "Lee" in name or wtype == "river" or tags.get("waterway") == "riverbank":
                river.append((p, name))
            elif wtype in ("dock", "basin", "harbour", "canal", "lock") or tags.get("waterway") == "dock" or "Dock" in name or "Basin" in name:
                dock.append((p, name))
            elif wtype == "reservoir" or tags.get("landuse") == "reservoir" or "Reservoir" in name:
                reservoir.append((p, name))
            else:
                lake.append((p, name))
    river_u = unary_union([p for p, n in river])
    dock_u = unary_union([p for p, n in dock]) if dock else Polygon()
    res_u = unary_union([p for p, n in reservoir]) if reservoir else Polygon()
    lake_u = unary_union([p for p, n in lake]) if lake else Polygon()
    # make the layers mutually exclusive so water surfaces never overlap (no z-fighting)
    dock_u = dock_u.difference(river_u.buffer(3))
    res_u = res_u.difference(river_u.buffer(3)).difference(dock_u)
    lake_u = lake_u.difference(river_u.buffer(3)).difference(dock_u).difference(res_u)
    water_json = []
    def add(u, kind, names, min_area, tol):
        for p in geoms(u):
            if p.is_empty or p.area < min_area:
                continue
            j = poly_to_json(p, tol)
            if j:
                nm = ""
                for q, n in names:
                    if n and q.intersects(p):
                        nm = n; break
                j["kind"] = kind; j["name"] = nm; j["area"] = round(p.area)
                water_json.append(j)
    add(river_u, "river", river, 3000, 1.5)
    add(dock_u, "dock", dock, 3000, 1.5)
    add(res_u, "reservoir", reservoir, 20000, 3.0)
    add(lake_u, "lake", lake, 4000, 2.0)
    out["water"] = water_json
    # canals: only outside the river/dock surfaces
    wet = unary_union([river_u, dock_u])
    canals = []
    for c in canal_lines + river_lines:
        ln = LineString(c["pts"])
        if ln.length < 30:
            continue
        rest = ln.difference(wet.buffer(c["width"] / 2 + 2))
        for g in geoms(rest):
            if isinstance(g, LineString) and g.length > 30:
                canals.append({"pts": [[round(x, 1), round(y, 1)] for x, y in shp_simplify(g, 2.0).coords], "width": c["width"], "name": c["name"]})
    out["canals"] = canals
    print("water", {k: sum(1 for w in water_json if w["kind"] == k) for k in ("river", "dock", "reservoir", "lake")}, "canals", len(canals))

    # ---- islands
    isl = []
    for el in raw.get("islands", []):
        for p in element_polygons(el):
            if p.area > 1000:
                c = p.centroid
                isl.append({"name": el.get("tags", {}).get("name", ""), "x": round(c.x, 1), "y": round(c.y, 1), "area": round(p.area)})
    out["islands"] = isl

    # ---- roads
    roads = []
    seen = set()
    for el in raw["roads_major"] + raw.get("roads_minor", []) + raw.get("roads_outer", []):
        if el["type"] != "way" or el.get("id") in seen:
            continue
        seen.add(el.get("id"))
        tags = el.get("tags", {})
        c = way_coords(el)
        if len(c) < 2:
            continue
        ln = shp_simplify(LineString(c), 2.0)
        cls = tags.get("highway", "").replace("_link", "")
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
            rail.append({"pts": [[round(x, 1), round(y, 1)] for x, y in ln.coords], "bridge": tags.get("bridge") == "yes",
                         "light": tags.get("railway") == "light_rail", "name": tags.get("name", "")})
    out["rail"] = rail
    print("rail", len(rail))

    # ---- detailed railways: every track with its attributes, platforms, stations
    tracks, platforms, stations = [], [], []
    seen_ids = set()
    for el in raw.get("rail_detail", []):
        if el.get("id") in seen_ids:
            continue
        seen_ids.add(el.get("id"))
        tags = el.get("tags", {})
        rw = tags.get("railway", "")
        if el["type"] == "node":
            if rw in ("station", "halt") and tags.get("subway") != "yes" and tags.get("station") not in ("subway", "light_rail"):
                x, y = proj(el["lon"], el["lat"])
                stations.append({"name": tags.get("name", ""), "x": round(x, 1), "y": round(y, 1), "area": 0})
            continue
        if el["type"] != "way":
            continue
        c = way_coords(el)
        if len(c) < 2:
            continue
        if rw in ("rail", "light_rail", "narrow_gauge"):
            if tags.get("tunnel") in ("yes", "building_passage") or tags.get("railway:preserved") == "yes":
                continue
            if tags.get("service") in ("crossover",) or tags.get("disused") == "yes" or tags.get("abandoned") == "yes":
                continue
            ln = shp_simplify(LineString(c), 2.0)
            try:
                ntr = int(str(tags.get("tracks", "1")).split(";")[0])
            except Exception:
                ntr = 1
            tracks.append({"pts": [[round(x, 1), round(y, 1)] for x, y in ln.coords],
                           "bridge": tags.get("bridge") in ("yes", "viaduct"), "embankment": tags.get("embankment") == "yes",
                           "cutting": tags.get("cutting") == "yes", "light": rw == "light_rail", "service": tags.get("service", ""),
                           "tracks": ntr, "name": tags.get("name", ""), "usage": tags.get("usage", "")})
        elif rw == "platform":
            closed = len(c) >= 4 and math.dist(c[0], c[-1]) < 1.0
            if closed:
                pg = Polygon(c)
                if pg.is_valid and pg.area > 0:
                    rect = pg.minimum_rotated_rectangle; rc = list(rect.exterior.coords)
                    e1 = math.dist(rc[0], rc[1]); e2 = math.dist(rc[1], rc[2])
                    if e1 >= e2:
                        a, b = rc[0], rc[1]; mid = ((rc[1][0] + rc[2][0]) / 2 - (rc[1][0] - rc[0][0]) / 2, 0)
                        p0 = ((rc[0][0] + rc[3][0]) / 2, (rc[0][1] + rc[3][1]) / 2); p1 = ((rc[1][0] + rc[2][0]) / 2, (rc[1][1] + rc[2][1]) / 2)
                    else:
                        p0 = ((rc[0][0] + rc[1][0]) / 2, (rc[0][1] + rc[1][1]) / 2); p1 = ((rc[2][0] + rc[3][0]) / 2, (rc[2][1] + rc[3][1]) / 2)
                    platforms.append({"pts": [[round(p0[0], 1), round(p0[1], 1)], [round(p1[0], 1), round(p1[1], 1)]], "closed": True})
            else:
                platforms.append({"pts": [[round(x, 1), round(y, 1)] for x, y in shp_simplify(LineString(c), 2.0).coords], "closed": False})
        elif rw == "station" or tags.get("building") == "train_station":
            polys = element_polygons(el)
            if polys:
                pg = max(polys, key=lambda q: q.area)
                cpt = pg.centroid
                rect = pg.minimum_rotated_rectangle; rc = list(rect.exterior.coords)
                e1 = math.dist(rc[0], rc[1]); e2 = math.dist(rc[1], rc[2])
                ang = math.atan2(rc[1][1] - rc[0][1], rc[1][0] - rc[0][0]) if e1 >= e2 else math.atan2(rc[2][1] - rc[1][1], rc[2][0] - rc[1][0])
                stations.append({"name": tags.get("name", ""), "x": round(cpt.x, 1), "y": round(cpt.y, 1), "area": round(pg.area),
                                 "w": round(max(e1, e2), 1), "d": round(min(e1, e2), 1), "angle": round(ang, 4)})
    out["rail2"] = {"tracks": tracks, "platforms": platforms, "stations": stations}
    print("rail2 tracks", len(tracks), "platforms", len(platforms), "stations", len(stations))

    # ---- green
    green = []
    for el in raw["green"]:
        tags = el.get("tags", {})
        if tags.get("landuse") == "forest" or tags.get("natural") == "wood":
            kind = "forest"
        elif tags.get("landuse") == "cemetery":
            kind = "cemetery"
        elif tags.get("natural") == "heath" or tags.get("leisure") in ("common", "nature_reserve"):
            kind = "heath"
        elif tags.get("leisure") == "golf_course":
            kind = "golf"
        else:
            kind = "park"
        for p in element_polygons(el):
            if p.area >= (15000 if kind == "park" else 30000):
                j = poly_to_json(p, 3.0)
                if j:
                    j["kind"] = kind; j["name"] = tags.get("name", ""); j["area"] = round(p.area)
                    green.append(j)
    out["green"] = green
    print("green", len(green))

    # ---- admin / periph / airports
    london = city = None
    periph, runways, aerodromes = [], [], []
    for el in raw.get("admin", []):
        tags = el.get("tags", {})
        if el["type"] == "relation" and tags.get("boundary") == "administrative":
            polys = element_polygons(el)
            if not polys:
                continue
            cand = max(polys, key=lambda p: p.area)
            if tags.get("name") == "Greater London":
                london = cand
            elif tags.get("name") == "City of London":
                city = cand
        elif tags.get("aeroway") == "runway":
            c = way_coords(el)
            if len(c) >= 2:
                runways.append({"pts": [[round(x, 1), round(y, 1)] for x, y in c], "name": tags.get("name", ""), "ref": tags.get("ref", "")})
        elif tags.get("aeroway") == "aerodrome":
            for p in element_polygons(el):
                if p.area > 200000:
                    j = poly_to_json(p, 10.0)
                    if j:
                        j["name"] = tags.get("name", ""); aerodromes.append(j)
        elif tags.get("highway") == "motorway":
            c = way_coords(el)
            if len(c) >= 2:
                periph.append([[round(x, 1), round(y, 1)] for x, y in shp_simplify(LineString(c), 5.0).coords])
    if london is not None:
        out["london"] = poly_to_json(london, 8.0)
        print("Greater London area km2", round(london.area / 1e6, 1))
    if city is not None:
        out["city"] = poly_to_json(city, 4.0)
        print("City area km2", round(city.area / 1e6, 2))
    out["periph"] = periph
    out["airports"] = {"runways": runways, "aerodromes": aerodromes}
    print("M25 ways", len(periph), "runways", len(runways), "aerodromes", len(aerodromes))

    # ---- bridges (named bridge ways: for matching hand-authored Thames bridges)
    bridges = []
    for el in raw.get("bridges", []):
        tags = el.get("tags", {})
        c = way_coords(el)
        if len(c) < 2:
            continue
        ln = LineString(c)
        m = ln.interpolate(0.5, normalized=True)
        bridges.append({"name": tags.get("name", ""), "x": round(m.x, 1), "y": round(m.y, 1), "length": round(ln.length, 1),
                        "pts": [[round(x, 1), round(y, 1)] for x, y in c], "rail": tags.get("railway") is not None,
                        "cls": tags.get("highway", tags.get("railway", ""))})
    out["bridges"] = bridges
    print("bridge ways", len(bridges))

    # ---- landmarks
    lm = []
    for el in raw.get("landmarks", []):
        tags = el.get("tags", {})
        polys = element_polygons(el)
        if not polys:
            if el["type"] == "way" and tags.get("historic") in ("citywalls", "city_gate"):
                c = way_coords(el)
                if c:
                    lm.append({"name": tags.get("name", tags.get("historic")), "kind": tags.get("historic"),
                               "pts": [[round(x, 1), round(y, 1)] for x, y in c]})
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
                   "w": round(w, 1), "d": round(d, 1), "area": round(p.area), "height": tags.get("height", ""),
                   "levels": tags.get("building:levels", "")})
    out["landmarks"] = lm
    print("landmarks", len(lm))
    for l in sorted([l for l in lm if "area" in l], key=lambda l: -l["area"])[:80]:
        print("   ", l["name"], l["x"], l["y"], l["w"], l["d"], l["height"])

    json.dump(out, open(OUT, "w", encoding="utf-8"))
    print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
