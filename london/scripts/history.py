"""Hand-authored + researched historical geography of London.

Coordinates: metres, origin St Paul's, x east, y north (converted from lon/lat).
Researched datasets (data/history/*.json, produced from web research) are loaded
when present; the hand-authored fallbacks below keep the pipeline runnable.

Exports used by growth.py / build_scene.py:
  INNER (shapely Polygon: County of London 1889, the dense core), CENTER, ROMAN_GRID,
  ZONES, VILLAGES, EVENTS, ESTATES, TOWERS, WALLS, PARK_YEARS, ROAD_YEARS,
  BRIDGES, WATER_EVENTS, LANDMARKS
"""
import json, math, os
try:
    from shapely.geometry import Polygon, LineString, Point
    HAVE_SHAPELY = True
except ImportError:          # inside Blender only the landmark / bridge tables are needed
    HAVE_SHAPELY = False
    class _Stub:
        def __init__(self, *a, **k): pass
        def buffer(self, *a, **k): return self
        area = 0.0
    Polygon = LineString = Point = _Stub

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "..", "data", "history")
from terrain import ll, LAT0, LON0


def P(coords):
    """lon/lat vertex list -> metre vertex list."""
    return [ll(lon, lat) for lon, lat in coords]


def load(name):
    p = os.path.join(HIST, name)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception as e:  # noqa
            print("[history] failed to read", name, e)
    return None


# ------------------------------------------------------------------ core geometry
CENTER = ll(-0.0870, 51.5125)          # Cornhill / forum: the Roman heart of the city
# County of London (1889) - the dense continuous city; density 1 inside, decaying outside
INNER = Polygon(P([(-0.245, 51.490), (-0.225, 51.465), (-0.200, 51.440), (-0.150, 51.415), (-0.100, 51.410),
                   (-0.045, 51.420), (0.020, 51.440), (0.075, 51.470), (0.105, 51.495), (0.090, 51.515),
                   (0.010, 51.545), (-0.040, 51.578), (-0.090, 51.578), (-0.150, 51.575), (-0.195, 51.565),
                   (-0.215, 51.540), (-0.235, 51.512)]))
# Roman street grid: origin at the forum, cardo bearing (deg clockwise from north), block size (m)
ROMAN_GRID = {"origin": ll(-0.0855, 51.5128), "bearing": 8.0, "block": 110.0}

# the walled Roman / medieval city
CITY_WALL_LL = [(-0.0755, 51.5085), (-0.0755, 51.5120), (-0.0762, 51.5140), (-0.0790, 51.5170), (-0.0815, 51.5176),
                (-0.0885, 51.5182), (-0.0935, 51.5186), (-0.0947, 51.5180), (-0.0975, 51.5170), (-0.1010, 51.5156),
                (-0.1030, 51.5140), (-0.1042, 51.5115)]
CITY_LL = CITY_WALL_LL + [(-0.1000, 51.5100), (-0.0900, 51.5080), (-0.0820, 51.5078), (-0.0760, 51.5080)]
CITY = Polygon(P(CITY_LL))

# ------------------------------------------------------------------ growth zones
# name, polygon (lon/lat) | shapely | special, year_start, year_end, kit
# kits: celtic roman saxon medieval tudor georgian victorian interwar postwar modern estate tower
ZONES_LL = [
    ("londinium_bridgehead", [(-0.0920, 51.5100), (-0.0830, 51.5100), (-0.0820, 51.5145), (-0.0910, 51.5148)], 47, 60, "roman"),
    ("londinium_peak", "CITY", 62, 160, "roman"),
    ("southwark_roman", [(-0.0935, 51.5060), (-0.0850, 51.5062), (-0.0845, 51.5000), (-0.0940, 51.5005)], 55, 160, "roman"),
    ("roman_west_suburb", [(-0.1042, 51.5115), (-0.1042, 51.5150), (-0.1090, 51.5160), (-0.1100, 51.5120)], 120, 220, "roman"),
    ("lundenwic", [(-0.1285, 51.5085), (-0.1140, 51.5100), (-0.1115, 51.5140), (-0.1170, 51.5175), (-0.1300, 51.5140)], 600, 820, "saxon"),
    ("westminster_thorney", [(-0.1310, 51.4970), (-0.1240, 51.4975), (-0.1235, 51.5015), (-0.1300, 51.5015)], 960, 1100, "saxon"),
    ("lundenburg", "CITY", 886, 1120, "saxon"),
    ("southwark_saxon", [(-0.0935, 51.5060), (-0.0850, 51.5062), (-0.0845, 51.5000), (-0.0940, 51.5005)], 900, 1150, "saxon"),
    ("medieval_city", "CITY", 1100, 1260, "medieval"),
    ("medieval_suburbs", [(-0.1150, 51.5130), (-0.1100, 51.5195), (-0.1000, 51.5210), (-0.0930, 51.5225), (-0.0790, 51.5240),
                          (-0.0700, 51.5190), (-0.0690, 51.5140), (-0.0740, 51.5085), (-0.0760, 51.5075), (-0.1050, 51.5105)],
     1150, 1340, "medieval"),
    ("southwark_medieval", [(-0.1000, 51.5075), (-0.0800, 51.5065), (-0.0790, 51.5000), (-0.0900, 51.4970), (-0.1010, 51.4990)], 1100, 1350, "medieval"),
    ("strand_ribbon", [(-0.1290, 51.5065), (-0.1050, 51.5105), (-0.1050, 51.5150), (-0.1280, 51.5120)], 1200, 1420, "medieval"),
    ("westminster_medieval", [(-0.1360, 51.4960), (-0.1220, 51.4960), (-0.1215, 51.5085), (-0.1300, 51.5085), (-0.1340, 51.5010)], 1250, 1500, "medieval"),
    ("tudor", [(-0.1370, 51.4960), (-0.1400, 51.5060), (-0.1300, 51.5100), (-0.1290, 51.5160), (-0.1150, 51.5200), (-0.1080, 51.5245),
               (-0.0950, 51.5245), (-0.0790, 51.5270), (-0.0710, 51.5215), (-0.0610, 51.5165), (-0.0650, 51.5085), (-0.0790, 51.5065),
               (-0.0790, 51.4995), (-0.0960, 51.4960), (-0.1030, 51.4975), (-0.1080, 51.5060), (-0.1200, 51.4990), (-0.1220, 51.4950)],
     1520, 1610, "tudor"),
    ("stuart", [(-0.1420, 51.4950), (-0.1470, 51.5090), (-0.1350, 51.5150), (-0.1300, 51.5210), (-0.1160, 51.5240), (-0.1050, 51.5290),
                (-0.0880, 51.5290), (-0.0750, 51.5310), (-0.0620, 51.5240), (-0.0500, 51.5200), (-0.0370, 51.5150), (-0.0420, 51.5070),
                (-0.0560, 51.5040), (-0.0700, 51.5000), (-0.0740, 51.4930), (-0.0960, 51.4900), (-0.1100, 51.4930), (-0.1200, 51.4900)],
     1600, 1690, "tudor"),
    ("restoration", [(-0.1500, 51.4950), (-0.1560, 51.5090), (-0.1450, 51.5170), (-0.1350, 51.5240), (-0.1150, 51.5290), (-0.1000, 51.5330),
                     (-0.0800, 51.5340), (-0.0600, 51.5290), (-0.0450, 51.5240), (-0.0300, 51.5150), (-0.0380, 51.5060), (-0.0500, 51.4980),
                     (-0.0700, 51.4900), (-0.1000, 51.4860), (-0.1200, 51.4870)], 1670, 1720, "georgian"),
    ("georgian_early", [(-0.1600, 51.4900), (-0.1660, 51.5130), (-0.1550, 51.5230), (-0.1400, 51.5290), (-0.1200, 51.5330), (-0.1000, 51.5380),
                        (-0.0750, 51.5380), (-0.0500, 51.5330), (-0.0300, 51.5250), (-0.0200, 51.5150), (-0.0300, 51.5050), (-0.0450, 51.4950),
                        (-0.0650, 51.4860), (-0.1000, 51.4820), (-0.1250, 51.4820), (-0.1450, 51.4850)], 1710, 1770, "georgian"),
    ("georgian_late", [(-0.1720, 51.4880), (-0.1780, 51.5150), (-0.1650, 51.5280), (-0.1450, 51.5360), (-0.1200, 51.5420), (-0.0950, 51.5440),
                       (-0.0650, 51.5430), (-0.0400, 51.5360), (-0.0150, 51.5280), (-0.0100, 51.5120), (-0.0250, 51.4980), (-0.0450, 51.4880),
                       (-0.0700, 51.4800), (-0.1050, 51.4760), (-0.1350, 51.4770), (-0.1600, 51.4820)], 1760, 1815, "georgian"),
    ("regency", [(-0.1850, 51.4850), (-0.1950, 51.5150), (-0.1800, 51.5330), (-0.1550, 51.5420), (-0.1300, 51.5480), (-0.1000, 51.5500),
                 (-0.0650, 51.5480), (-0.0350, 51.5420), (-0.0050, 51.5320), (0.0000, 51.5100), (-0.0200, 51.4900), (-0.0400, 51.4820),
                 (-0.0750, 51.4720), (-0.1100, 51.4680), (-0.1450, 51.4700), (-0.1700, 51.4760)], 1805, 1850, "georgian"),
    ("victorian_a", [(-0.2150, 51.4780), (-0.2250, 51.5100), (-0.2100, 51.5350), (-0.1800, 51.5480), (-0.1450, 51.5580), (-0.1100, 51.5640),
                     (-0.0700, 51.5620), (-0.0300, 51.5560), (0.0100, 51.5430), (0.0250, 51.5200), (0.0100, 51.4950), (-0.0150, 51.4780),
                     (-0.0450, 51.4650), (-0.0850, 51.4560), (-0.1300, 51.4540), (-0.1700, 51.4600), (-0.2000, 51.4680)], 1840, 1875, "victorian"),
    ("victorian_b", [(-0.2450, 51.4700), (-0.2500, 51.5050), (-0.2400, 51.5400), (-0.2050, 51.5600), (-0.1600, 51.5720), (-0.1150, 51.5780),
                     (-0.0700, 51.5780), (-0.0250, 51.5720), (0.0250, 51.5600), (0.0550, 51.5350), (0.0500, 51.5050), (0.0250, 51.4800),
                     (-0.0050, 51.4600), (-0.0450, 51.4450), (-0.0900, 51.4370), (-0.1400, 51.4370), (-0.1850, 51.4450), (-0.2200, 51.4550)],
     1865, 1905, "victorian"),
    ("croydon_town", [(-0.1100, 51.3650), (-0.0950, 51.3650), (-0.0930, 51.3800), (-0.1100, 51.3820)], 1840, 1900, "victorian"),
    ("kingston_town", [(-0.3150, 51.4050), (-0.2950, 51.4050), (-0.2950, 51.4200), (-0.3150, 51.4200)], 1840, 1900, "victorian"),
    ("richmond_town", [(-0.3150, 51.4530), (-0.2950, 51.4540), (-0.2950, 51.4680), (-0.3150, 51.4660)], 1840, 1900, "victorian"),
    ("woolwich_town", [(0.0550, 51.4850), (0.0850, 51.4850), (0.0850, 51.4980), (0.0550, 51.4980)], 1830, 1890, "victorian"),
    ("edwardian", [(-0.2750, 51.4650), (-0.2800, 51.5050), (-0.2650, 51.5500), (-0.2300, 51.5750), (-0.1800, 51.5900), (-0.1200, 51.5950),
                   (-0.0600, 51.5950), (0.0000, 51.5900), (0.0500, 51.5750), (0.0850, 51.5500), (0.0800, 51.5100), (0.0600, 51.4700),
                   (0.0250, 51.4450), (-0.0200, 51.4300), (-0.0800, 51.4200), (-0.1400, 51.4200), (-0.1900, 51.4250), (-0.2350, 51.4400)],
     1895, 1920, "victorian"),
    ("interwar", [(-0.4000, 51.4450), (-0.4100, 51.5050), (-0.3800, 51.5450), (-0.3700, 51.5900), (-0.3000, 51.6150), (-0.2200, 51.6350),
                  (-0.1200, 51.6450), (-0.0200, 51.6300), (0.0350, 51.6100), (0.1400, 51.5900), (0.2300, 51.5700), (0.1800, 51.5250),
                  (0.1500, 51.4500), (0.1000, 51.4150), (0.0800, 51.3800), (-0.0100, 51.3950), (-0.0800, 51.3550), (-0.1900, 51.3550),
                  (-0.2900, 51.3800), (-0.3300, 51.4150), (-0.3700, 51.4250)], 1915, 1942, "interwar"),
    ("postwar_fringe", ("INTERWAR_BUFFER", 1200), 1948, 1975, "interwar"),
    ("docklands", [(-0.0450, 51.5120), (0.0000, 51.5150), (0.0700, 51.5100), (0.0750, 51.4980), (0.0050, 51.4880), (-0.0250, 51.4900),
                   (-0.0600, 51.4950)], 1985, 2010, "modern"),
    ("olympic_park", [(-0.0250, 51.5350), (0.0000, 51.5340), (0.0020, 51.5480), (-0.0200, 51.5500)], 2008, 2014, "modern"),
]

# village nuclei fallback (name, lon, lat, r, ys, ye) - replaced by data/history/villages.json when present
VILLAGES_LL = [
    ("Westminster", -0.1273, 51.4993, 400, 960, 1300), ("Southwark", -0.0910, 51.5040, 400, 50, 1300),
    ("Islington", -0.1030, 51.5386, 250, 1005, 1800), ("Hackney", -0.0555, 51.5480, 250, 1198, 1850),
    ("Stepney", -0.0430, 51.5180, 250, 1000, 1700), ("Chelsea", -0.1712, 51.4830, 250, 785, 1800),
    ("Kensington", -0.1920, 51.5010, 250, 1086, 1830), ("Greenwich", -0.0093, 51.4816, 350, 918, 1800),
    ("Deptford", -0.0271, 51.4854, 300, 1086, 1800), ("Hampstead", -0.1780, 51.5560, 250, 986, 1850),
    ("Highgate", -0.1470, 51.5710, 220, 1350, 1850), ("Camberwell", -0.0895, 51.4740, 250, 1086, 1820),
    ("Clapham", -0.1390, 51.4630, 250, 880, 1830), ("Battersea", -0.1795, 51.4718, 250, 693, 1850),
    ("Fulham", -0.2140, 51.4700, 250, 691, 1850), ("Putney", -0.2166, 51.4671, 220, 1086, 1850),
    ("Hammersmith", -0.2250, 51.4930, 250, 1294, 1850), ("Chiswick", -0.2560, 51.4870, 220, 1000, 1880),
    ("Brentford", -0.3090, 51.4870, 350, 700, 1850), ("Kingston", -0.3050, 51.4120, 400, 838, 1800),
    ("Croydon", -0.1027, 51.3722, 450, 809, 1800), ("Barking", 0.0808, 51.5348, 350, 666, 1850),
    ("Woolwich", 0.0690, 51.4900, 350, 918, 1800), ("Stratford", 0.0020, 51.5410, 250, 1135, 1850),
    ("Tottenham", -0.0715, 51.5985, 250, 1086, 1880), ("Harrow", -0.3355, 51.5723, 250, 767, 1900),
    ("Ealing", -0.3020, 51.5090, 250, 700, 1880), ("Enfield", -0.0810, 51.6520, 300, 1086, 1880),
    ("Romford", 0.1830, 51.5757, 350, 1177, 1900), ("Bromley", -0.0170, 51.4060, 350, 862, 1900),
    ("Lewisham", -0.0139, 51.4553, 250, 862, 1850), ("Wandsworth", -0.1900, 51.4570, 250, 1086, 1850),
    ("Richmond", -0.3070, 51.4610, 300, 1086, 1850), ("Twickenham", -0.3262, 51.4463, 250, 704, 1900),
    ("Hounslow", -0.3620, 51.4700, 300, 1217, 1900), ("Uxbridge", -0.4780, 51.5460, 300, 1200, 1900),
    ("Hendon", -0.2320, 51.5836, 220, 959, 1900), ("Edmonton", -0.0670, 51.6180, 250, 1086, 1880),
    ("Walthamstow", -0.0165, 51.5855, 250, 1086, 1880), ("Ilford", 0.0700, 51.5590, 250, 1086, 1890),
    ("Wimbledon", -0.2180, 51.4335, 250, 967, 1880), ("Streatham", -0.1290, 51.4285, 220, 1086, 1880),
    ("Eltham", 0.0520, 51.4500, 250, 1086, 1900), ("Bexley", 0.1490, 51.4410, 220, 814, 1900),
    ("Sutton", -0.1940, 51.3610, 250, 1086, 1900), ("Mitcham", -0.1660, 51.3990, 250, 1086, 1900),
    ("Barnet", -0.2000, 51.6520, 300, 1070, 1900), ("Dagenham", 0.1650, 51.5420, 220, 692, 1920),
]

# ------------------------------------------------------------------ destruction / rebuild events
# polygon (lon/lat), year, fraction of buildings destroyed, rebuild (start,end,kit) or None,
# resettle (start,end) = the site stays empty and is re-founded later
EVENTS_LL = [
    {"name": "boudica", "poly": [(-0.0960, 51.4980), (-0.0700, 51.4980), (-0.0700, 51.5180), (-0.1120, 51.5180)],
     "year": 60, "fraction": 1.0, "rebuild": (63, 95, "roman"), "resettle": None},
    {"name": "roman_abandonment", "poly": "CITY_BUF", "year": 420, "fraction": 1.0, "rebuild": None, "resettle": (886, 1050)},
    {"name": "lundenwic_abandoned", "poly": [(-0.1310, 51.5070), (-0.1120, 51.5090), (-0.1100, 51.5185), (-0.1330, 51.5150)],
     "year": 880, "fraction": 1.0, "rebuild": None, "resettle": (1180, 1400)},
    {"name": "great_fire", "poly": [(-0.0770, 51.5085), (-0.0810, 51.5135), (-0.0850, 51.5165), (-0.0920, 51.5185), (-0.0980, 51.5185),
                                    (-0.1030, 51.5170), (-0.1100, 51.5150), (-0.1110, 51.5115), (-0.1050, 51.5100), (-0.0950, 51.5083), (-0.0850, 51.5080)],
     "year": 1666, "fraction": 0.96, "rebuild": (1667, 1682, "georgian"), "resettle": None},
    {"name": "blitz_city", "poly": [(-0.1050, 51.5120), (-0.0850, 51.5115), (-0.0850, 51.5215), (-0.1050, 51.5215)],
     "year": 1940, "fraction": 0.55, "rebuild": (1953, 1976, "postwar"), "resettle": None},
    {"name": "blitz_east_end", "poly": [(-0.0750, 51.5020), (-0.0150, 51.4990), (0.0100, 51.5100), (0.0000, 51.5330), (-0.0400, 51.5330), (-0.0750, 51.5220)],
     "year": 1940, "fraction": 0.42, "rebuild": (1950, 1975, "estate"), "resettle": None},
    {"name": "blitz_southwark", "poly": [(-0.1100, 51.4900), (-0.0500, 51.4930), (-0.0450, 51.5060), (-0.1050, 51.5060)],
     "year": 1940, "fraction": 0.35, "rebuild": (1950, 1975, "estate"), "resettle": None},
    {"name": "blitz_silvertown", "poly": [(0.0050, 51.4970), (0.0700, 51.5000), (0.0650, 51.5200), (0.0050, 51.5250)],
     "year": 1940, "fraction": 0.40, "rebuild": (1952, 1975, "postwar"), "resettle": None},
    {"name": "blitz_deptford_woolwich", "poly": [(-0.0400, 51.4780), (0.0900, 51.4850), (0.0900, 51.4960), (-0.0350, 51.4900)],
     "year": 1941, "fraction": 0.30, "rebuild": (1952, 1975, "estate"), "resettle": None},
    {"name": "blitz_scatter", "poly": "INNER", "year": 1941, "fraction": 0.08, "rebuild": (1950, 1975, "postwar"), "resettle": None},
    {"name": "docklands_clearance", "poly": [(-0.0500, 51.4950), (0.0000, 51.4880), (0.0750, 51.4960), (0.0750, 51.5120), (0.0000, 51.5150), (-0.0450, 51.5120)],
     "year": 1978, "fraction": 0.55, "rebuild": (1985, 2012, "modern"), "resettle": None},
    {"name": "estate_regeneration", "poly": "INNER", "year": 2005, "fraction": 0.0, "rebuild": None, "resettle": None},
]

# post-war council estates / tower clusters: (lon, lat, radius, year_start, year_end)
ESTATES_LL = [
    (-0.0937, 51.5200, 260, 1965, 1976), (-0.0955, 51.5225, 150, 1953, 1962), (-0.1407, 51.4870, 250, 1946, 1962),
    (-0.1789, 51.4809, 200, 1969, 1977), (-0.2062, 51.5240, 200, 1968, 1972), (-0.0107, 51.5140, 260, 1965, 1970),
    (-0.0083, 51.5094, 150, 1968, 1972), (-0.0170, 51.5145, 350, 1949, 1962), (0.0214, 51.5128, 300, 1966, 1968),
    (-0.0430, 51.5215, 350, 1948, 1965), (-0.0930, 51.5710, 350, 1946, 1962), (-0.0620, 51.5540, 250, 1966, 1968),
    (-0.0895, 51.5975, 300, 1967, 1973), (-0.1130, 51.5620, 300, 1973, 1979), (-0.1810, 51.5382, 150, 1972, 1978),
    (-0.2470, 51.4530, 500, 1952, 1959), (-0.0880, 51.4870, 400, 1963, 1977), (-0.0960, 51.4930, 250, 1970, 1974),
    (-0.1040, 51.4830, 300, 1957, 1962), (-0.0750, 51.4750, 400, 1966, 1973), (-0.0356, 51.4894, 300, 1966, 1973),
    (-0.1040, 51.4690, 300, 1953, 1957), (0.0260, 51.4620, 400, 1968, 1972), (0.1100, 51.5050, 900, 1967, 1985),
    (-0.1500, 51.4740, 250, 1967, 1971), (-0.1710, 51.4640, 250, 1956, 1966), (-0.2830, 51.5650, 350, 1966, 1970),
    (-0.2730, 51.5420, 350, 1967, 1975), (-0.2700, 51.5010, 350, 1949, 1975), (-0.0450, 51.4890, 250, 1959, 1964),
    (-0.0990, 51.4950, 250, 1960, 1974), (-0.0300, 51.5300, 300, 1955, 1972), (-0.0650, 51.5280, 300, 1955, 1972),
    (-0.0620, 51.5100, 300, 1955, 1972), (-0.1700, 51.5300, 250, 1955, 1972), (-0.0200, 51.5220, 250, 1958, 1972),
]
# 21st-century (and City 1980+) high-rise clusters: (lon, lat, radius, year_start, year_end, typical height)
TOWERS_LL = [
    (-0.0820, 51.5150, 420, 1980, 2023, 150), (-0.0195, 51.5050, 480, 1988, 2022, 160), (-0.1280, 51.4830, 600, 2010, 2024, 110),
    (-0.0990, 51.4940, 280, 2010, 2022, 100), (-0.0050, 51.5410, 450, 2010, 2022, 90), (-0.0980, 51.3750, 380, 1965, 2022, 80),
    (-0.1750, 51.5180, 280, 2005, 2020, 70), (-0.1250, 51.5350, 320, 2008, 2020, 60), (-0.1450, 51.4810, 320, 2013, 2022, 70),
    (-0.0500, 51.4980, 260, 2015, 2024, 80), (-0.2830, 51.5560, 380, 2008, 2022, 70), (-0.2260, 51.5120, 280, 2015, 2022, 60),
    (-0.0130, 51.4620, 220, 2015, 2022, 80), (-0.0700, 51.5150, 280, 2005, 2022, 90), (-0.1050, 51.5050, 250, 2010, 2020, 90),
    (0.0650, 51.4900, 220, 2012, 2022, 60), (0.0050, 51.5000, 420, 2000, 2024, 70), (0.0400, 51.5080, 380, 2005, 2024, 60),
    (-0.0800, 51.4850, 220, 1995, 2020, 50), (-0.1900, 51.4680, 220, 2000, 2020, 50), (-0.0430, 51.5040, 250, 1995, 2020, 60),
]

# ------------------------------------------------------------------ city walls: (name, polyline lon/lat | special, birth, death, height)
WALLS_LL = [
    ("london_wall", CITY_WALL_LL, 200, 1765, 6),
    ("riverside_wall", [(-0.1042, 51.5115), (-0.0960, 51.5090), (-0.0880, 51.5082), (-0.0800, 51.5080), (-0.0755, 51.5085)], 280, 1200, 5),
    ("cripplegate_fort", [(-0.0965, 51.5170), (-0.0965, 51.5190), (-0.0935, 51.5192), (-0.0935, 51.5172), (-0.0965, 51.5170)], 120, 200, 5),
    ("tower_outer_wall", [(-0.0770, 51.5075), (-0.0770, 51.5100), (-0.0740, 51.5102), (-0.0735, 51.5075), (-0.0770, 51.5075)], 1285, 9999, 9),
]

# ------------------------------------------------------------------ parks (birth year by name substring)
PARK_YEARS = {
    "Hyde Park": 1637, "St James's Park": 1603, "Green Park": 1668, "Regent's Park": 1835, "Kensington Gardens": 1728,
    "Greenwich Park": 1433, "Richmond Park": 1637, "Bushy Park": 1529, "Victoria Park": 1845, "Battersea Park": 1858,
    "Finsbury Park": 1869, "Southwark Park": 1869, "Kennington Park": 1854, "Clapham Common": -9999, "Hampstead Heath": -9999,
    "Wimbledon Common": -9999, "Blackheath": -9999, "Hackney Marsh": -9999, "Epping Forest": -9999, "Wanstead Flats": -9999,
    "Crystal Palace Park": 1854, "Alexandra Park": 1863, "Brockwell Park": 1892, "Dulwich Park": 1890, "Peckham Rye": -9999,
    "Gunnersbury": 1926, "Kew Gardens": 1759, "Royal Botanic": 1759, "Lincoln's Inn Fields": 1638, "Russell Square": 1806,
    "Bloomsbury Square": 1665, "Bedford Square": 1783, "Grosvenor Square": 1725, "Berkeley Square": 1738, "Hanover Square": 1717,
    "Cavendish Square": 1720, "Portman Square": 1780, "Fitzroy Square": 1798, "Belgrave Square": 1830, "Eaton Square": 1840,
    "Sloane Square": 1771, "Soho Square": 1681, "St James's Square": 1670, "Leicester Square": 1670, "Golden Square": 1685,
    "Kensal Green": 1833, "Highgate Cemetery": 1839, "West Norwood": 1837, "Abney Park": 1840, "Brompton Cemetery": 1840,
    "Nunhead": 1840, "Tower Hamlets Cemetery": 1841, "City of London Cemetery": 1856, "Queen Elizabeth Olympic Park": 2012,
    "Burgess Park": 1950, "Mile End Park": 1950, "Thames Barrier Park": 2000, "Holland Park": 1952, "Ravenscourt": 1888,
    "Bishops Park": 1893, "Wandsworth Common": -9999, "Tooting Common": -9999, "Streatham Common": -9999, "Woolwich Common": -9999,
    "Mitcham Common": -9999, "Barnes Common": -9999, "Ham Common": -9999, "Hounslow Heath": -9999, "Hampstead": -9999,
    "Primrose Hill": 1842, "Parliament Hill": -9999, "Waterlow Park": 1889, "Clissold Park": 1889, "Springfield Park": 1905,
    "West Ham Park": 1874, "Ruskin Park": 1907, "Myatt's Fields": 1889, "Vauxhall Park": 1890, "Archbishop's Park": 1901,
    "Hilly Fields": 1896, "Telegraph Hill": 1895, "Ladywell Fields": 1889, "Mountsfield": 1905, "Beckenham Place": 1929,
    "Danson Park": 1925, "Valentines Park": 1899, "Lloyd Park": 1900, "Trent Park": 1973, "Osterley Park": 1939,
    "Syon Park": 1547, "Marble Hill": 1724, "Chiswick House": 1729, "Kenwood": 1925, "Golders Hill": 1898,
    "Bruce Castle": 1892, "Broomfield": 1903, "Grovelands": 1913, "Fryent": 1938, "Roundwood": 1895, "Gladstone Park": 1901,
    "Hanwell": 1900, "Brent Lodge": 1900, "Walpole Park": 1901, "Lammas": 1900, "Pitshanger": 1900,
    "Morden Hall": 1941, "Cannizaro": 1949, "Nonsuch": 1937, "Oaks Park": 1930, "Lloyd": 1900, "South Norwood": 1890,
}
PARK_DEFAULT_YEAR = 1900

# ------------------------------------------------------------------ road birth years by name substring
ROAD_YEARS = {
    # Roman roads (still the main radials)
    "Edgware Road": 50, "Maida Vale": 50, "Kilburn High Road": 50, "Shoot-up Hill": 50, "Cricklewood Broadway": 50, "Watling": 50,
    "Old Kent Road": 50, "New Cross Road": 50, "Shooters Hill": 50, "Kingsland Road": 50, "Kingsland High Street": 50,
    "Stoke Newington Road": 50, "Stoke Newington High Street": 50, "Stamford Hill": 50, "Tottenham High Road": 50, "Ermine": 50,
    "Bishopsgate": 50, "Gracechurch Street": 50, "Shoreditch High Street": 50, "Whitechapel Road": 50, "Mile End Road": 50,
    "Bow Road": 50, "Romford Road": 50, "High Road Ilford": 50, "Oxford Street": 50, "Bayswater Road": 50, "Notting Hill Gate": 50,
    "Holland Park Avenue": 50, "Uxbridge Road": 50, "High Street Kensington": 50, "Clapham Road": 50, "Kennington Park Road": 50,
    "Clapham High Street": 50, "Balham High Road": 50, "Tooting High Street": 50, "Borough High Street": 50, "Newington Causeway": 50,
    "London Road": 50, "Stane": 50, "Fleet Street": 50, "Ludgate Hill": 50, "Cheapside": 60, "Cornhill": 60, "Leadenhall Street": 60,
    "Fenchurch Street": 60, "Cannon Street": 60, "Eastcheap": 60, "Thames Street": 100, "Aldgate High Street": 60, "Newgate Street": 60,
    # Saxon / medieval
    "Strand": 700, "Holborn": 950, "High Holborn": 950, "Aldersgate Street": 950, "Goswell Road": 1100, "St John Street": 1100,
    "Whitehall": 1250, "King Street": 1100, "Charing Cross": 1200, "Long Acre": 1600, "Drury Lane": 1200, "Chancery Lane": 1200,
    "Farringdon Road": 1860, "Farringdon Street": 1737, "Moorgate": 1415, "Coleman Street": 1100, "Wood Street": 900, "Gresham Street": 1100,
    "Lombard Street": 900, "Threadneedle Street": 1100, "Old Street": 700, "Bethnal Green Road": 1300, "Hackney Road": 1300,
    "Cable Street": 1650, "The Highway": 1300, "Ratcliffe Highway": 1300, "Commercial Street": 1845, "Brick Lane": 1550,
    "Tooley Street": 1100, "Bermondsey Street": 1200, "Jamaica Road": 1300, "Lambeth Road": 1750, "Kennington Lane": 1300,
    "King's Road": 1720, "Fulham Road": 1300, "Brompton Road": 1300, "Knightsbridge": 1100, "Piccadilly": 1600, "Park Lane": 1700,
    "Tottenham Court Road": 1300, "Hampstead Road": 1300, "Gray's Inn Road": 1200, "Kentish Town Road": 1300, "Highgate Road": 1300,
    "Holloway Road": 1300, "Upper Street": 1000, "Essex Road": 1300, "Camden High Street": 1791, "Camden Road": 1826,
    # 18th-19th c. new roads
    "Euston Road": 1756, "Marylebone Road": 1756, "Pentonville Road": 1756, "New Road": 1756, "City Road": 1761,
    "Westminster Bridge Road": 1750, "Vauxhall Bridge Road": 1816, "Regent Street": 1820, "Portland Place": 1775,
    "Commercial Road": 1804, "East India Dock Road": 1808, "Camberwell New Road": 1818, "Finchley Road": 1830, "Caledonian Road": 1826,
    "Kingsway": 1905, "Aldwych": 1905, "Shaftesbury Avenue": 1886, "Charing Cross Road": 1887, "New Oxford Street": 1847,
    "Holborn Viaduct": 1869, "Victoria Street": 1851, "Queen Victoria Street": 1871, "Victoria Embankment": 1870,
    "Albert Embankment": 1869, "Chelsea Embankment": 1874, "Blackfriars Road": 1769, "Waterloo Road": 1817, "St George's Road": 1750,
    "Walworth Road": 1300, "Camberwell Road": 1300, "Brixton Road": 50, "Streatham High Road": 1300, "Southwark Bridge Road": 1819,
    "Great Dover Street": 1814, "Rotherhithe New Road": 1830, "Lower Road": 1300, "Evelyn Street": 1750, "Deptford Broadway": 1300,
    "Rosebery Avenue": 1892, "Clerkenwell Road": 1878, "Theobalds Road": 1650, "Southampton Row": 1700, "Woburn Place": 1800,
    "Harrow Road": 1300, "Westbourne Grove": 1840, "Ladbroke Grove": 1840, "Cromwell Road": 1855, "Exhibition Road": 1855,
    "Warwick Road": 1860, "Earl's Court Road": 1300, "Lillie Road": 1860, "Talgarth Road": 1860, "Great West Road": 1925,
    "Western Avenue": 1932, "North Circular": 1930, "Eastern Avenue": 1925, "Southend Arterial": 1925, "Kingston By-Pass": 1927,
    "Kingston Bypass": 1927, "Great Cambridge Road": 1924, "Watford Way": 1927, "Hendon Way": 1927, "Barnet By-Pass": 1927,
    "Barnet Way": 1927, "Sidcup Road": 1923, "Purley Way": 1925, "Rochester Way": 1930, "Great South West Road": 1925,
    "Westway": 1970, "Marylebone Flyover": 1967, "East Cross Route": 1970, "Blackwall Tunnel": 1967, "Limehouse Link": 1993,
    "Aspen Way": 1993, "Silvertown Way": 1934, "Cromwell Road Extension": 1941, "Talgarth": 1961, "Hammersmith Flyover": 1961,
    "Chiswick Flyover": 1959, "M1": 1959, "M4": 1965, "M11": 1977, "M25": 1986, "A102": 1967, "A12": 1999, "A13": 1990,
    "Lea Bridge Road": 1750, "Seven Sisters Road": 1833, "Green Lanes": 1300, "Southgate Road": 1830, "New North Road": 1812,
    "Mare Street": 1300, "Homerton": 1300, "Roman Road": 100, "Grove Road": 1840, "Burdett Road": 1862, "Westferry Road": 1810,
    "Manchester Road": 1850, "Prestons Road": 1810, "Poplar High Street": 1300, "Barking Road": 1810, "Stratford High Street": 50,
    "Bow Flyover": 1967, "Battersea Park Road": 1850, "Lavender Hill": 1850, "Queenstown Road": 1860, "Nine Elms Lane": 1750,
    "Wandsworth Road": 1300, "Trinity Road": 1850, "Upper Richmond Road": 1300, "Putney Bridge Road": 1729, "Lower Richmond Road": 1300,
    "Castelnau": 1827, "Hammersmith Bridge Road": 1827, "Chiswick High Road": 50, "Kew Road": 1759, "Kew Bridge Road": 1759,
    "Uxbridge": 50, "Ealing Road": 1300, "Greenford Road": 1924, "Hanger Lane": 1930, "Ruislip Road": 1930, "Northolt Road": 1930,
}

# ------------------------------------------------------------------ bridges (fallback list, replaced by data/history/bridges.json)
BRIDGES_FALLBACK = [
    {"id": "roman_bridge", "name": "Roman London Bridge", "lon": -0.0870, "lat": 51.5078, "birth": 50, "death": 400, "kind": "roman_timber", "length_m": 300, "width_m": 5, "deck_height_m": 5},
    {"id": "old_london_bridge", "name": "Old London Bridge", "lon": -0.0873, "lat": 51.5079, "birth": 1209, "death": 1831, "kind": "medieval_stone_with_houses", "length_m": 282, "width_m": 8, "deck_height_m": 6},
    {"id": "new_london_bridge", "name": "London Bridge (1831)", "lon": -0.0878, "lat": 51.5081, "birth": 1831, "death": 1967, "kind": "stone_arch", "length_m": 283, "width_m": 16, "deck_height_m": 8},
    {"id": "london_bridge_1973", "name": "London Bridge", "lon": -0.0878, "lat": 51.5081, "birth": 1973, "death": None, "kind": "concrete_beam", "length_m": 269, "width_m": 32, "deck_height_m": 9},
    {"id": "westminster_bridge_1750", "name": "Westminster Bridge", "lon": -0.1219, "lat": 51.5008, "birth": 1750, "death": 1861, "kind": "stone_arch", "length_m": 373, "width_m": 13, "deck_height_m": 7.5},
    {"id": "westminster_bridge", "name": "Westminster Bridge", "lon": -0.1219, "lat": 51.5008, "birth": 1862, "death": None, "kind": "iron_arch", "length_m": 250, "width_m": 26, "deck_height_m": 8},
    {"id": "blackfriars_bridge_1769", "name": "Blackfriars Bridge", "lon": -0.1044, "lat": 51.5097, "birth": 1769, "death": 1864, "kind": "stone_arch", "length_m": 303, "width_m": 13, "deck_height_m": 8},
    {"id": "blackfriars_bridge", "name": "Blackfriars Bridge", "lon": -0.1044, "lat": 51.5097, "birth": 1869, "death": None, "kind": "iron_arch", "length_m": 281, "width_m": 32, "deck_height_m": 8.5},
    {"id": "tower_bridge", "name": "Tower Bridge", "lon": -0.0753, "lat": 51.5056, "birth": 1894, "death": None, "kind": "bascule", "length_m": 244, "width_m": 18, "deck_height_m": 9.5},
]

# ------------------------------------------------------------------ water that appears / disappears (fallback)
# polygon or polyline (lon/lat) with width, birth, death
WATER_EVENTS_FALLBACK = [
    {"name": "Fleet river", "line": [(-0.1400, 51.5560), (-0.1330, 51.5450), (-0.1180, 51.5370), (-0.1100, 51.5270), (-0.1060, 51.5200),
                                      (-0.1045, 51.5175), (-0.1043, 51.5130), (-0.1040, 51.5100)], "width": 12, "birth": -9999, "death": 1760},
    {"name": "Fleet ditch (lower)", "line": [(-0.1050, 51.5185), (-0.1043, 51.5130), (-0.1040, 51.5100)], "width": 15, "birth": -9999, "death": 1766},
    {"name": "Walbrook", "line": [(-0.0880, 51.5240), (-0.0890, 51.5185), (-0.0900, 51.5140), (-0.0910, 51.5100), (-0.0915, 51.5085)], "width": 6, "birth": -9999, "death": 1450},
    {"name": "Tyburn", "line": [(-0.1650, 51.5550), (-0.1560, 51.5350), (-0.1500, 51.5220), (-0.1450, 51.5120), (-0.1380, 51.5060), (-0.1320, 51.4990), (-0.1290, 51.4940)], "width": 5, "birth": -9999, "death": 1700},
    {"name": "Westbourne", "line": [(-0.1900, 51.5560), (-0.1800, 51.5300), (-0.1700, 51.5100), (-0.1600, 51.5000), (-0.1550, 51.4900), (-0.1500, 51.4840)], "width": 5, "birth": -9999, "death": 1850},
    {"name": "Effra", "line": [(-0.0900, 51.4200), (-0.1050, 51.4450), (-0.1150, 51.4600), (-0.1180, 51.4750), (-0.1250, 51.4850)], "width": 5, "birth": -9999, "death": 1860},
    {"name": "Neckinger", "line": [(-0.1000, 51.4960), (-0.0850, 51.4990), (-0.0700, 51.5010), (-0.0640, 51.5030)], "width": 5, "birth": -9999, "death": 1820},
    {"name": "Thames foreshore (pre-embankment, north bank)", "poly": [(-0.1235, 51.5070), (-0.1160, 51.5090), (-0.1060, 51.5105), (-0.1060, 51.5115),
                                                                       (-0.1160, 51.5100), (-0.1235, 51.5080)], "birth": -9999, "death": 1870},
    {"name": "London Docks", "poly": [(-0.0660, 51.5060), (-0.0530, 51.5060), (-0.0530, 51.5100), (-0.0660, 51.5100)], "birth": 1805, "death": 1975},
    {"name": "Surrey Commercial Docks", "poly": [(-0.0580, 51.4930), (-0.0400, 51.4930), (-0.0400, 51.5010), (-0.0580, 51.5010)], "birth": 1807, "death": 1978},
]


# ------------------------------------------------------------------ conversion of everything to metres
def _poly_from(spec):
    if spec == "CITY":
        return CITY
    if spec == "CITY_BUF":
        return CITY.buffer(120)
    if spec == "INNER":
        return INNER
    if isinstance(spec, tuple):
        return spec   # resolved by growth.py (e.g. ("INTERWAR_BUFFER", 1200))
    if isinstance(spec, list):
        return Polygon(P(spec))
    return spec


ZONES = [(n, _poly_from(p), ys, ye, k) for n, p, ys, ye, k in ZONES_LL]

_v = load("villages.json")
if _v:
    VILLAGES = [(v["name"], *ll(v["lon"], v["lat"]), v["radius_m"], v["year_start"], v["year_end"]) for v in _v["villages"]
                if abs(ll(v["lon"], v["lat"])[0]) < 26000 and abs(ll(v["lon"], v["lat"])[1]) < 20000]
else:
    VILLAGES = [(n, *ll(lon, lat), r, ys, ye) for n, lon, lat, r, ys, ye in VILLAGES_LL]

EVENTS = []
for e in EVENTS_LL:
    EVENTS.append({"name": e["name"], "poly": _poly_from(e["poly"]), "year": e["year"], "fraction": e["fraction"],
                   "rebuild": e["rebuild"], "resettle": e["resettle"]})
_ev = load("events.json")
if _ev:
    for e in _ev.get("events", []):
        try:
            if not e.get("polygon"):
                continue
            EVENTS.append({"name": e["name"], "poly": Polygon(P(e["polygon"])), "year": int(e["year"]),
                           "fraction": float(e.get("destroyed_fraction", 0.5)),
                           "rebuild": ((int(e["rebuild_start"]), int(e["rebuild_end"]), e.get("rebuild_kit", "postwar")) if e.get("rebuild_start") else None),
                           "resettle": None, "researched": True})
        except Exception as ex:  # noqa
            print("[history] bad event", e.get("name"), ex)
if any(e.get("researched") for e in EVENTS):
    # the researched event table supersedes the hand-authored fire / Blitz / Docklands entries
    EVENTS = [e for e in EVENTS if e.get("researched") or e["name"] in ("roman_abandonment", "lundenwic_abandoned")]
EVENTS.sort(key=lambda e: e["year"])

_gz = load("growth_zones.json")
ESTATES = [(*ll(lon, lat), r, ys, ye) for lon, lat, r, ys, ye in ESTATES_LL]
TOWERS = [(*ll(lon, lat), r, ys, ye, h) for lon, lat, r, ys, ye, h in TOWERS_LL]
if _gz:
    for e in _gz.get("estates", []):
        try:
            ESTATES.append((*ll(e["lon"], e["lat"]), float(e.get("radius_m", 250)), int(e["year_start"]), int(e["year_end"])))
        except Exception:
            pass
    for t in _gz.get("towers", []):
        try:
            TOWERS.append((*ll(t["lon"], t["lat"]), float(t.get("radius_m", 300)), int(t["year_start"]), int(t["year_end"]), float(t.get("typical_height_m", 80))))
        except Exception:
            pass
RESEARCH_ZONES = []
if _gz and HAVE_SHAPELY:
    # district-level polygons only: the huge policy envelopes (Green Belt, "infill", "densification") would
    # otherwise stamp a single birth year over hundreds of km2
    for z in _gz.get("zones", []):
        try:
            poly = Polygon(P(z["polygon"]))
            if not poly.is_valid:
                poly = poly.buffer(0)
            kit = z.get("kit", "victorian")
            if poly.area > 100e6 or kit not in ("celtic", "roman", "saxon", "medieval", "tudor", "georgian", "victorian", "interwar", "postwar", "modern", "estate", "tower"):
                continue
            nm = z["name"].lower()
            if any(k in nm for k in ("dereliction", "green belt", "growth stops", "contraction", "abandon")):
                continue
            RESEARCH_ZONES.append((z["name"], poly, int(z["year_start"]), int(z["year_end"]), kit))
        except Exception as ex:  # noqa
            print("[history] bad zone", z.get("name"), ex)

# the hand-authored growth envelopes were 2-3x the historical built-up area (London c.1600 ~5 km2, 1700 ~13 km2,
# 1750 ~20 km2, 1800 ~30 km2): shrink them about their centroid; the researched district polygons stay as they are
ZONE_SHRINK = {"medieval_suburbs": 0.62, "tudor": 0.65, "stuart": 0.65, "restoration": 0.62, "georgian_early": 0.66, "georgian_late": 0.80}
if HAVE_SHAPELY:
    from shapely import affinity as _aff
    ZONES = [(n, (_aff.scale(p, ZONE_SHRINK[n], ZONE_SHRINK[n], origin="centroid") if (n in ZONE_SHRINK and hasattr(p, "centroid")) else p), a, b, k)
             for n, p, a, b, k in ZONES]

WALLS = [(n, [ll(lon, lat) for lon, lat in pl], b, d, h) for n, pl, b, d, h in WALLS_LL]
PRE_FORESTS, PRE_MARSHES = [], []
_L = load("landscape_history.json")
if _L:
    rw = []
    for w in _L.get("walls", []):
        try:
            wid = w.get("id", "")
            if wid == "london_wall_landward" and w.get("polyline"):
                rw.append(("london_wall", [ll(a, b) for a, b in w["polyline"]], 200, 1775, 6))
            elif wid == "london_wall_riverside" and w.get("polyline"):
                rw.append(("riverside_wall", [ll(a, b) for a, b in w["polyline"]], 275, 1150, 5))
            elif wid == "cripplegate_fort" and w.get("polygon"):
                rw.append(("cripplegate_fort", [ll(a, b) for a, b in w["polygon"]], 120, 260, 5))
            elif wid == "civil_war_lines_of_communication" and w.get("polyline"):
                rw.append(("civil_war_lines", [ll(a, b) for a, b in w["polyline"]], 1643, 1647, 3))
        except Exception as ex:  # noqa
            print("[history] bad wall", w.get("id"), ex)
    if rw:
        WALLS = rw + [w for w in WALLS if w[0] == "tower_outer_wall"]
    for pk in _L.get("parks", []):
        nm = pk.get("name"); yr = pk.get("enclosed_or_opened") or pk.get("public_year")
        if nm and yr is not None and nm not in PARK_YEARS:
            try:
                PARK_YEARS[nm] = int(yr)
            except Exception:
                pass
    if HAVE_SHAPELY:
        for f in _L.get("forests_and_marshes", []):
            try:
                if not f.get("polygon"):
                    continue
                poly = Polygon(P(f["polygon"]))
                ceased = int(f.get("ceased_year") or f.get("year_built_over") or 1850)
                cover = (f.get("land_cover") or "").lower()
                if "marsh" in cover or "fen" in cover or "reed" in cover:
                    PRE_MARSHES.append((poly, ceased))
                elif "wood" in cover or "forest" in cover or "heath" in cover:
                    PRE_FORESTS.append((poly, ceased))
            except Exception as ex:  # noqa
                print("[history] bad land cover", f.get("id"), ex)

_b = load("bridges.json")
BRIDGES = []
for b in (_b if _b else BRIDGES_FALLBACK):
    x, y = ll(b["lon"], b["lat"])
    BRIDGES.append({"id": b["id"], "name": b["name"], "x": x, "y": y, "birth": int(b["birth"]), "death": int(b["death"]) if b.get("death") else 9999,
                    "kind": b.get("kind", "stone_arch"), "length": float(b.get("length_m", 250)), "width": float(b.get("width_m", 12)),
                    "deck": float(b.get("deck_height_m", 8))})

WATER_EVENTS = []
_w = load("water_history.json")
_used_research_water = False


def _int(v):
    try:
        return int(v)
    except Exception:
        return None


if _w and HAVE_SHAPELY:
    for d in _w.get("docks", []):
        try:
            if not d.get("polygon"):
                continue
            if "group" in d["name"].lower() or "whole" in d["name"].lower():
                continue          # crude envelopes around whole dock systems: the individual docks are listed anyway
            birth = _int(d.get("dug")) or _int(d.get("opened"))
            if birth is None:
                continue
            filled = _int(d.get("filled"))
            death = filled if filled else 9999
            WATER_EVENTS.append({"name": d["name"], "poly": Polygon(P(d["polygon"])), "birth": birth, "death": death})
            _used_research_water = True
        except Exception as ex:  # noqa
            print("[history] bad dock", d.get("name"), ex)
    COVER_WORDS = ("cover", "arch", "culvert", "vault", "sewer", "piped", "enclosed", "built over", "filled", "taken into")
    for r in _w.get("lost_rivers", []):
        try:
            pl = r.get("polyline") or r.get("course")
            if not pl or r.get("status") == "open":
                continue
            years = sorted(int(c["to_year"]) for c in (r.get("culverted") or [])
                           if c.get("to_year") and any(w in c.get("segment", "").lower() for w in COVER_WORDS))
            if not years:
                continue
            lo, hi = years[0], years[-1]
            line = LineString(P(pl))
            wdt = float(r.get("width_m", 6))
            if hi - lo > 20 and line.length > 2000:
                # lower (mouth) half disappears first, the upper reaches later
                half = line.length / 2
                pts = list(line.coords)
                upper, lower, acc = [pts[0]], [], 0.0
                for a, b in zip(pts[:-1], pts[1:]):
                    seg = math.dist(a, b)
                    if acc + seg <= half:
                        upper.append(b)
                    else:
                        if not lower:
                            lower.append(a)
                        lower.append(b)
                    acc += seg
                if len(upper) > 1:
                    WATER_EVENTS.append({"name": r["name"] + " (upper)", "line": LineString(upper), "width": wdt * 0.7, "birth": -9999, "death": hi})
                if len(lower) > 1:
                    WATER_EVENTS.append({"name": r["name"] + " (lower)", "line": LineString(lower), "width": wdt, "birth": -9999, "death": lo})
            else:
                WATER_EVENTS.append({"name": r["name"], "line": line, "width": wdt, "birth": -9999, "death": lo})
            _used_research_water = True
        except Exception as ex:  # noqa
            print("[history] bad river", r.get("name"), ex)
    for t in _w.get("thames_changes", []):
        try:
            if t.get("type") in ("embankment", "waterfront_line") and t.get("polyline") and t.get("width_reclaimed_m"):
                w = float(t["width_reclaimed_m"])
                if w <= 0:
                    continue
                yr = int(t.get("year") or t.get("year_opened"))
                WATER_EVENTS.append({"name": t["name"], "line": LineString(P(t["polyline"])), "width": w, "birth": -9999, "death": yr})
        except Exception as ex:  # noqa
            print("[history] bad thames change", t.get("name"), ex)
if not _used_research_water and HAVE_SHAPELY:
    for w in WATER_EVENTS_FALLBACK:
        if "line" in w:
            WATER_EVENTS.append({"name": w["name"], "line": LineString(P(w["line"])), "width": w["width"], "birth": w["birth"], "death": w["death"]})
        else:
            WATER_EVENTS.append({"name": w["name"], "poly": Polygon(P(w["poly"])), "birth": w["birth"], "death": w["death"]})

# canal birth years by OSM name substring
CANAL_YEARS = {"Regent's Canal": 1820, "Regents Canal": 1820, "Grand Union": 1801, "Grand Junction": 1801, "Paddington": 1801,
               "Hertford Union": 1830, "Limehouse Cut": 1770, "Lee Navigation": 1770, "Lea Navigation": 1770, "River Lea": -9999,
               "River Lee": -9999, "New River": 1613, "Bow Back": -9999, "City Mill": -9999, "Wandle": -9999, "Ravensbourne": -9999,
               "Brent": -9999, "Beverley": -9999, "Crane": -9999, "Colne": -9999, "Longford": 1650, "Duke of Northumberland": 1530,
               "Roding": -9999, "Ingrebourne": -9999, "Pool": -9999, "Quaggy": -9999, "Hogsmill": -9999, "Pinn": -9999, "Yeading": -9999,
               "Silk Stream": -9999, "Dollis": -9999, "Mutton": -9999, "Salmons": -9999, "Pymmes": -9999, "Moselle": -9999,
               "Cray": -9999, "Darent": -9999, "Shuttle": -9999, "Wealdstone": -9999, "Deans": -9999, "Grand Surrey": 1807}

# researched transport lines (metres) with opening years: used to date rail / road pieces by proximity
RAIL_LINES, ROAD_LINES = [], []
_t = load("transport_history.json")
if _t and HAVE_SHAPELY:
    SKIP = ("Metropolitan", "District", "City & South", "Central London", "Yerkes", "Victoria line", "Jubilee", "Elizabeth", "East London", "High Speed")
    for r in _t.get("railways", []):
        try:
            if any(k in r.get("name", "") for k in SKIP) or not r.get("polyline"):
                continue
            RAIL_LINES.append((LineString(P(r["polyline"])), int(r["opened"]), r.get("name", "")))
        except Exception as ex:  # noqa
            print("[history] bad railway", r.get("name"), ex)
    for r in _t.get("roman_roads", []):
        try:
            if r.get("polyline"):
                ROAD_LINES.append((LineString(P(r["polyline"])), int(r.get("built_year") or 50), r.get("name", "")))
        except Exception:
            pass
    for r in _t.get("medieval_roads", []):
        try:
            if r.get("polyline"):
                ROAD_LINES.append((LineString(P(r["polyline"])), int(r.get("established_by") or 1300), r.get("name", "")))
        except Exception:
            pass
    for r in _t.get("new_roads", []):
        try:
            if r.get("polyline") and (r.get("year") or r.get("opened")) and "Tunnel" not in r.get("name", ""):
                ROAD_LINES.append((LineString(P(r["polyline"])), int(r.get("year") or r.get("opened")), r.get("name", "")))
        except Exception:
            pass

# ------------------------------------------------------------------ landmarks
# (name, x, y, rotation deg ccw from +x, birth, death, builder, params) - builder "glb:<id>" or procedural
from landmark_table import build_landmark_list   # noqa: E402
LANDMARKS = build_landmark_list(load("landmarks.json"))

if __name__ == "__main__":
    print("zones", len(ZONES), "research zones", len(RESEARCH_ZONES), "villages", len(VILLAGES), "events", len(EVENTS),
          "estates", len(ESTATES), "towers", len(TOWERS), "bridges", len(BRIDGES), "water events", len(WATER_EVENTS), "landmarks", len(LANDMARKS))
    for n, p, ys, ye, k in ZONES:
        a = p.area / 1e6 if hasattr(p, "area") else None
        print(f"  {n:24s} {ys:5d}-{ye:5d} {k:10s} {a and round(a, 1)} km2")
