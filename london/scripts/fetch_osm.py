"""Fetch OpenStreetMap geometry for the London replica via Overpass.

Output: london/data/osm_raw.json  (lon/lat geometry, grouped by layer)
Attribution: (c) OpenStreetMap contributors, ODbL 1.0
"""
import json, os, sys, time, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "osm_raw.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# big bbox ~ 49 x 36 km around St Paul's (south, west, north, east)
BIG = (51.355, -0.44, 51.685, 0.27)
# inner London for fine streets, split in tiles to keep Overpass happy
INNER = (51.43, -0.26, 51.585, 0.06)


def bbox(b):
    return f"({b[0]},{b[1]},{b[2]},{b[3]})"


def tiles(b, nx, ny):
    s, w, n, e = b
    out = []
    for i in range(ny):
        for j in range(nx):
            out.append((s + (n - s) * i / ny, w + (e - w) * j / nx, s + (n - s) * (i + 1) / ny, w + (e - w) * (j + 1) / nx))
    return out


LANDMARK_NAMES = "|".join([
    "St Paul's Cathedral", "Tower of London", "White Tower", "Westminster Abbey", "Palace of Westminster", "Elizabeth Tower",
    "Buckingham Palace", "Tower Bridge", "The Shard", "30 St Mary Axe", "22 Bishopsgate", "20 Fenchurch Street", "122 Leadenhall Street",
    "Heron Tower", "Tower 42", "Lloyd's building", "Bank of England", "Royal Exchange", "Mansion House", "Guildhall", "Monument to the Great Fire",
    "One Canada Square", "8 Canada Square", "25 Canada Square", "Newfoundland", "Landmark Pinnacle", "One Park Drive",
    "BT Tower", "Centre Point", "Millbank Tower", "Barbican", "Shakespeare Tower", "Lauderdale Tower", "Cromwell Tower",
    "London Eye", "The O2", "Tate Modern", "Battersea Power Station", "British Museum", "Natural History Museum", "Victoria and Albert Museum",
    "Royal Albert Hall", "Albert Memorial", "National Gallery", "Nelson's Column", "Somerset House", "St Pancras", "King's Cross",
    "Paddington", "Liverpool Street", "Victoria Station", "Charing Cross", "Cannon Street", "Waterloo", "London Bridge Station", "Euston", "Marylebone",
    "Royal Courts of Justice", "Old Bailey", "Westminster Cathedral", "Southwark Cathedral", "St Bartholomew", "Temple Church",
    "Lambeth Palace", "St James's Palace", "Kensington Palace", "Horse Guards", "Banqueting House", "Admiralty Arch", "Marble Arch",
    "Wellington Arch", "Wembley Stadium", "London Stadium", "Emirates Stadium", "Stamford Bridge", "Tottenham Hotspur Stadium",
    "The Oval", "Lord's", "Alexandra Palace", "Crystal Palace", "Old Royal Naval College", "Queen's House", "Royal Observatory",
    "Royal Hospital Chelsea", "St Martin-in-the-Fields", "Christ Church Spitalfields", "St Bride", "St Mary-le-Bow", "Smithfield Market",
    "Leadenhall Market", "County Hall", "City Hall", "Senate House", "Bush House", "Broadcasting House", "Harrods", "Selfridges",
    "Trellick Tower", "Strata", "One Blackfriars", "St George Wharf Tower", "Thames Barrier", "ExCeL", "Olympic", "ArcelorMittal Orbit",
    "Royal Festival Hall", "National Theatre", "Shell Centre", "Imperial Institute", "Queen's Tower", "Kew Palace", "Great Pagoda",
    "Hampton Court Palace", "Eltham Palace", "Charterhouse", "Mansion House", "Custom House", "St Katharine Docks", "Tobacco Dock",
    "Broadgate Tower", "The Scalpel", "Millennium Dome", "Wembley Arena", "Twickenham Stadium", "Chelsea Barracks", "Apsley House",
    "Cumberland Terrace", "Bedford Square", "Grosvenor Square", "SIS Building", "Vauxhall Cross", "Tate Britain", "Imperial War Museum",
    "Chiswick House", "Syon House", "Osterley", "Ham House", "Marble Hill", "Fulham Palace", "Kenwood", "Highgate Cemetery",
])

QUERIES = {
    "water": f"""
[out:json][timeout:300];
(
  way["natural"="water"]{bbox(BIG)};
  relation["natural"="water"]{bbox(BIG)};
  way["waterway"="riverbank"]{bbox(BIG)};
  relation["waterway"="riverbank"]{bbox(BIG)};
  way["waterway"="dock"]{bbox(BIG)};
  relation["waterway"="dock"]{bbox(BIG)};
  way["landuse"="reservoir"]{bbox(BIG)};
  relation["landuse"="reservoir"]{bbox(BIG)};
  way["waterway"="canal"]{bbox(BIG)};
  way["waterway"="river"]{bbox(BIG)};
);
out geom;
""",
    "islands": f"""
[out:json][timeout:120];
(
  way["place"="island"]{bbox(BIG)};
  relation["place"="island"]{bbox(BIG)};
  way["place"="islet"]{bbox(BIG)};
);
out geom;
""",
    "roads_major": f"""
[out:json][timeout:600];
(
  way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|secondary|tertiary)$"]{bbox(BIG)};
);
out geom;
""",
    "green": f"""
[out:json][timeout:300];
(
  way["leisure"="park"]{bbox(BIG)};
  relation["leisure"="park"]{bbox(BIG)};
  way["leisure"="garden"]{bbox(INNER)};
  relation["leisure"="garden"]{bbox(INNER)};
  way["leisure"="common"]{bbox(BIG)};
  relation["leisure"="common"]{bbox(BIG)};
  way["landuse"="forest"]{bbox(BIG)};
  relation["landuse"="forest"]{bbox(BIG)};
  way["natural"="wood"]{bbox(BIG)};
  relation["natural"="wood"]{bbox(BIG)};
  way["natural"="heath"]{bbox(BIG)};
  relation["natural"="heath"]{bbox(BIG)};
  way["landuse"="cemetery"]{bbox(BIG)};
  relation["landuse"="cemetery"]{bbox(BIG)};
  way["leisure"="golf_course"]{bbox(BIG)};
  relation["leisure"="golf_course"]{bbox(BIG)};
  way["landuse"="recreation_ground"]{bbox(BIG)};
  way["leisure"="nature_reserve"]{bbox(BIG)};
  relation["leisure"="nature_reserve"]{bbox(BIG)};
);
out geom;
""",
    "rail": f"""
[out:json][timeout:300];
(
  way["railway"="rail"]["usage"~"^(main|branch)$"]{bbox(BIG)};
  way["railway"="light_rail"]{bbox(BIG)};
);
out geom;
""",
    "admin": f"""
[out:json][timeout:180];
(
  relation["boundary"="administrative"]["admin_level"="5"]["name"="Greater London"];
  relation["boundary"="administrative"]["admin_level"="6"]["name"="City of London"];
  relation["boundary"="administrative"]["admin_level"="8"]{bbox(BIG)};
  way["highway"="motorway"]["ref"="M25"];
  way["aeroway"="runway"]{bbox((51.30, -0.55, 51.70, 0.30))};
  way["aeroway"="aerodrome"]{bbox((51.30, -0.55, 51.70, 0.30))};
  relation["aeroway"="aerodrome"]{bbox((51.30, -0.55, 51.70, 0.30))};
);
out geom;
""",
    "landmarks": f"""
[out:json][timeout:300];
(
  way["building"]["name"~"{LANDMARK_NAMES}"]{bbox(BIG)};
  relation["building"]["name"~"{LANDMARK_NAMES}"]{bbox(BIG)};
  way["man_made"~"^(tower|bridge)$"]["name"~"{LANDMARK_NAMES}"]{bbox(BIG)};
  relation["man_made"~"^(tower|bridge)$"]["name"~"{LANDMARK_NAMES}"]{bbox(BIG)};
  way["historic"]["name"~"{LANDMARK_NAMES}"]{bbox(BIG)};
  relation["historic"]["name"~"{LANDMARK_NAMES}"]{bbox(BIG)};
  way["historic"="citywalls"]{bbox(BIG)};
  way["historic"="city_gate"]{bbox(BIG)};
);
out geom;
""",
    "bridges": f"""
[out:json][timeout:300];
(
  way["bridge"]["name"~"Bridge|bridge"]{bbox(BIG)};
);
out geom;
""",
}
# outer suburbs (residential streets, lower priority; fetched in a second pass)
OUTER = (51.375, -0.40, 51.645, 0.22)
for i, t in enumerate(tiles(OUTER, 6, 4)):
    if t[2] <= INNER[2] and t[0] >= INNER[0] and t[1] >= INNER[1] and t[3] <= INNER[3]:
        continue
    QUERIES[f"roads_outer_{i}"] = f"""
[out:json][timeout:600];
(
  way["highway"~"^(residential|unclassified|living_street)$"]{bbox(t)};
);
out geom;
"""
for i, t in enumerate(tiles(INNER, 4, 3)):
    QUERIES[f"roads_minor_{i}"] = f"""
[out:json][timeout:600];
(
  way["highway"~"^(residential|unclassified|living_street|pedestrian)$"]{bbox(t)};
);
out geom;
"""


def fetch(name, query):
    for attempt in range(4):
        for ep in ENDPOINTS:
            try:
                data = urllib.parse.urlencode({"data": query}).encode()
                req = urllib.request.Request(ep, data=data, headers={"User-Agent": "london-replica/1.0"})
                t0 = time.time()
                with urllib.request.urlopen(req, timeout=700) as r:
                    payload = json.load(r)
                n = len(payload.get("elements", []))
                print(f"[{name}] {ep} -> {n} elements in {time.time()-t0:.1f}s", flush=True)
                return payload["elements"]
            except Exception as e:  # noqa
                print(f"[{name}] {ep} attempt {attempt} failed: {e}", flush=True)
                time.sleep(15 * (attempt + 1))
    raise SystemExit(f"failed to fetch {name}")


def main():
    only = sys.argv[1:]
    result = {}
    if os.path.exists(OUT):
        result = json.load(open(OUT, encoding="utf-8"))
    for name, q in QUERIES.items():
        if only and name not in only:
            continue
        if name in result and not only:
            print(f"[{name}] cached ({len(result[name])})")
            continue
        result[name] = fetch(name, q)
        json.dump(result, open(OUT, "w", encoding="utf-8"))
    # merge minor road tiles
    minor, outer = [], []
    for k in list(result):
        if k.startswith("roads_minor_"):
            minor.extend(result[k])
        if k.startswith("roads_outer_"):
            outer.extend(result[k])
    result["roads_minor"] = minor
    result["roads_outer"] = outer
    json.dump(result, open(OUT, "w", encoding="utf-8"))
    print("layers:", {k: len(v) for k, v in result.items()})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
