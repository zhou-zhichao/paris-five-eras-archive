#!/usr/bin/env bash
#SBATCH --job-name=reference-encode
#SBATCH --partition=long
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=12G
#SBATCH --time=02:00:00
#SBATCH --output=logs/encode-%j.log
set -Eeuo pipefail
RUN_DIR=${REBUILD_RUN_DIR:?}
FFMPEG=/data/users/zhichaoz/blender-render/runtime/ffmpeg/ffmpeg
FFPROBE=/data/users/zhichaoz/blender-render/runtime/ffmpeg/ffprobe
for ((frame=1;frame<=5400;frame++)); do
    printf -v name '%s/frames/frame_%05d.png' "$RUN_DIR" "$frame"
    if [[ ! -s "$name" ]]; then echo "Missing frame $frame" >&2; exit 1; fi
done
mkdir -p "$RUN_DIR/output"
GRADE="eq=gamma='0.86-0.12*clip((t-30)/110,0,1)':gamma_g='1-0.06*clip((t-30)/110,0,1)':gamma_b='0.96-0.05*clip((t-30)/110,0,1)':eval=frame,vignette=PI/8"
"$FFMPEG" -hide_banner -nostdin -v warning -xerror -progress "$RUN_DIR/logs/encode-progress.txt" -stats_period 10 -threads 12 -framerate 30 -start_number 1 \
    -i "$RUN_DIR/frames/frame_%05d.png" -vf "$GRADE" -frames:v 5400 -c:v libx264 -threads 12 -preset slow -crf 18 \
    -pix_fmt yuv420p -movflags +faststart -y "$RUN_DIR/output/paris_reference_rebuild_1440p.pending.mp4"
"$FFPROBE" -v error -count_frames -show_entries stream=width,height,r_frame_rate,nb_read_frames -show_entries format=duration,size \
    -of json "$RUN_DIR/output/paris_reference_rebuild_1440p.pending.mp4" > "$RUN_DIR/output/video-probe.json"
python3 - "$RUN_DIR/output/video-probe.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]));s=p['streams'][0]
assert (s['width'],s['height'],s['r_frame_rate'],int(s['nb_read_frames']))==(2560,1440,'30/1',5400),p
assert abs(float(p['format']['duration'])-180)<.01,p
PY
"$FFMPEG" -hide_banner -nostdin -v error -xerror -i "$RUN_DIR/output/paris_reference_rebuild_1440p.pending.mp4" -f null -
mv "$RUN_DIR/output/paris_reference_rebuild_1440p.pending.mp4" "$RUN_DIR/output/paris_reference_rebuild_1440p.mp4"
sha256sum "$RUN_DIR/output/paris_reference_rebuild_1440p.mp4" > "$RUN_DIR/output/sha256.txt"
echo ENCODE_AND_DECODE_CHECK_COMPLETE
