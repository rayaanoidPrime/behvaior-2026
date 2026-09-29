#!/usr/bin/env bash
# Checks whether this machine can run OmniGibson / Isaac Sim 5.1.
# Run this first on a fresh molab GPU session. Nothing here installs anything.
source "$(dirname "$0")/env.sh"

ok()   { echo "  [ok]   $*"; }
warn() { echo "  [WARN] $*"; }
bad()  { echo "  [FAIL] $*"; }

echo "== OS"
if [ -r /etc/os-release ]; then . /etc/os-release; echo "  $PRETTY_NAME"; fi
echo "  glibc: $(ldd --version 2>/dev/null | head -1)"

echo "== GPU"
if command -v nvidia-smi >/dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | sed 's/^/  /'
else
    bad "nvidia-smi not found: attach a GPU to the notebook (notebook specs button in molab header)"
fi
echo "  NVIDIA_DRIVER_CAPABILITIES=${NVIDIA_DRIVER_CAPABILITIES:-<unset>}"
case "${NVIDIA_DRIVER_CAPABILITIES:-}" in
    *all*|*graphics*) ok "container exposes graphics capability (needed for RTX rendering)" ;;
    *) warn "graphics capability not advertised; Isaac Sim rendering may fail without Vulkan" ;;
esac

echo "== Vulkan / GL driver libraries (Isaac Sim renders through Vulkan)"
found_icd=""
for f in /usr/share/vulkan/icd.d/nvidia_icd.json /etc/vulkan/icd.d/nvidia_icd.json /usr/share/glvnd/egl_vendor.d/10_nvidia.json; do
    [ -e "$f" ] && { ok "$f"; found_icd=1; }
done
[ -z "$found_icd" ] && warn "no NVIDIA Vulkan ICD json found"
if ldconfig -p 2>/dev/null | grep -q libGLX_nvidia; then ok "libGLX_nvidia present"; else warn "libGLX_nvidia not in ldconfig cache"; fi
if ldconfig -p 2>/dev/null | grep -q libnvidia-rtcore; then ok "libnvidia-rtcore present"; else warn "libnvidia-rtcore not found (RTX ray tracing)"; fi

echo "== Resources"
echo "  CPUs: $(nproc)"
free -g 2>/dev/null | awk 'NR<=2{print "  "$0}'
echo "  Disk for B1K_WORK ($B1K_WORK):"
mkdir -p "$B1K_WORK"
df -h "$B1K_WORK" | sed 's/^/  /'
avail_gb=$(df -BG --output=avail "$B1K_WORK" | tail -1 | tr -dc '0-9')
if [ "${avail_gb:-0}" -lt 100 ]; then
    warn "less than 100 GB free; Isaac Sim + BEHAVIOR assets + one task of demos need roughly 100 GB"
fi

echo "== Tooling"
for c in git curl conda uv sudo apt-get; do
    if command -v "$c" >/dev/null; then ok "$c: $(command -v "$c")"; else echo "  [--]   $c not found"; fi
done
if command -v sudo >/dev/null && sudo -n true 2>/dev/null; then ok "passwordless sudo"; else echo "  [--]   no passwordless sudo"; fi
