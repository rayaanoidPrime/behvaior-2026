#!/usr/bin/env bash
# Loads one task in the simulator with the evaluator's built-in zero-action policy (no server).
# If this works, Isaac Sim rendering works on this machine. First launch compiles shaders (~5 min),
# and scene loading takes another 2-5 min.
set -euo pipefail
source "$(dirname "$0")/env.sh"
activate_behavior

TASK="${1:-turning_on_radio}"
cd "$PATH_TO_BEHAVIOR_1K"
python -m omnigibson.eval.eval \
    --task-name "$TASK" \
    --policy local \
    --instance-indices 0 \
    --max-steps 50 \
    --output-dir "$REPO_ROOT/outputs/smoke/$TASK" \
    --write-video
echo ">> Smoke test finished; see $REPO_ROOT/outputs/smoke/$TASK"
