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

if conda env list | grep -q "^behavior "; then
    echo ">> conda env 'behavior' already exists; skipping setup.sh"
    echo "   (to rebuild: conda env remove -n behavior && rerun)"
else
    echo ">> Running BEHAVIOR-1K setup.sh (Isaac Sim + OmniGibson + assets; this takes a while)"
    cd "$PATH_TO_BEHAVIOR_1K"
    ./setup.sh --new-env --omnigibson --bddl --eval --dataset \
        --accept-conda-tos --accept-nvidia-eula --accept-dataset-tos
fi

echo ">> Done. Next: scripts/smoke_test.sh"
