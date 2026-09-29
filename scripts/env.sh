# Shared settings. Source this file; override any variable by exporting it first.
# Everything heavy (conda, Isaac Sim, BEHAVIOR assets, demos) lives under B1K_WORK, outside git.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO_ROOT

# The challenge docs say "v3.9.3", but upstream only has v3.9.3-post1 (released 2026-09-29).
export B1K_TAG="${B1K_TAG:-v3.9.3-post1}"
export B1K_WORK="${B1K_WORK:-$HOME/b1k}"
export PATH_TO_BEHAVIOR_1K="${PATH_TO_BEHAVIOR_1K:-$B1K_WORK/BEHAVIOR-1K}"
export CONDA_ROOT="${CONDA_ROOT:-$B1K_WORK/miniforge3}"
export DATA_ROOT="${DATA_ROOT:-$B1K_WORK/2026-challenge-demos}"
export REPO_ID="behavior-1k/2026-challenge-demos"
export OMNI_KIT_ACCEPT_EULA=YES

activate_behavior() {
    # shellcheck disable=SC1091
    source "$CONDA_ROOT/etc/profile.d/conda.sh"
    # Activation hooks may read unset variables; don't let callers' `set -u` abort on them.
    local restore_u=0
    [[ $- == *u* ]] && restore_u=1 && set +u
    conda activate behavior
    [ "$restore_u" = 1 ] && set -u
    return 0
}
