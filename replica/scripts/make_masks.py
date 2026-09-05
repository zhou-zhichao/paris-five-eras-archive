"""Write the tilt-shift focus mask and vignette mask PNGs for a given size (needs numpy + PIL).
usage: python make_masks.py out_dir 2560 1440
"""
import os, sys
import numpy as np
from PIL import Image


def write_masks(out_dir, W, H):
    yy, xx = np.mgrid[0:H, 0:W]
    v = yy / (H - 1); u = xx / (W - 1)
    focus = np.clip((np.abs(v - 0.47) - 0.16) / 0.30, 0, 1) ** 1.4
    Image.fromarray((focus * 255).astype(np.uint8)).save(os.path.join(out_dir, "mask_focus.png"))
    r = np.sqrt(((u - 0.5) * 1.15) ** 2 + ((v - 0.5) * 1.35) ** 2)
    vig = 1.0 - 0.42 * np.clip((r - 0.45) / 0.55, 0, 1) ** 1.5
    Image.fromarray((vig * 255).astype(np.uint8)).convert("RGB").save(os.path.join(out_dir, "mask_vignette.png"))


if __name__ == "__main__":
    d, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    os.makedirs(d, exist_ok=True)
    write_masks(d, W, H)
    print("masks written", d, W, H)
