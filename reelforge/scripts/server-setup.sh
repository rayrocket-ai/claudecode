#!/usr/bin/env bash
# ReelForge server mode.
#
# Turns a Debian/Ubuntu box (a Hetzner dedicated or cloud instance) into an
# always-on editing machine you can reach from anywhere:
#
#   inbox/  ->  watcher pre-warms transcription + analysis, unattended
#   tmux    ->  a persistent Claude Code session you can attach from any device
#   outbox/ ->  finished renders, synced back to your phone
#
# Run scripts/install.sh first. Run this as your normal user, not as root --
# the systemd units are user-scoped on purpose so nothing here needs to run
# privileged once the packages are in.

set -euo pipefail

REELFORGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="${REELFORGE_ROOT:-$HOME/reelforge}"
TMUX_SESSION="${REELFORGE_TMUX:-reelforge}"

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

[ "$(id -u)" -eq 0 ] && die "run as your normal user, not root"
have systemctl || die "systemd required for server mode"
have ffmpeg || die "run scripts/install.sh first"
SUDO="sudo"; have sudo || SUDO=""

# --- directory tree ---------------------------------------------------------

log "Creating $ROOT"
mkdir -p "$ROOT"/{inbox,outbox,.cache,memory,beds}

# The engine lives in the repo; the working tree lives in $ROOT. Link them so
# systemd units and Syncthing both have one stable path to point at.
if [ "$REELFORGE_DIR" != "$ROOT/engine" ]; then
  ln -sfn "$REELFORGE_DIR" "$ROOT/engine"
fi
for f in .venv config.toml server core scripts; do
  [ -e "$ROOT/$f" ] || ln -sfn "$REELFORGE_DIR/$f" "$ROOT/$f" 2>/dev/null || true
done

[ -f "$ROOT/config.toml" ] || cp "$REELFORGE_DIR/config.example.toml" "$REELFORGE_DIR/config.toml"

# memory/ is the only irreplaceable thing here. Seed it, never clobber it.
if [ ! -f "$ROOT/memory/playbook.md" ]; then
  cat > "$ROOT/memory/playbook.md" <<'EOF'
# Playbook

Rules the composer applies at render time. Each entry records where it came
from, so a rule you no longer agree with can be traced back and removed.

This file starts empty on purpose. It fills in as you use `/reel-feedback` --
anything you say twice becomes a rule here. Editing it by hand is fine.
EOF
fi
touch "$ROOT/memory/decisions.jsonl"

# --- syncthing --------------------------------------------------------------

if have syncthing; then
  log "Syncthing already installed"
else
  log "Installing Syncthing"
  $SUDO mkdir -p /etc/apt/keyrings
  curl -fsSL https://syncthing.net/release-key.gpg | \
    $SUDO tee /etc/apt/keyrings/syncthing.gpg >/dev/null
  echo "deb [signed-by=/etc/apt/keyrings/syncthing.gpg] https://apt.syncthing.net/ syncthing stable" | \
    $SUDO tee /etc/apt/sources.list.d/syncthing.list >/dev/null
  $SUDO apt-get update -qq
  $SUDO apt-get install -y syncthing
fi

systemctl --user enable --now syncthing.service 2>/dev/null || \
  warn "could not enable user syncthing; see docs/SERVER-RUNBOOK.md"

# Syncthing's admin GUI binds to localhost only. Reach it over the tailnet or an
# SSH tunnel -- never expose it directly, it has no authentication by default.
log "Syncthing GUI stays on 127.0.0.1:8384 (tunnel to reach it)"

# --- tailscale --------------------------------------------------------------

if have tailscale; then
  log "Tailscale already installed"
else
  log "Installing Tailscale (private mesh -- nothing exposed to the internet)"
  curl -fsSL https://tailscale.com/install.sh | sh || \
    warn "tailscale install failed; you can use SSH tunnels instead"
fi
have tailscale && ! tailscale status >/dev/null 2>&1 && \
  warn "run 'sudo tailscale up' to join your tailnet"

# --- systemd units ----------------------------------------------------------

log "Installing user systemd units"
mkdir -p "$HOME/.config/systemd/user"
for unit in reelforge-watch.service reelforge-retention.service reelforge-retention.timer; do
  sed -e "s|%h|$HOME|g" -e "s|^User=%i$||" \
    "$REELFORGE_DIR/server/systemd/$unit" > "$HOME/.config/systemd/user/$unit"
done

systemctl --user daemon-reload
systemctl --user enable --now reelforge-retention.timer
systemctl --user enable --now reelforge-watch.service 2>/dev/null || \
  warn "watcher not started -- it needs phase 2 (ingest) to be present. Expected for now."

# Without lingering, user units die when your SSH session ends -- which defeats
# the entire point of an always-on box.
loginctl enable-linger "$USER" 2>/dev/null || \
  warn "could not enable linger; run: sudo loginctl enable-linger $USER"

# --- persistent claude code session -----------------------------------------

if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  log "tmux session '$TMUX_SESSION' already running"
else
  log "Creating persistent tmux session '$TMUX_SESSION'"
  tmux new-session -d -s "$TMUX_SESSION" -c "$ROOT"
  tmux send-keys -t "$TMUX_SESSION" "cd $ROOT && source .venv/bin/activate" C-m
fi

# --- report -----------------------------------------------------------------

cat <<EOF

ReelForge server mode is up.

  Root:      $ROOT
  Inbox:     $ROOT/inbox      (drop footage here)
  Outbox:    $ROOT/outbox     (finished renders appear here)
  Memory:    $ROOT/memory     (your learned taste -- back this up)

Attach from any device:
  ssh $(whoami)@$(hostname) -t 'tmux attach -t $TMUX_SESSION'

Next steps:
  1. sudo tailscale up                     join your private mesh
  2. ssh -L 8384:127.0.0.1:8384 $(whoami)@$(hostname)
     then open http://127.0.0.1:8384       pair Syncthing with your phone
  3. Share $ROOT/inbox and $ROOT/outbox as Syncthing folders
  4. /reel-doctor                          verify from Claude Code

Full walkthrough: docs/SERVER-RUNBOOK.md
EOF
