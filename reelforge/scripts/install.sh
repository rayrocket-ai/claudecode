#!/usr/bin/env bash
# ReelForge toolchain installer.
#
# Installs everything the editing pipeline needs, on Debian/Ubuntu (the Hetzner
# case) or macOS. Idempotent -- safe to re-run after a partial failure.
#
# This installs *tools*. For server mode (inbox watcher, systemd, Syncthing,
# Tailscale) run scripts/server-setup.sh afterwards.

set -euo pipefail

REELFORGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${REELFORGE_VENV:-$REELFORGE_DIR/.venv}"

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# --- platform ---------------------------------------------------------------

case "$(uname -s)" in
  Linux)  PLATFORM=linux ;;
  Darwin) PLATFORM=macos ;;
  *) die "unsupported platform: $(uname -s)" ;;
esac

if [ "$PLATFORM" = linux ]; then
  have apt-get || die "only Debian/Ubuntu is supported on Linux (no apt-get found)"
  SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO="sudo"
fi

# --- system packages --------------------------------------------------------

log "Installing system packages ($PLATFORM)"

if [ "$PLATFORM" = linux ]; then
  export DEBIAN_FRONTEND=noninteractive
  $SUDO apt-get update -qq
  $SUDO apt-get install -y --no-install-recommends \
    ffmpeg \
    python3 python3-venv python3-pip \
    fonts-noto-color-emoji fonts-inter \
    libgl1 libglib2.0-0 \
    git curl tmux
else
  have brew || die "Homebrew required on macOS: https://brew.sh"
  brew install ffmpeg python@3.12 tmux git || true
  brew install --cask font-inter || warn "Inter font not installed; captions fall back to a system sans"
fi

have ffmpeg  || die "ffmpeg still missing after install"
have ffprobe || die "ffprobe still missing after install"
log "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')"

# --- node (Remotion premium overlays) --------------------------------------
# Optional: the fast render path never touches Node. Only the premium overlay
# tier needs it, so a missing Node degrades rather than blocks.

if have node; then
  NODE_MAJOR="$(node --version | sed 's/^v\([0-9]*\).*/\1/')"
  if [ "$NODE_MAJOR" -lt 20 ]; then
    warn "node $(node --version) is old; Remotion needs 20+. Premium overlays disabled."
  else
    log "node $(node --version)"
  fi
else
  warn "node not found -- Remotion premium overlays will be unavailable."
  warn "Install Node 22+ and re-run to enable them."
fi

# --- python environment -----------------------------------------------------

log "Creating virtualenv at $VENV"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

python -m pip install --quiet --upgrade pip wheel

log "Installing Python dependencies (this pulls PyTorch; expect a few minutes)"
pip install --quiet -r "$REELFORGE_DIR/requirements.txt"

# --- whisper model warm-up --------------------------------------------------
# Pull the model now rather than on the first real edit, so the first video the
# watcher sees is not also a several-hundred-megabyte download.

MODEL="$(python "$REELFORGE_DIR/core/hardware.py" | python -c 'import json,sys; print(json.load(sys.stdin)["profile"]["whisper_model"])')"
log "Pre-downloading whisper model: $MODEL"
python - <<PY || warn "model pre-download failed; it will download on first use"
from faster_whisper import WhisperModel
WhisperModel("$MODEL", device="cpu", compute_type="int8")
print("model cached")
PY

# --- emoji pack -------------------------------------------------------------

if [ -f "$REELFORGE_DIR/scripts/build-emoji-pack.py" ]; then
  log "Rasterising emoji overlay pack"
  python "$REELFORGE_DIR/scripts/build-emoji-pack.py" || \
    warn "emoji pack build failed; emoji overlays unavailable until fixed"
fi

# --- report -----------------------------------------------------------------

log "Environment check"
python "$REELFORGE_DIR/core/hardware.py"

cat <<EOF

ReelForge toolchain installed.

  Activate:  source $VENV/bin/activate
  Verify:    /reel-doctor   (from Claude Code)

Next, for server mode on the Hetzner box:
  $REELFORGE_DIR/scripts/server-setup.sh
EOF
