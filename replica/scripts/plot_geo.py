"""Quick PIL map of geo.json for visual QA.  usage: python plot_geo.py out.png [half_extent_m]"""
import json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
geo = json.load(open(os.path.join(HERE, "..", "data", "geo.json"), encoding="utf-8"))
out = sys.argv[1]
ext = float(sys.argv[2]) if len(sys.argv) > 2 else 14000
W = 2400
scale = W / (2 * ext)
im = Image.new("RGB", (W, int(W * 0.7)), (120, 140, 80))
H = im.size[1]
d = ImageDraw.Draw(im)


def P(x, y):
    return (W / 2 + x * scale, H / 2 - y * scale)


for g in geo["green"]:
    col = (60, 90, 40) if g["kind"] == "forest" else ((90, 150, 60) if g["kind"] == "park" else (80, 110, 60))
    d.polygon([P(*p) for p in g["outer"]], fill=col)
for w in geo["water"]:
    d.polygon([P(*p) for p in w["outer"]], fill=(70, 130, 140))
    for h in w["holes"]:
        d.polygon([P(*p) for p in h], fill=(120, 140, 80))
for c in geo["canals"]:
    d.line([P(*p) for p in c["pts"]], fill=(70, 130, 140), width=2)
wid = {"motorway": 4, "trunk": 3, "primary": 3, "secondary": 2, "tertiary": 1, "residential": 1, "unclassified": 1, "living_street": 1, "pedestrian": 1}
for r in geo["roads"]:
    col = (240, 230, 200) if r["cls"] in ("motorway", "trunk", "primary", "secondary") else (200, 195, 170)
    d.line([P(*p) for p in r["pts"]], fill=col, width=wid.get(r["cls"], 1))
for r in geo["rail"]:
    d.line([P(*p) for p in r["pts"]], fill=(60, 60, 60), width=1)
if geo.get("paris"):
    d.line([P(*p) for p in geo["paris"]["outer"]], fill=(255, 0, 0), width=3)
for l in geo["landmarks"]:
    x, y = P(l["x"], l["y"])
    d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 255, 0))
d.ellipse([W / 2 - 6, H / 2 - 6, W / 2 + 6, H / 2 + 6], fill=(255, 0, 255))
im.save(out)
print("saved", out)
