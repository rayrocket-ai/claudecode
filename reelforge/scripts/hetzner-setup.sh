#!/usr/bin/env bash
#
# ReelForge on a Hetzner box, end to end, in one command.
#
# This is the "one machine, reachable from anywhere" setup: the editor, the
# AI that drives it, your footage and your finished renders all live here, and
# every laptop and phone you own is just a way to reach it. Nothing is
# installed per-device ever again.
#
#   bash scripts/hetzner-setup.sh
#
# Runs install.sh (packages + venv), server-setup.sh (inbox/outbox, watcher,
# Syncthing, tmux), then adds the two things those two miss: a browser for
# animated overlays, and Claude Code itself.
#
# Safe to run twice.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

say()  { printf "\n\033[1;36m==>\033[0m \033[1m%s\033[0m\n" "$1"; }
ok()   { printf "    \033[0;32mok\033[0m  %s\n" "$1"; }
warn() { printf "    \033[0;33m!\033[0m   %s\n" "$1"; }
die()  { printf "\n\033[0;31mstopped:\033[0m %s\n\n" "$1" >&2; exit 1; }

# --------------------------------------------------------------------------
say "Checking who is running this"

if [ "$(id -u)" -eq 0 ]; then
    die "do not run this as root.

Chromium refuses to launch as root without disabling its sandbox, the
systemd units here are deliberately user-scoped, and anything that renders
untrusted media should not be running with the whole box's authority.

Create an ordinary user once, then come back:

  adduser ray
  usermod -aG sudo ray
  su - ray

Then re-clone the repo in that user's home and run this script again.

While you are logged in as root, also change the root password: it was
pasted into a chat window and must be treated as compromised.

  passwd"
fi

sudo -n true 2>/dev/null || warn "you will be asked for your sudo password"
ok "running as $(whoami)"

# --------------------------------------------------------------------------
say "Base install (packages, Python environment, ffmpeg)"
bash "$REPO/scripts/install.sh"

# --------------------------------------------------------------------------
say "Server mode (inbox, watcher, outbox, Syncthing, tmux)"
bash "$REPO/scripts/server-setup.sh"

# --------------------------------------------------------------------------
say "Browser for animated overlays"

if command -v chromium >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1; then
    ok "chromium already installed"
else
    # Headless only -- no X, no desktop. The HyperFrames backend screenshots
    # pages; it never shows a window.
    if sudo apt-get install -y --no-install-recommends chromium 2>/dev/null \
       || sudo apt-get install -y --no-install-recommends chromium-browser 2>/dev/null; then
        ok "chromium installed"
    else
        warn "no chromium -- animated overlays will be skipped and say so."
        warn "Everything else (trimming, captions, zooms, emoji, sound) works."
    fi
fi

# --------------------------------------------------------------------------
say "Claude Code"

# The piece the other two scripts miss. `reelforge` can transcribe, compose
# and render on its own, but choosing WHICH moments to cut is a judgement
# call -- that is what Claude Code does, and without it the box can only
# execute edits somebody else decided on.
if command -v claude >/dev/null 2>&1; then
    ok "claude already installed ($(claude --version 2>/dev/null | head -1))"
else
    if ! command -v node >/dev/null 2>&1; then
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - >/dev/null 2>&1 \
            || warn "nodesource setup failed; falling back to distro node"
        sudo apt-get install -y nodejs || die "could not install Node.js"
    fi
    sudo npm install -g @anthropic-ai/claude-code \
        || die "could not install Claude Code. Try: sudo npm install -g @anthropic-ai/claude-code"
    ok "claude installed"
fi

# --------------------------------------------------------------------------
say "Verifying"

VENV="$HOME/.reelforge/venv"
PYBIN="$VENV/bin/python"
[ -x "$PYBIN" ] || PYBIN="python3"

"$PYBIN" - <<'PY'
from reelforge.core import hardware
from reelforge.core.render import motion, emoji

p = hardware.profile()
print(f"    ok  {p.cores} cores, {p.ram_gb}GB RAM, encoder: {p.encoder}")
print(f"    ok  transcription: {p.whisper_model} on {p.whisper_device}")
browser = motion.find_chromium()
print(f"    ok  browser: {browser}" if browser
      else "    !   no browser -- animated overlays will be skipped")
font = emoji.find_font()
print(f"    ok  emoji font: {font.name}" if font
      else "    !   no colour emoji font -- emoji overlays will be skipped")
PY

cat <<EOF

$(printf "\033[1;32mReady.\033[0m") This box is now the only machine that needs setting up.

1. Authenticate Claude Code, once:

     claude

   Follow the login prompt, then type /exit.

2. Get a video onto the box. From any Mac:

     scp ~/Desktop/IMG_1200.MOV $(whoami)@$(hostname -I 2>/dev/null | awk '{print $1}'):~/reelforge/inbox/

   The watcher notices it and transcribes it in the background, so it is
   ready before you ask for anything.

3. Edit it, from any machine, in a session that survives disconnection:

     ssh $(whoami)@$(hostname -I 2>/dev/null | awk '{print $1}')
     tmux attach -t reelforge || tmux new -s reelforge
     cd ~/reelforge-src && claude

   then inside Claude Code:

     /reels ~/reelforge/inbox/IMG_1200.MOV --count 3

   Close your laptop mid-render and it keeps going. Reattach from the Mac
   mini, your phone, anywhere.

Finished reels land in ~/reelforge/outbox/.

EOF
