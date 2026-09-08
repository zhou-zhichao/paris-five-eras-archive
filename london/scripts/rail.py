"""Railway network processing (growth side): OSM tracks / platforms / stations -> dated pieces.

Piece columns: x0, y0, x1, y1, year, elev, kind, tracks
  elev : 0 at grade, 1 bridge/viaduct, 2 embankment, 3 cutting
  kind : 0 main/branch rail, 1 light rail (DLR / tram), 2 siding / yard
"""
import math
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree


def build_rail(geo, history, cell, river, water_perm, CENTER, rand, log, PIECE=60.0):
    rail2 = geo.get("rail2") or {}
    tracks = rail2.get("tracks") or []
    legacy = not tracks
    if legacy:                       # old geo.json without the detailed layer
        tracks = [{"pts": r["pts"], "bridge": r.get("bridge", False), "light": r.get("light", False), "embankment": False,
                   "cutting": False, "service": "", "tracks": 1, "name": r.get("name", "")} for r in geo["rail"]]
    lines = [(LineString(r["pts"]), r) for r in tracks if len(r["pts"]) >= 2]
    log("rail ways", len(lines), "(legacy)" if legacy else "")

    RL = [g for g, yr, nm in history.RAIL_LINES]
    rtree = STRtree(RL) if RL else None

    def researched_year(x, y):
        if rtree is None:
            return None
        pt = Point(x, y)
        best = None
        for i in rtree.query(pt.buffer(400)):
            g, yr, nm = history.RAIL_LINES[int(i)]
            if g.distance(pt) <= 400 and (best is None or yr < best):
                best = yr
        return best

    pieces = []
    way_year = []
    for ln, r in lines:
        if ln.length < 10:
            way_year.append(None); continue
        n = max(1, int(math.ceil(ln.length / PIECE)))
        pts = [ln.interpolate(i / n, normalized=True) for i in range(n + 1)]
        light = bool(r.get("light"))
        siding = r.get("service", "") in ("siding", "yard", "spur", "crossover")
        kind = 1 if light else (2 if siding else 0)
        ntr = int(r.get("tracks") or 1)
        # one year per way (from the researched line it belongs to, else distance from the centre)
        mid = ln.interpolate(0.5, normalized=True)
        d = math.hypot(mid.x - CENTER[0], mid.y - CENTER[1])
        if light:
            yr = 1987 + max(0.0, d - 5000) / 1000 * 1.5 + rand.uniform(0, 4)
        else:
            yr = min(1836 + d / 1000 * 2.2, 1905) + rand.uniform(0, 8)
            ry = researched_year(mid.x, mid.y)
            if ry is not None:
                yr = min(yr, ry + rand.uniform(0, 3))
        if siding:
            yr += rand.uniform(3, 15)
        way_year.append(yr)
        for i in range(n):
            a, b = pts[i], pts[i + 1]
            mx, my = (a.x + b.x) / 2, (a.y + b.y) / 2
            rr, cc = cell(mx, my)
            if river[rr, cc]:
                continue                                   # Thames crossings are the hand-authored bridges
            if r.get("bridge") or water_perm[rr, cc]:
                elev = 1
            elif r.get("embankment"):
                elev = 2
            elif r.get("cutting"):
                elev = 3
            else:
                elev = 0
            pieces.append((a.x, a.y, b.x, b.y, yr, elev, kind, ntr))
    pieces = np.array(pieces, dtype=np.float32) if pieces else np.zeros((0, 8), dtype=np.float32)
    log("rail pieces", len(pieces))

    # platforms: strips with the year of the nearest track
    seg_geoms = [LineString([(p[0], p[1]), (p[2], p[3])]) for p in pieces[:, :4]] if len(pieces) else []
    stree = STRtree(seg_geoms) if seg_geoms else None

    def nearest_track_year(x, y, maxd=200.0):
        if stree is None:
            return None
        pt = Point(x, y)
        idx = stree.query(pt.buffer(maxd))
        best = None
        for i in idx:
            dd = seg_geoms[int(i)].distance(pt)
            if best is None or dd < best[0]:
                best = (dd, float(pieces[int(i), 4]))
        return best[1] if best else None

    platforms = []
    for p in rail2.get("platforms") or []:
        pts = p["pts"]
        if len(pts) < 2:
            continue
        ln = LineString(pts)
        m = ln.interpolate(0.5, normalized=True)
        yr = nearest_track_year(m.x, m.y)
        if yr is None:
            continue
        for i in range(len(pts) - 1):
            platforms.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], yr + 1.0, 3.0 if p.get("closed") else 4.0))
    platforms = np.array(platforms, dtype=np.float32) if platforms else np.zeros((0, 6), dtype=np.float32)
    log("platform pieces", len(platforms))

    stations = []
    for st in rail2.get("stations") or []:
        yr = nearest_track_year(st["x"], st["y"], 300.0)
        if yr is None:
            continue
        # orientation: direction of the nearest track segment
        pt = Point(st["x"], st["y"])
        idx = stree.query(pt.buffer(300.0))
        ang = 0.0; bestd = None
        for i in idx:
            dd = seg_geoms[int(i)].distance(pt)
            if bestd is None or dd < bestd:
                bestd = dd; q = pieces[int(i)]; ang = math.atan2(q[3] - q[1], q[2] - q[0])
        stations.append({"name": st.get("name", ""), "x": st["x"], "y": st["y"], "year": float(yr) + 1.0, "angle": ang,
                         "area": st.get("area", 0), "w": st.get("w", 0), "d": st.get("d", 0)})
    log("stations", len(stations))
    return pieces, platforms, stations
