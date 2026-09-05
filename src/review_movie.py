"""Validate a downloaded Minerva movie and extract individual comparison stills."""
from pathlib import Path
import hashlib
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MOVIE = ROOT / 'output/paris_reference_rebuild_1440p.mp4'
REVIEW = ROOT / 'review'
TIMES = [6, 24, 54, 80, 127, 165, 171, 173, 176]


def extract(path, seconds, destination):
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-ss', str(seconds), '-i', str(path), '-frames:v', '1',
        '-vf', 'scale=1280:-2', '-q:v', '2', str(destination),
    ], check=True)


def main():
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-count_frames', '-show_streams',
        '-show_format', '-of', 'json', str(MOVIE),
    ]))
    stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    assert (stream['width'], stream['height']) == (2560, 1440)
    assert stream['r_frame_rate'] == '30/1'
    assert int(stream['nb_read_frames']) == 5400
    assert abs(float(probe['format']['duration']) - 180) < 0.01
    expected = (ROOT / 'output/sha256.txt').read_text().split()[0].lower()
    with MOVIE.open('rb') as source:
        actual = hashlib.file_digest(source, 'sha256').hexdigest()
    assert actual == expected, (actual, expected)
    REVIEW.mkdir(exist_ok=True)
    font_path = Path('C:/Windows/Fonts/arial.ttf')
    font = ImageFont.truetype(str(font_path), 20) if font_path.exists() else ImageFont.load_default(size=20)
    sheet = Image.new('RGB', (1280, len(TIMES) * 394), '#171916')
    draw = ImageDraw.Draw(sheet)
    for row, seconds in enumerate(TIMES):
        y = row * 394
        for col, (source, prefix, label) in enumerate([
            (ROOT / 'reference/source.mp4', 'source', 'Reference'),
            (MOVIE, 'final', 'Blender rebuild'),
        ]):
            still = REVIEW / f'{prefix}-{seconds:03d}.jpg'
            extract(source, seconds, still)
            with Image.open(still) as picture:
                sheet.paste(picture.resize((640, 360)), (col * 640, y + 34))
            draw.text((col * 640 + 12, y + 6), f'{label} | {seconds}s', font=font, fill='white')
    sheet.save(REVIEW / 'final-comparison.jpg', quality=94)
    report = {
        'passed': True,
        'sha256': actual,
        'bytes': MOVIE.stat().st_size,
        'width': 2560,
        'height': 1440,
        'fps': 30,
        'decoded_frames': 5400,
        'duration_seconds': 180,
        'inspection_times': TIMES,
        'local_operation': 'decode validation and individual still extraction; no animation rendering',
    }
    (REVIEW / 'movie-validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
