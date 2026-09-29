#!/usr/bin/env bash
# Downloads the LeRobot v3 demos for one or more tasks (the full dataset is 3.27 TB).
#
#   scripts/download_demos.sh turning_on_radio [more task names...]
set -euo pipefail
source "$(dirname "$0")/env.sh"
[ $# -ge 1 ] || { echo "usage: download_demos.sh <task_name> [...]" >&2; exit 1; }

HF="${HF:-hf}"
command -v "$HF" >/dev/null || { echo "Install the HF CLI first: pip install -U 'huggingface_hub[cli]'" >&2; exit 1; }

mkdir -p "$DATA_ROOT"
"$HF" download "$REPO_ID" --repo-type dataset --local-dir "$DATA_ROOT" \
    --include "meta/info.json" --include "meta/stats.json" \
    --include "meta/tasks.parquet" --include "meta/tasks.jsonl"

for task in "$@"; do
    # task_index doubles as the chunk index (chunk-000 is task 0, ...).
    idx=$(python3 - "$DATA_ROOT/meta/tasks.jsonl" "$task" <<'EOF'
import json, sys
for line in open(sys.argv[1]):
    row = json.loads(line)
    if row["task_name"] == sys.argv[2]:
        print(row["task_index"]); break
else:
    sys.exit(f"unknown task {sys.argv[2]!r}")
EOF
)
    chunk=$(printf "chunk-%03d" "$idx")
    ann=$(printf "task-%04d" "$idx")
    echo ">> $task -> $chunk"
    "$HF" download "$REPO_ID" --repo-type dataset --local-dir "$DATA_ROOT" \
        --include "data/$chunk/**" \
        --include "meta/episodes/$chunk/**" \
        --include "videos/*/$chunk/**" \
        --include "annotations/$ann/**"
done
