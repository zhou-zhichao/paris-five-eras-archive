"""Post: tilt-shift blur, vignette, era label + year counter, fades; encode MP4.

usage: python overlay.py --frames renders/final --out renders/paris_replica.mp4 [--fps 30]
Frames are named frame_%05d.png.  If frames were rendered with a step (preview),
each frame is held for `step` frames so the preview plays at real speed.
"""
import argparse, glob, os, re, struct, subprocess, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline


def png_size(path):
    """(width, height) of a PNG without PIL."""
    with open(path, "rb") as fh:
        head = fh.read(24)
    w, h = struct.unpack(">II", head[16:24])
    return w, h

ap = argparse.ArgumentParser()
ap.add_argument("--frames", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--font", default="C:/Windows/Fonts/bahnschrift.ttf")
ap.add_argument("--crf", type=int, default=18)
ap.add_argument("--blur", type=float, default=0.0055, help="tilt-shift blur sigma as fraction of height")
ap.add_argument("--no-text", action="store_true")
ap.add_argument("--t", type=float, default=0, help="limit output duration (seconds) for quick tests")
ap.add_argument("--preset", default="slow")
a = ap.parse_args()

files = sorted(glob.glob(os.path.join(a.frames, "frame_*.png")))
frames = [int(re.search(r"frame_(\d+)", f).group(1)) for f in files]
if not frames:
    raise SystemExit("no frames")
step = (frames[1] - frames[0]) if len(frames) > 1 else 1
W, H = png_size(files[0])
print("frames", len(frames), "step", step, "size", W, H)

# ---------------------------------------------------------------- masks (focus band + vignette)
# Pre-made masks of the right size are used if present (render servers without numpy/PIL);
# otherwise they are generated here.
mf, mv = os.path.join(a.frames, "mask_focus.png"), os.path.join(a.frames, "mask_vignette.png")
if not (os.path.exists(mf) and os.path.exists(mv) and png_size(mf) == (W, H)):
    from make_masks import write_masks
    write_masks(a.frames, W, H)

# ---------------------------------------------------------------- ASS subtitles
scale = H / 1440.0


def ts(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Year,Bahnschrift,{int(150*scale)},&H00FFFFFF,&H000000FF,&H60000000,&H80000000,1,0,0,0,86,100,{int(10*scale)},0,1,0,{int(3*scale)},3,{int(60*scale)},{int(90*scale)},{int(60*scale)},1
Style: Era,Bahnschrift,{int(60*scale)},&H00F2F2F2,&H000000FF,&H60000000,&H80000000,0,0,0,0,86,100,{int(4*scale)},0,1,0,{int(2*scale)},1,{int(100*scale)},{int(60*scale)},{int(72*scale)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
lines = []
dt = step / a.fps
for i, f in enumerate(frames):
    t = (f - 1) / a.fps
    if t > timeline.OUTRO_START + 1.5:
        continue
    y = timeline.year_at(min(t, timeline.OUTRO_START))
    yi = int(round(y))
    txt = f"- {abs(yi)}" if yi < 0 else f"{yi}"
    lines.append(f"Dialogue: 1,{ts(i*dt)},{ts((i+1)*dt)},Year,,0,0,0,,{txt}")
era_spans = []
cur = None
for i, f in enumerate(frames):
    t = (f - 1) / a.fps
    if t > timeline.OUTRO_START + 1.5:
        break
    e = timeline.era_at(timeline.year_at(t))
    if e != cur:
        era_spans.append([e, i, i]); cur = e
    else:
        era_spans[-1][2] = i
for e, i0, i1 in era_spans:
    lines.append(f"Dialogue: 0,{ts(i0*dt)},{ts((i1+1)*dt)},Era,,0,0,0,,{{\\fad(700,700)}}{e}")
ass_path = os.path.join(a.frames, "overlay.ass")
open(ass_path, "w", encoding="utf-8").write(header + "\n".join(lines) + "\n")

# ---------------------------------------------------------------- concat list (handles stepped previews)
lst = os.path.join(a.frames, "list.txt")
with open(lst, "w", encoding="utf-8") as fh:
    for f in files:
        fh.write(f"file '{os.path.abspath(f).replace(chr(92), '/')}'\nduration {dt:.6f}\n")
    fh.write(f"file '{os.path.abspath(files[-1]).replace(chr(92), '/')}'\n")

fontsdir = os.path.dirname(a.font).replace("\\", "/").replace(":", "\\:")
ass_ff = ass_path.replace("\\", "/").replace(":", "\\:")
total = len(frames) * dt
sigma = max(1.0, a.blur * H)
blueprint = os.path.join(a.frames, "blueprint.png")
use_outro = os.path.exists(blueprint) and total > timeline.OUTRO_START + 2
WIPE = 4.0
end_t = timeline.DURATION if use_outro else total


def post(src, dst, text, m1, m2):
    """tilt-shift + vignette (+ subtitles) chain for stream label src -> dst (m1/m2: mask stream labels)"""
    s = (f"[{src}]fps={a.fps},format=gbrp,split[{dst}a][{dst}b];[{dst}b]gblur=sigma={sigma:.2f}:steps=2[{dst}bl];"
         f"[{dst}a][{dst}bl][{m1}]maskedmerge[{dst}ts];[{dst}ts][{m2}]blend=all_mode=multiply:all_opacity=1[{dst}vg];"
         f"[{dst}vg]format=yuv420p")
    if text and not a.no_text:
        s += f",subtitles='{ass_ff}':fontsdir='{fontsdir}'"
    return s + f"[{dst}]"


inputs = ["-f", "concat", "-safe", "0", "-i", lst,
          "-loop", "1", "-framerate", str(a.fps), "-i", os.path.join(a.frames, "mask_focus.png"),
          "-loop", "1", "-framerate", str(a.fps), "-i", os.path.join(a.frames, "mask_vignette.png")]
if use_outro:
    fc = "[1:v]format=gbrp,split[m1a][m1b];[2:v]format=gbrp,split[m2a][m2b];"
    fc += post("0:v", "va", True, "m1a", "m2a")
    inputs += ["-loop", "1", "-framerate", str(a.fps), "-t", f"{end_t - timeline.OUTRO_START + 1:.2f}", "-i", blueprint]
    fc += ";" + post("3:v", "vb", False, "m1b", "m2b")
    fc += f";[va][vb]xfade=transition=smoothleft:duration={WIPE}:offset={timeline.OUTRO_START:.2f}[vx]"
    last = "vx"
else:
    fc = "[1:v]format=gbrp[m1a];[2:v]format=gbrp[m2a];" + post("0:v", "va", True, "m1a", "m2a")
    last = "va"
fc += f";[{last}]fade=t=in:st=0:d={timeline.FADE_IN_END},fade=t=out:st={max(0.0, end_t-2.5):.2f}:d=2.5,trim=duration={end_t:.2f}[out]"
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"] + inputs + [
       "-filter_complex", fc, "-map", "[out]"] + (["-t", str(a.t)] if a.t > 0 else []) + [
       "-r", str(a.fps), "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf), "-pix_fmt", "yuv420p", a.out]
print(" ".join(cmd))
subprocess.run(cmd, check=True)
print("wrote", a.out)
