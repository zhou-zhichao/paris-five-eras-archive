"""Side-by-side sheet: reference video frame vs our render at the same timestamps.

usage: python compare.py renders/preview1 out.png [t1,t2,...]
Picks the rendered frame closest to each timestamp.
"""
import glob, os, re, subprocess, sys
from PIL import Image, ImageDraw

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "reference", "PARIS-original-IFhKB5zHWFg.mp4")
d = sys.argv[1]; out = sys.argv[2]
ts = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [10, 22, 46, 61, 85, 111, 141, 166]
files = sorted(glob.glob(os.path.join(d, "frame_*.png")))
frames = {int(re.search(r"frame_(\d+)", f).group(1)): f for f in files}
tmp = os.path.join(d, "_ref_tmp.png")
W, H = 640, 360
sheet = Image.new("RGB", (2 * W, len(ts) * H), "black")
dr = ImageDraw.Draw(sheet)
for i, t in enumerate(ts):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(t), "-i", REF, "-frames:v", "1", "-y", tmp], check=True)
    ref = Image.open(tmp).convert("RGB").resize((W, H))
    target = t * 30 + 1
    f = min(frames, key=lambda k: abs(k - target))
    mine = Image.open(frames[f]).convert("RGB").resize((W, H))
    sheet.paste(ref, (0, i * H)); sheet.paste(mine, (W, i * H))
    dr.text((4, i * H + 4), f"ref t={t}s", fill="yellow"); dr.text((W + 4, i * H + 4), f"ours frame {f} (t={(f-1)/30:.1f}s)", fill="yellow")
sheet.save(out)
print("saved", out)
