#!/usr/bin/env bash
#SBATCH --job-name=london-timelapse
#SBATCH --partition=long
#SBATCH --array=0-7%8
#SBATCH --gres=gpu:L4:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=120G
#SBATCH --time=23:00:00
#SBATCH --output=%x-%A-%a.out

# Renders frames of the Paris replica with several Blender workers per GPU.
# Each worker renders frames start, start+TOTAL_WORKERS, ... (Blender -j stride).
set -Eeuo pipefail
umask 002

RUN_DIR=${PARIS_RUN_DIR:?PARIS_RUN_DIR is required}
BLENDER_ROOT=${BLENDER_ROOT:-/data/users/zhichaoz/blender-render/runtime/blender-4.5.10-linux-x64}
BLEND_FILE="$RUN_DIR/input/${BLEND_NAME:-london_packed.blend}"
CONFIG_SCRIPT="$RUN_DIR/configure_final.py"
FRAMES_DIR="$RUN_DIR/frames"
TASK_LOG_DIR="$RUN_DIR/logs/task-${SLURM_ARRAY_JOB_ID}-${SLURM_ARRAY_TASK_ID}"
TASK_TMP_DIR="$RUN_DIR/tmp/task-${SLURM_ARRAY_JOB_ID}-${SLURM_ARRAY_TASK_ID}"
WORKERS_PER_GPU=${WORKERS_PER_GPU:-4}
ARRAY_TASKS=${ARRAY_TASKS:-8}
TOTAL_WORKERS=$((WORKERS_PER_GPU * ARRAY_TASKS))
FIRST_FRAME=${FIRST_FRAME:-1}
FINAL_FRAME=${FINAL_FRAME:-5400}
MIN_FRAME_BYTES=50000

export LD_LIBRARY_PATH="$RUN_DIR/syslibs:${LD_LIBRARY_PATH:-}"
export __GLX_VENDOR_LIBRARY_NAME=nvidia
# The L4 nodes have no cgroup device isolation and Blender's headless EGL always initialises the first GPU it can
# open, so without this every worker of every task on a node piles onto GPU 0.  The shim hides the other
# /dev/nvidiaN nodes so each task really uses the GPU Slurm gave it (tools/gpufilter.c, 2026-09-10).
export LD_PRELOAD=${GPU_FILTER_SO:-/data/users/zhichaoz/blender-render/tools/gpufilter.so}
export GPU_ALLOW=${CUDA_VISIBLE_DEVICES:-0}
export EGL_PLATFORM=surfaceless
export OMP_NUM_THREADS=6
export PARIS_RES_X=${PARIS_RES_X:-2560}
export PARIS_RES_Y=${PARIS_RES_Y:-1440}
export PARIS_SAMPLES=${PARIS_SAMPLES:-32}

mkdir -p "$FRAMES_DIR" "$TASK_LOG_DIR" "$TASK_TMP_DIR"
echo "RENDER_TASK_START_EPOCH=$(date +%s) task=$SLURM_ARRAY_TASK_ID host=$(hostname) gpu=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L || true

worker_pids=()
for ((w = 0; w < WORKERS_PER_GPU; w++)); do
    g=$((SLURM_ARRAY_TASK_ID * WORKERS_PER_GPU + w))
    start=$((FIRST_FRAME + g))
    wtmp="$TASK_TMP_DIR/worker-$g"; mkdir -p "$wtmp"
    (
        export TMPDIR="$wtmp"
        "$BLENDER_ROOT/blender" --background "$BLEND_FILE" -noaudio \
            --python "$CONFIG_SCRIPT" -t 6 \
            -o "$FRAMES_DIR/frame_#####" -F PNG \
            -s "$start" -e "$FINAL_FRAME" -j "$TOTAL_WORKERS" -a \
            > "$TASK_LOG_DIR/worker-$g.log" 2>&1
    ) &
    worker_pids+=("$!")
done
status=0
for pid in "${worker_pids[@]}"; do wait "$pid" || status=1; done

missing=0; done_frames=0
for ((w = 0; w < WORKERS_PER_GPU; w++)); do
    g=$((SLURM_ARRAY_TASK_ID * WORKERS_PER_GPU + w))
    for ((f = FIRST_FRAME + g; f <= FINAL_FRAME; f += TOTAL_WORKERS)); do
        p=$(printf '%s/frame_%05d.png' "$FRAMES_DIR" "$f")
        b=0; [[ -f "$p" ]] && b=$(stat -c %s "$p")
        if ((b <= MIN_FRAME_BYTES)); then echo "MISSING_FRAME=$f"; missing=$((missing+1)); else done_frames=$((done_frames+1)); fi
    done
done
echo "RENDER_TASK_FRAMES=$done_frames RENDER_TASK_MISSING=$missing RENDER_TASK_END_EPOCH=$(date +%s)"
[[ $status -eq 0 && $missing -eq 0 ]]
