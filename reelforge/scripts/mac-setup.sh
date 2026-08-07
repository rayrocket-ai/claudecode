#!/usr/bin/env bash
#
# ReelForge setup for macOS.
#
# Run this after Homebrew is installed and the repository is cloned. It
# installs the tools, builds an isolated environment, puts `reelforge` on your
# PATH, and verifies the result -- so the first thing you run is a check that
# passed rather than a command that might not exist.
#
#   bash scripts/mac-setup.sh
#
# Safe to run twice. Everything it does is idempotent.

set -euo pipefail

VENV="$HOME/.reelforge/venv"
BIN="$HOME/.local/bin"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

say()  { printf "\n\033[1;36m==>\033[0m \033[1m%s\033[0m\n" "$1"; }
ok()   { printf "    \033[0;32mok\033[0m  %s\n" "$1"; }
warn() { printf "    \033[0;33m!\033[0m   %s\n" "$1"; }
die()  { printf "\n\033[0;31mstopped:\033[0m %s\n\n" "$1" >&2; exit 1; }

# --------------------------------------------------------------------------
say "Checking Homebrew"

if ! command -v brew >/dev/null 2>&1; then
    # The installer adds brew to a shell profile, but only for *new* shells --
    # the most common reason "brew: command not found" survives an install.
    for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
        if [ -x "$candidate" ]; then
            eval "$("$candidate" shellenv)"
            warn "found Homebrew at $candidate but it was not on PATH (fixed for this run)"
            break
        fi
    done
fi

command -v brew >/dev/null 2>&1 || die "Homebrew is not installed. Install it first:

  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"

then close this terminal, open a new one, and run this script again."

ok "brew $(brew --version | head -1 | awk '{print $2}')"

# --------------------------------------------------------------------------
say "Installing ffmpeg, Python and Chromium (this is the slow part)"

brew list ffmpeg     >/dev/null 2>&1 || brew install ffmpeg
brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
ok "ffmpeg $(ffmpeg -version 2>/dev/null | head -1 | awk '{print $3}')"

# Chromium is only needed for animated overlays, so a failure here is not
# fatal -- the rest of the editor works without it and says so at render time.
if [ -d "/Applications/Google Chrome.app" ] || [ -d "/Applications/Chromium.app" ]; then
    ok "a browser for animated overlays is already installed"
else
    # Google Chrome rather than Chromium: Homebrew deprecated the Chromium
    # cask because it fails the macOS Gatekeeper check, and is disabling it
    # on 2026-09-01. Chrome is signed, needs no quarantine surgery, and is
    # the same engine as far as frame capture is concerned.
    if brew install --cask google-chrome; then
        ok "Google Chrome installed"
    elif brew install --cask chromium; then
        # Unsigned, so Gatekeeper refuses to launch it until the quarantine
        # flag is cleared -- otherwise you get a baffling "cannot be opened"
        # dialog at render time rather than at install time.
        xattr -dr com.apple.quarantine /Applications/Chromium.app 2>/dev/null || true
        warn "installed Chromium (deprecated by Homebrew; Chrome is preferred)"
    else
        warn "no browser installed -- animated overlays will be skipped."
        warn "Everything else (trimming, captions, zooms, emoji, sound) still works."
    fi
fi

# --------------------------------------------------------------------------
say "Building the ReelForge environment"

PY="$(brew --prefix python@3.12)/bin/python3.12"
[ -x "$PY" ] || PY="python3"

if [ ! -d "$VENV" ]; then
    "$PY" -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -e "$REPO"
ok "installed into $VENV"

# --------------------------------------------------------------------------
say "Putting reelforge on your PATH"

mkdir -p "$BIN"
ln -sf "$VENV/bin/reelforge" "$BIN/reelforge"

# Symlinking the console script rather than adding the venv's bin to PATH is
# deliberate: the shebang already points at the venv's Python, so the command
# works everywhere without the venv's `python3` shadowing the system one.
if ! echo ":$PATH:" | grep -q ":$BIN:"; then
    for profile in "$HOME/.zprofile" "$HOME/.zshrc"; do
        if [ -f "$profile" ] || [ "$profile" = "$HOME/.zprofile" ]; then
            grep -q '\.local/bin' "$profile" 2>/dev/null || \
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$profile"
        fi
    done
    export PATH="$BIN:$PATH"
    warn "added ~/.local/bin to your PATH (open a new terminal to make it permanent)"
fi
ok "reelforge -> $BIN/reelforge"

# --------------------------------------------------------------------------
say "Verifying"

"$BIN/reelforge" --help >/dev/null || die "reelforge did not run. Send me the output above."
ok "the command runs"

# Imported through the installed package name, not the source layout: after
# `pip install -e .` the modules live under `reelforge.core`, and importing
# them as `core` only works from the repository root.
"$VENV/bin/python" - <<'PY'
from reelforge.core import hardware
from reelforge.core.render import motion, emoji

p = hardware.profile()
print(f"    ok  {p.cores} cores, {p.ram_gb}GB RAM, encoder: {p.encoder}")
print(f"    ok  transcription: {p.whisper_model} on {p.whisper_device}")
browser = motion.find_chromium()
print(f"    ok  browser: {browser}" if browser
      else "    !   no browser found -- animated overlays will be skipped")
font = emoji.find_font()
print(f"    ok  emoji font: {font.name}" if font
      else "    !   no colour emoji font found -- emoji overlays will be skipped")
PY

cat <<EOF

$(printf "\033[1;32mReady.\033[0m")

Edit your first video:

  reelforge prepare /path/to/your/video.mp4

Tip: instead of typing the path, drag the video from Finder into this
terminal window and it will paste the path for you.

The first run downloads the speech model (~1.5GB, once) and transcribes.
After that it is cached and instant.

Then from Claude Code, inside this repository:

  /reels /path/to/your/video.mp4 --count 3     # vertical reels
  /vlog /path/to/your/video.mp4                # a YouTube episode

EOF
