#!/usr/bin/env bash
# Installs Miniforge (user-space), clones BEHAVIOR-1K at $B1K_TAG and runs its setup.sh
# non-interactively. Idempotent: re-running skips finished steps.
#
# Passing this script accepts the Conda ToS, the NVIDIA Omniverse EULA and the BEHAVIOR
# dataset license on your behalf; read them in BEHAVIOR-1K/setup.sh first.
set -euo pipefail
source "$(dirname "$0")/env.sh"

mkdir -p "$B1K_WORK"

if [ ! -x "$CONDA_ROOT/bin/conda" ]; then
    echo ">> Installing Miniforge into $CONDA_ROOT"
    installer="$B1K_WORK/miniforge.sh"
    curl -fsSL -o "$installer" \
        "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    bash "$installer" -b -p "$CONDA_ROOT"
    rm -f "$installer"
fi
# shellcheck disable=SC1091
source "$CONDA_ROOT/etc/profile.d/conda.sh"

if [ ! -d "$PATH_TO_BEHAVIOR_1K/.git" ]; then
    echo ">> Cloning BEHAVIOR-1K $B1K_TAG"
    git clone --depth 1 -b "$B1K_TAG" https://github.com/StanfordVL/BEHAVIOR-1K.git "$PATH_TO_BEHAVIOR_1K"
fi

# --- 1. Python env: Isaac Sim + OmniGibson + BDDL + JoyLo + eval extras -------------------------
# torch_cluster is the last thing setup.sh installs for --eval, so importing it together with
# isaacsim means the env build finished.
env_built() {
    conda env list | grep -q "^behavior " &&
        conda run -n behavior python -c "import isaacsim, torch_cluster" >/dev/null 2>&1
}

if env_built; then
    echo ">> conda env 'behavior' already built; skipping setup.sh"
else
    # A previous run may have died half-way; setup.sh refuses to reuse an existing env.
    if conda env list | grep -q "^behavior "; then
        echo ">> Removing incomplete conda env 'behavior' from a previous failed run"
        conda env remove -n behavior -y
    fi
    echo ">> Running BEHAVIOR-1K setup.sh (Isaac Sim + OmniGibson; this takes a while)"
    # --eval requires --joylo in upstream setup.sh. Assets are downloaded in step 3 instead of
    # via --dataset, because setup.sh's dataset step imports omnigibson before warp exists.
    (cd "$PATH_TO_BEHAVIOR_1K" && ./setup.sh --new-env --omnigibson --bddl --joylo --eval \
        --accept-conda-tos --accept-nvidia-eula)
fi

activate_behavior

# --- 2. warp ---------------------------------------------------------------------------------------
# OmniGibson imports warp at module level (utils/usd_utils.py, simulator.py), but at
# v3.9.3-post1 warp-lang is only declared in the [primitives] extra. Same pin as that extra.
if ! python -c "import warp" 2>/dev/null; then
    echo ">> Installing warp-lang (missing upstream dependency)"
    python -m pip install "warp-lang==1.12.0"
fi
python -c "import omnigibson" || { echo "ERROR: omnigibson still fails to import" >&2; exit 1; }

# --- 3. Assets (what setup.sh --dataset does) ----------------------------------------------------
ASSETS_MARKER="$B1K_WORK/.assets_done_$B1K_TAG"
if [ -f "$ASSETS_MARKER" ]; then
    echo ">> Assets already downloaded"
else
    echo ">> Downloading robot assets, BEHAVIOR-1K assets and 2026 challenge task instances"
    python -c "from omnigibson.utils.asset_utils import download_omnigibson_robot_assets; download_omnigibson_robot_assets()"
    python -c "from omnigibson.utils.asset_utils import download_behavior_1k_assets; download_behavior_1k_assets(accept_license=True)"
    python -c "from omnigibson.utils.asset_utils import download_2026_challenge_task_instances; download_2026_challenge_task_instances()"
    touch "$ASSETS_MARKER"
fi

echo ">> Done. Next: scripts/smoke_test.sh"
