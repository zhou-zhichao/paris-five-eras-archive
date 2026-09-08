"""Frame-to-frame difference at water edges vs water interior vs land, for consecutive rendered frames.
usage: python flicker_metric.py dir [crop_out.png]
"""
import glob, sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

d = sys.argv[1]
fs = sorted(glob.glob(os.path.join(d, "frame_*.png")))[:3]
ims = [np.asarray(Image.open(f).convert("RGB")).astype(np.int16) for f in fs]
a = ims[0]
r, g, b = a[..., 0], a[..., 1], a[..., 2]
water = (b > g * 0.95) & (b > r + 15) & (g > r + 5)
water = ndimage.binary_opening(water, iterations=2)
edge = ndimage.binary_dilation(water, iterations=5) & ~ndimage.binary_erosion(water, iterations=5)
inner = ndimage.binary_erosion(water, iterations=8)
land = ~ndimage.binary_dilation(water, iterations=12)
for i in range(len(ims) - 1):
    diff = np.abs(ims[i] - ims[i + 1]).sum(axis=2)
    print(f"{os.path.basename(fs[i])} -> {os.path.basename(fs[i+1])}: edge {diff[edge].mean():.2f}  interior {diff[inner].mean():.2f}  land {diff[land].mean():.2f}  "
          f"edge px>60: {(diff[edge] > 60).mean()*100:.2f}%")
if len(sys.argv) > 2:
    diff = np.abs(ims[0] - ims[1]).sum(axis=2)
    lab, n = ndimage.label(water)
    best = None
    for k in range(1, n + 1):
        m = lab == k
        if m.sum() < 300 or m.sum() > 40000:
            continue
        e = ndimage.binary_dilation(m, iterations=5) & ~ndimage.binary_erosion(m, iterations=5)
        v = diff[e].mean()
        if best is None or v > best[0]:
            best = (v, ndimage.center_of_mass(m))
    cy, cx = int(best[1][0]), int(best[1][1])
    H, W = diff.shape
    y0, y1 = max(cy - 150, 0), min(cy + 150, H); x0, x1 = max(cx - 250, 0), min(cx + 250, W)
    sheet = Image.new("RGB", (3 * (x1 - x0) * 2, (y1 - y0) * 2))
    for i, im in enumerate(ims):
        c = Image.fromarray(im[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.NEAREST)
        sheet.paste(c, (i * (x1 - x0) * 2, 0))
    sheet.save(sys.argv[2])
    print("worst lake edge diff", round(best[0], 2), "at", (cx, cy), "->", sys.argv[2])
