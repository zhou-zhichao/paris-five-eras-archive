"""Stylised relief of the London basin (pure numpy, shared by growth.py and Blender).

Coordinates: metres, origin St Paul's Cathedral, x east, y north.
The Thames floodplain sits low; the gravel terraces rise gently to the north and
south; the named hills are Gaussian blobs (height above the terrace).
"""
import math
import numpy as np

LAT0, LON0 = 51.51385, -0.09840
M_PER_DEG_LAT = 111320.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(LAT0))


def ll(lon, lat):
    """lon/lat -> local metres."""
    return ((lon - LON0) * M_PER_DEG_LON, (lat - LAT0) * M_PER_DEG_LAT)


# (lon, lat, sigma, height)  - height above the general terrace level
HILLS_LL = [
    (-0.1655, 51.5605, 900, 105),    # Hampstead Heath / Parliament Hill (134 m)
    (-0.1480, 51.5710, 700, 100),    # Highgate
    (-0.1600, 51.5390, 300, 40),     # Primrose Hill (63 m)
    (-0.1300, 51.5940, 900, 75),     # Muswell Hill / Alexandra Palace
    (-0.3360, 51.5730, 600, 95),     # Harrow on the Hill (124 m)
    (0.0580, 51.4690, 900, 105),     # Shooter's Hill (132 m)
    (-0.0010, 51.4770, 400, 35),     # Greenwich Park
    (0.0080, 51.4670, 1200, 35),     # Blackheath plateau
    (-0.0750, 51.4210, 1100, 90),    # Sydenham Hill / Crystal Palace (110 m)
    (-0.0500, 51.4400, 800, 55),     # Forest Hill / Honor Oak
    (-0.1100, 51.4500, 1300, 40),    # Denmark / Herne / Tulse / Streatham hills
    (-0.2300, 51.4400, 1500, 45),    # Wimbledon / Putney Heath
    (-0.3000, 51.4500, 700, 40),     # Richmond Hill
    (-0.0984, 51.5138, 500, 10),     # Ludgate Hill / Cornhill (the twin hills of the City)
    (-0.0700, 51.5700, 900, 35),     # Stamford Hill
    (0.0300, 51.6300, 2500, 80),     # Epping Forest ridge
    (0.2000, 51.6000, 2500, 70),     # Havering ridge
    (0.0600, 51.4100, 2000, 80),     # Chislehurst / Bromley ridge
    (-0.0300, 51.3600, 2000, 110),   # Addington Hills
    (-0.1900, 51.6400, 3000, 110),   # Barnet / Totteridge plateau
    (-0.2300, 51.6100, 1500, 80),    # Mill Hill
    (-0.3200, 51.5500, 800, 50),     # Horsenden Hill
    (-0.1000, 51.3800, 2500, 60),    # Croydon / Norbury slopes
    (0.1200, 51.5800, 2500, 50),     # Hainault / Chigwell
]
HILLS = [(*ll(lon, lat), s, h) for lon, lat, s, h in HILLS_LL]

# researched relief (data/history/landscape_history.json) replaces the hand list when present
import json, os
_lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "history", "landscape_history.json")
if os.path.exists(_lp):
    try:
        _L = json.load(open(_lp, encoding="utf-8"))
        _r = [(*ll(t["lon"], t["lat"]), float(t["sigma_m"]), float(t["height_m"])) for t in _L.get("terrain", [])
              if t.get("sigma_m") and t.get("height_m") and float(t["height_m"]) > 0]
        if len(_r) >= 10:
            HILLS = _r
    except Exception as e:  # noqa
        print("[terrain] landscape_history unreadable", e)


def height(x, y):
    """Raw relief height (metres) before water damping."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.zeros(np.broadcast(x, y).shape, dtype=np.float64)
    # soft-max blend of the blobs (adjacent ridge entries overlap; summing them over-shoots)
    acc = np.zeros_like(z)
    for hx, hy, s, h in HILLS:
        b = h * np.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * s * s))
        acc = np.maximum(acc, b) + 0.25 * np.minimum(acc, b)
    z += acc
    # terrace: the basin rises slowly away from the river (north and south)
    z += 6.0 * np.clip(np.abs(y) / 6000.0, 0, 2.5)
    # gentle rolling noise
    z += 3.5 * np.sin(x / 2100.0 + 0.3) * np.cos(y / 1700.0 - 0.7)
    z += 2.5 * np.sin(x / 800.0 - 1.1) * np.sin(y / 950.0 + 0.4)
    z += 1.5 * np.cos(x / 350.0 + y / 420.0)
    return z
