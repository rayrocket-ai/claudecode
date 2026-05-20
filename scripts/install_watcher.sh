#!/usr/bin/env bash
# Install dependencies for watch_and_upload.sh on macOS.
#
# - Installs gh + fswatch via Homebrew if missing.
# - Logs you into GitHub if needed.
# - Installs a LaunchAgent so the watcher runs on login.
#
# Usage:
#   scripts/install_watcher.sh [WATCH_DIR]
#
# Defaults WATCH_DIR to ~/Dropbox/raw_videos.

set -euo pipefail

WATCH_DIR="${1:-$HOME/Dropbox/raw_videos}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_DIR/scripts/watch_and_upload.sh"
LABEL="com.claudecode.video-watcher"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/claudecode-video-watcher"

if [ "$(uname)" != "Darwin" ]; then
  echo "This installer is macOS-only. For Linux, run scripts/watch_and_upload.sh"
  echo "under systemd or tmux:  nohup scripts/watch_and_upload.sh &"
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "error: install Homebrew first: https://brew.sh" >&2
  exit 1
fi

for pkg in gh fswatch; do
  if ! command -v "$pkg" >/dev/null 2>&1; then
    echo "installing $pkg..."
    brew install "$pkg"
  fi
done

if ! gh auth status >/dev/null 2>&1; then
  echo "logging into GitHub..."
  gh auth login
fi

mkdir -p "$WATCH_DIR" "$LOG_DIR" "$(dirname "$PLIST")"

# Unload existing agent first (no-op if missing).
launchctl unload "$PLIST" 2>/dev/null || true

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$SCRIPT</string>
    <string>$WATCH_DIR</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOG_DIR/out.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/err.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
</dict>
</plist>
EOF

launchctl load "$PLIST"

echo
echo "Installed and started: $LABEL"
echo "  watching: $WATCH_DIR"
echo "  logs:     $LOG_DIR/{out,err}.log"
echo
echo "To stop:    launchctl unload $PLIST"
echo "To remove:  rm $PLIST"
