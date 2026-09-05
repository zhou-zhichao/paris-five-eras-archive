#!/usr/bin/env bash
#SBATCH --job-name=reference-rebuild
#SBATCH --partition=long
#SBATCH --array=0-15%16
#SBATCH --gres=gpu:L4:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=logs/slurm-%A-%a.log
set -Eeuo pipefail
RUN_DIR=${REBUILD_RUN_DIR:?}
BLENDER=/data/users/zhichaoz/blender-render/runtime/blender-4.5.10-linux-x64/blender
export LD_LIBRARY_PATH="$RUN_DIR/syslibs:${LD_LIBRARY_PATH:-}"
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export EGL_PLATFORM=surfaceless
export LD_PRELOAD="$RUN_DIR/egl_device_v2.so"
export PARIS_EGL_GPU=0
export OMP_NUM_THREADS=8
mkdir -p "$RUN_DIR/tmp/worker-${SLURM_ARRAY_TASK_ID}" "$RUN_DIR/frames" "$RUN_DIR/logs"
export TMPDIR="$RUN_DIR/tmp/worker-${SLURM_ARRAY_TASK_ID}"
nvidia-smi -L
"$BLENDER" -b "$RUN_DIR/paris_reference_rebuild.blend" -noaudio -t 8 --python-exit-code 1 \
    --python "$RUN_DIR/render_worker.py" -- --root "$RUN_DIR" --worker "$SLURM_ARRAY_TASK_ID" --workers 16 --width 2560 --samples 64
