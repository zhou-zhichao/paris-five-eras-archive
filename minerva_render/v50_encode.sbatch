#!/usr/bin/env bash
#SBATCH --job-name=paris-v50-encode
#SBATCH --partition=long
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/encode-%j.log
set -Eeuo pipefail
RUN_DIR=${PARIS_RUN_DIR:?}
FFMPEG=/data/users/zhichaoz/blender-render/runtime/ffmpeg/ffmpeg
FFPROBE=/data/users/zhichaoz/blender-render/runtime/ffmpeg/ffprobe
for ((frame=1;frame<=3600;frame++)); do
    printf -v filename '%s/frames/frame_%04d.png' "$RUN_DIR" "$frame"
    if [[ ! -s "$filename" ]]; then echo "Missing frame $frame" >&2; exit 1; fi
done
mkdir -p "$RUN_DIR/output"
"$FFMPEG" -hide_banner -nostdin -v warning -xerror -threads 8 -framerate 30 -start_number 1 \
    -i "$RUN_DIR/frames/frame_%04d.png" -frames:v 3600 -c:v libx264 -threads 8 -preset fast -crf 19 \
    -pix_fmt yuv420p -movflags +faststart -y "$RUN_DIR/output/paris_v50_720p.pending.mp4"
"$FFPROBE" -v error -count_frames -show_entries stream=width,height,r_frame_rate,nb_read_frames -show_entries format=duration,size \
    -of json "$RUN_DIR/output/paris_v50_720p.pending.mp4" > "$RUN_DIR/output/probe.json"
mv "$RUN_DIR/output/paris_v50_720p.pending.mp4" "$RUN_DIR/output/paris_v50_720p.mp4"
sha256sum "$RUN_DIR/output/paris_v50_720p.mp4" > "$RUN_DIR/output/sha256.txt"
echo ENCODE_COMPLETE
