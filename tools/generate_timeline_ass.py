import argparse
import math
from pathlib import Path


FPS = 30
TOTAL_FRAMES = 3600
YEAR_ANCHORS = [
    (1, -52),
    (150, -52),
    (825, 1259),
    (1500, 1700),
    (2175, 1850),
    (3600, 2025),
]
ERA_SEGMENTS = [
    (1, 149, "PARIS"),
    (150, 824, "ROMAN ERA"),
    (825, 1499, "MEDIEVAL PARIS"),
    (1500, 2174, "ROYAL PARIS"),
    (2175, 2849, "INDUSTRIAL PARIS"),
    (2850, 3600, "MODERN PARIS"),
]


def ass_time(frame):
    total_centiseconds = round((frame - 1) * 100 / FPS)
    hours, remainder = divmod(total_centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def interpolate_year(frame):
    for (start_frame, start_year), (end_frame, end_year) in zip(
        YEAR_ANCHORS, YEAR_ANCHORS[1:]
    ):
        if frame <= end_frame:
            span = max(1, end_frame - start_frame)
            progress = (frame - start_frame) / span
            return round(start_year + (end_year - start_year) * progress)
    return YEAR_ANCHORS[-1][1]


def format_year(year):
    if year < 0:
        return f"{abs(year)} BC"
    if year == 0:
        return "1"
    return str(year)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--step-frames", type=int, default=3)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Year,Arial,104,&H00FFFFFF,&H00FFFFFF,&H72000000,&H50000000,-1,0,0,0,100,100,-2,0,1,2.2,3,3,40,68,48,1
Style: Era,Arial,46,&H00FFFFFF,&H00FFFFFF,&H72000000,&H50000000,-1,0,0,0,100,100,5,0,1,1.5,2,1,64,40,56,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    events = []
    step = max(1, args.step_frames)
    for start_frame in range(1, TOTAL_FRAMES + 1, step):
        end_frame = min(TOTAL_FRAMES + 1, start_frame + step)
        year = format_year(interpolate_year(start_frame))
        events.append(
            f"Dialogue: 0,{ass_time(start_frame)},{ass_time(end_frame)},Year,,0,0,0,,{year}"
        )
    for start_frame, end_frame, label in ERA_SEGMENTS:
        events.append(
            "Dialogue: 0,"
            f"{ass_time(start_frame)},{ass_time(end_frame + 1)},Era,,0,0,0,,"
            f"{{\\fad(220,220)}}{label}"
        )

    args.output.write_text(header + "\n".join(events) + "\n", encoding="utf-8-sig")
    print(f"Wrote {len(events)} events to {args.output.resolve()}")


if __name__ == "__main__":
    main()
