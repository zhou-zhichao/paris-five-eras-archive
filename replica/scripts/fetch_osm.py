"""Fetch OpenStreetMap geometry for the Paris replica via Overpass.

Output: replica/data/osm_raw.json  (lon/lat geometry, grouped by layer)
Attribution: (c) OpenStreetMap contributors, ODbL 1.0
"""
import json, os, sys, time, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "osm_raw.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# big bbox ~ 36 x 26 km around Notre-Dame (south, west, north, east)
BIG = (48.72, 2.10, 48.98, 2.60)
# Paris proper (inside the peripherique) for fine streets
PARIS = (48.812, 2.245, 48.905, 2.425)


def bbox(b):
    return f"({b[0]},{b[1]},{b[2]},{b[3]})"


QUERIES = {
    "water": f"""
[out:json][timeout:180];
(
  way["natural"="water"]{bbox(BIG)};
  relation["natural"="water"]{bbox(BIG)};
  way["waterway"="riverbank"]{bbox(BIG)};
  relation["waterway"="riverbank"]{bbox(BIG)};
  way["waterway"="canal"]{bbox(BIG)};
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
[out:json][timeout:300];
(
  way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|secondary|tertiary)$"]{bbox(BIG)};
);
out geom;
""",
    "roads_minor": f"""
[out:json][timeout:300];
(
  way["highway"~"^(residential|unclassified|living_street|pedestrian)$"]{bbox(PARIS)};
);
out geom;
""",
    "green": f"""
[out:json][timeout:180];
(
  way["leisure"="park"]{bbox(BIG)};
  relation["leisure"="park"]{bbox(BIG)};
  way["leisure"="garden"]{bbox(PARIS)};
  relation["leisure"="garden"]{bbox(PARIS)};
  way["landuse"="forest"]{bbox(BIG)};
  relation["landuse"="forest"]{bbox(BIG)};
  way["natural"="wood"]{bbox(BIG)};
  relation["natural"="wood"]{bbox(BIG)};
  way["landuse"="cemetery"]{bbox(PARIS)};
  relation["landuse"="cemetery"]{bbox(PARIS)};
);
out geom;
""",
    "rail": f"""
[out:json][timeout:180];
(
  way["railway"="rail"]["usage"~"^(main|branch)$"]{bbox(BIG)};
);
out geom;
""",
    "admin": f"""
[out:json][timeout:120];
(
  relation["boundary"="administrative"]["admin_level"="8"]["name"="Paris"];
  way["highway"="motorway"]["ref"~"^BP"]{bbox(BIG)};
);
out geom;
""",
    "landmarks": f"""
[out:json][timeout:180];
(
  way["building"]["name"~"Notre-Dame de Paris|Louvre|Arc de Triomphe|Tour Eiffel|Sainte-Chapelle|Panthéon|Invalides|Sacré-Cœur|Opéra Garnier|Palais Garnier|Gare du Nord|Gare de l'Est|Gare de Lyon|Gare Saint-Lazare|Gare Montparnasse|Tour Montparnasse|Hôtel de Ville|Conciergerie|Bastille|Palais du Luxembourg|Grande Arche|Arènes de Lutèce|Saint-Germain-des-Prés|Saint-Eustache|Centre Pompidou|Palais de Chaillot|Musée d'Orsay|Grand Palais|Palais Bourbon|Saint-Sulpice|Saint-Denis"]{bbox(BIG)};
  relation["building"]["name"~"Notre-Dame de Paris|Louvre|Arc de Triomphe|Tour Eiffel|Sainte-Chapelle|Panthéon|Invalides|Sacré-Cœur|Opéra Garnier|Palais Garnier|Gare du Nord|Gare de l'Est|Gare de Lyon|Gare Saint-Lazare|Gare Montparnasse|Tour Montparnasse|Hôtel de Ville|Conciergerie|Palais du Luxembourg|Grande Arche|Arènes de Lutèce|Saint-Germain-des-Prés|Saint-Eustache|Centre Pompidou|Palais de Chaillot|Musée d'Orsay|Grand Palais|Palais Bourbon|Saint-Sulpice"]{bbox(BIG)};
);
out geom;
""",
}


def fetch(name, query):
    for ep in ENDPOINTS:
        for attempt in range(3):
            try:
                data = urllib.parse.urlencode({"data": query}).encode()
                req = urllib.request.Request(ep, data=data, headers={"User-Agent": "paris-replica/1.0"})
                t0 = time.time()
                with urllib.request.urlopen(req, timeout=400) as r:
                    payload = json.load(r)
                n = len(payload.get("elements", []))
                print(f"[{name}] {ep} -> {n} elements in {time.time()-t0:.1f}s", flush=True)
                return payload["elements"]
            except Exception as e:  # noqa
                print(f"[{name}] {ep} attempt {attempt} failed: {e}", flush=True)
                time.sleep(10 * (attempt + 1))
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
    print("layers:", {k: len(v) for k, v in result.items()})


if __name__ == "__main__":
    main()
