#!/usr/bin/env bash
#SBATCH --job-name=paris-v50-720
#SBATCH --partition=long
#SBATCH --array=0-3%4
#SBATCH --gres=gpu:L4:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=logs/array-%A-%a.log
set -Eeuo pipefail
RUN_DIR=${PARIS_RUN_DIR:?}
BLENDER=/data/users/zhichaoz/blender-render/runtime/blender-4.5.10-linux-x64/blender
export LD_LIBRARY_PATH="$RUN_DIR/syslibs:${LD_LIBRARY_PATH:-}"
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export EGL_PLATFORM=surfaceless
export OMP_NUM_THREADS=4
mkdir -p "$RUN_DIR/frames" "$RUN_DIR/tmp"
nvidia-smi -L
pids=()
for ((worker=0;worker<4;worker++)); do
    index=$((SLURM_ARRAY_TASK_ID*4+worker))
    start=$((index+1))
    mkdir -p "$RUN_DIR/tmp/worker-$index"
    (
      export TMPDIR="$RUN_DIR/tmp/worker-$index"
      export LD_PRELOAD="$RUN_DIR/egl_device_v2.so"
      export PARIS_EGL_GPU=0
      "$BLENDER" -b "$RUN_DIR/input/paris_v50_woodland.blend" -noaudio -t 4 --python-exit-code 1 \
        --python "$RUN_DIR/worker_v50.py" -- --worker "$index" > "$RUN_DIR/logs/worker-${SLURM_ARRAY_JOB_ID}-$index.log" 2>&1
    ) &
    pids+=("$!")
done
status=0
for pid in "${pids[@]}"; do wait "$pid" || status=1; done
exit "$status"
