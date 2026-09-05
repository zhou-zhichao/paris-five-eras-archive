"""Extract reproducible, explicitly timed inspection frames from the sole source."""
from pathlib import Path
import subprocess
import io
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
times = [1, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 80, 90, 100, 110, 120, 127, 136, 144, 152, 160, 168, 171, 173, 176, 178]
sheet = Image.new('RGB', (4 * 512, 7 * 312), '#111111')
draw = ImageDraw.Draw(sheet)
for i, t in enumerate(times):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', str(ROOT / 'reference/source.mp4'), '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'])
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    im.save(ROOT / f'review/reference-{t:03d}.jpg', quality=96)
    sheet.paste(im.resize((512, 288)), ((i % 4) * 512, (i // 4) * 312))
    draw.text(((i % 4) * 512 + 10, (i // 4) * 312 + 291), f'{t:03d} seconds', fill='white')
sheet.save(ROOT / 'review/reference-timed.jpg', quality=95)
