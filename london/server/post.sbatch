#!/usr/bin/env bash
#SBATCH --job-name=london-post
#SBATCH --partition=long
#SBATCH --gres=gpu:L4:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=%x-%j.out

# 1) render the outro blueprint still  2) ffmpeg post (tilt-shift, vignette, titles, wipe, fades) -> mp4
set -Eeuo pipefail
umask 002
RUN_DIR=${PARIS_RUN_DIR:?PARIS_RUN_DIR is required}
BLENDER_ROOT=${BLENDER_ROOT:-/data/users/zhichaoz/blender-render/runtime/blender-4.5.10-linux-x64}
FFMPEG_ROOT=${FFMPEG_ROOT:-/data/users/zhichaoz/blender-render/runtime/ffmpeg}
FRAMES_DIR="$RUN_DIR/frames"
export LD_LIBRARY_PATH="$RUN_DIR/syslibs:${LD_LIBRARY_PATH:-}"
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export EGL_PLATFORM=surfaceless
export PATH="$FFMPEG_ROOT:$PATH"
export PARIS_RES_X=${PARIS_RES_X:-2560}
export PARIS_RES_Y=${PARIS_RES_Y:-1440}

n=$(find "$FRAMES_DIR" -maxdepth 1 -name 'frame_*.png' -size +50k | wc -l)
echo "FRAME_COUNT=$n"
if [[ "$n" -lt ${EXPECTED_FRAMES:-5880} ]]; then echo "not all frames rendered" >&2; exit 1; fi

if [[ ! -s "$FRAMES_DIR/blueprint.png" ]]; then
    "$BLENDER_ROOT/blender" --background "$RUN_DIR/input/${BLEND_NAME:-london_packed.blend}" -noaudio \
        --python "$RUN_DIR/scripts/render_blueprint.py" -- --out "$FRAMES_DIR/blueprint.png" --res "${PARIS_RES_X}x${PARIS_RES_Y}"
fi
mkdir -p "$RUN_DIR/output"
cd "$RUN_DIR/scripts"
python3 overlay.py --frames "$FRAMES_DIR" --out "$RUN_DIR/output/london_${PARIS_RES_Y}p.mp4" \
    --font "$RUN_DIR/fonts/bahnschrift.ttf" --preset slow --crf 17
ls -la "$RUN_DIR/output"
sha256sum "$RUN_DIR/output/"*.mp4
