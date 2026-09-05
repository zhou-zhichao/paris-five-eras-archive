#!/usr/bin/env bash
#SBATCH --job-name=reference-probe
#SBATCH --partition=long
#SBATCH --gres=gpu:L4:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH --output=logs/probe-%j.log
set -Eeuo pipefail
RUN_DIR=${REBUILD_RUN_DIR:?}
export LD_LIBRARY_PATH="$RUN_DIR/syslibs:${LD_LIBRARY_PATH:-}"
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export EGL_PLATFORM=surfaceless
export LD_PRELOAD="$RUN_DIR/egl_device_v2.so"
export PARIS_EGL_GPU=0
nvidia-smi -L
/data/users/zhichaoz/blender-render/runtime/blender-4.5.10-linux-x64/blender \
    -b "$RUN_DIR/paris_reference_rebuild.blend" -noaudio -t 8 --python-exit-code 1 \
    --python "$RUN_DIR/render_worker.py" -- --root "$RUN_DIR/probe" --frames 721 2401 4951 --width 1920 --samples 64
