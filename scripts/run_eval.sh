#!/usr/bin/env bash
# Runs the official challenge-track evaluation for one task against a websocket policy server.
#
#   scripts/run_eval.sh <task_name> [instance indices...]      (default indices: 0..9)
#
# Env overrides:
#   POLICY=zero          policy served by `python -m policy.serve` (set START_SERVER=0 to use your own)
#   PORT=8000
#   NUM_ENVS=1           1 = one instance at a time (low memory); N = run the listed instances in
#                        batches of N parallel envs (N must divide the number of indices)
#   CHUNK=0              --replay-action-chunk-size (only for open-loop chunked policies)
#   ROBOT_CONFIG=configs/r1pro.yaml
set -euo pipefail
source "$(dirname "$0")/env.sh"
activate_behavior

TASK="${1:?usage: run_eval.sh <task_name> [instance indices...]}"
shift
INDICES=("$@")
[ ${#INDICES[@]} -eq 0 ] && INDICES=(0 1 2 3 4 5 6 7 8 9)

POLICY="${POLICY:-zero}"
PORT="${PORT:-8000}"
NUM_ENVS="${NUM_ENVS:-1}"
CHUNK="${CHUNK:-0}"
START_SERVER="${START_SERVER:-1}"
ROBOT_CONFIG="${ROBOT_CONFIG:-$REPO_ROOT/configs/r1pro.yaml}"
OUT="$REPO_ROOT/outputs/eval/$TASK"
mkdir -p "$OUT"

if (( ${#INDICES[@]} % NUM_ENVS != 0 )); then
    echo "NUM_ENVS=$NUM_ENVS must divide the number of instance indices (${#INDICES[@]})" >&2
    exit 1
fi

if [ "$START_SERVER" = 1 ]; then
    echo ">> Starting policy server ($POLICY) on :$PORT, log: $OUT/server.log"
    (cd "$REPO_ROOT" && python -m policy.serve --policy "$POLICY" --port "$PORT" >"$OUT/server.log" 2>&1) &
    SERVER_PID=$!
    trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
fi

cd "$PATH_TO_BEHAVIOR_1K"
for ((i = 0; i < ${#INDICES[@]}; i += NUM_ENVS)); do
    batch=("${INDICES[@]:i:NUM_ENVS}")
    echo ">> $TASK: instances ${batch[*]}"
    python -m omnigibson.eval.eval \
        --task-name "$TASK" \
        --host 127.0.0.1 --port "$PORT" \
        --instance-indices "${batch[@]}" \
        --num-envs "$NUM_ENVS" \
        --num-rollouts 1 \
        --env-wrapper omnigibson.eval.wrappers.RGBDFullResWrapper \
        --robot-config "$ROBOT_CONFIG" \
        --replay-action-chunk-size "$CHUNK" \
        --output-dir "$OUT" \
        --write-video
done
echo ">> Results in $OUT/json, videos in $OUT/videos"
