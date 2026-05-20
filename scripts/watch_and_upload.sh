#!/usr/bin/env bash
# Watch a folder for new video files; upload each as a GitHub release so
# Claude Code (running in a sandbox that can reach github.com but not your
# laptop or Dropbox) can pull it down with `studio.py pull --latest`.
#
# Usage:
#   scripts/watch_and_upload.sh [WATCH_DIR]
#   scripts/watch_and_upload.sh --once [WATCH_DIR]    # scan + upload + exit
#
# Defaults to ~/Dropbox/raw_videos. Repo defaults to the env var
# WATCH_REPO or "rayrocket-ai/claudecode".
#
# Requirements (install on your laptop, not the sandbox):
#   gh           https://cli.github.com  — authenticated (`gh auth login`)
#   fswatch      macOS: brew install fswatch
#   inotifywait  Linux: apt-get install inotify-tools
#
# Behavior:
#   - Waits for a file to stop growing for 5s before uploading.
#   - Tags releases `raw-YYYYMMDD-HHMMSS-<slug>` (unique).
#   - Tracks uploaded files in <WATCH_DIR>/.uploaded.log to avoid re-uploads.
#   - Moves uploaded files to <WATCH_DIR>/uploaded/ on success.
#   - Retries upload up to 3 times with backoff.

set -euo pipefail

ONCE=0
if [ "${1:-}" = "--once" ]; then
  ONCE=1
  shift
fi

WATCH_DIR="${1:-$HOME/Dropbox/raw_videos}"
REPO="${WATCH_REPO:-rayrocket-ai/claudecode}"
EXTS="mp4 mov m4v webm mkv"
STABLE_SECONDS=5
LOG_FILE="$WATCH_DIR/.uploaded.log"
UPLOADED_DIR="$WATCH_DIR/uploaded"

# ---- prerequisite checks ----

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not found. Install: https://cli.github.com" >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "error: gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi
if [ $ONCE -eq 0 ]; then
  if ! command -v fswatch >/dev/null 2>&1 && ! command -v inotifywait >/dev/null 2>&1; then
    echo "error: need fswatch (macOS) or inotifywait (Linux)" >&2
    echo "  macOS: brew install fswatch" >&2
    echo "  linux: sudo apt-get install inotify-tools" >&2
    exit 1
  fi
fi

mkdir -p "$WATCH_DIR" "$UPLOADED_DIR"
touch "$LOG_FILE"

echo "watching:  $WATCH_DIR"
echo "repo:      $REPO"
echo "log:       $LOG_FILE"
echo

# ---- helpers ----

slugify() {
  # filename → safe slug for a tag
  echo "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/\.[^.]+$//' \
    | sed -E 's/[^a-z0-9]+/-/g' \
    | sed -E 's/^-+|-+$//g' \
    | cut -c1-40
}

is_video() {
  local f="$1" ext
  ext="${f##*.}"
  for e in $EXTS; do
    [ "${ext,,}" = "$e" ] && return 0
  done
  return 1
}

wait_until_stable() {
  local f="$1" last_size=0 size=0
  while true; do
    size=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo 0)
    if [ "$size" -gt 0 ] && [ "$size" = "$last_size" ]; then
      return 0
    fi
    last_size=$size
    sleep "$STABLE_SECONDS"
  done
}

already_uploaded() {
  local f="$1"
  grep -Fxq "$f" "$LOG_FILE"
}

upload_one() {
  local f="$1" base slug tag
  base="$(basename "$f")"
  slug="$(slugify "$base")"
  tag="raw-$(date +%Y%m%d-%H%M%S)-$slug"

  echo "[$(date +%H:%M:%S)] uploading: $base"
  wait_until_stable "$f"

  local attempt=0 max=3
  while [ $attempt -lt $max ]; do
    attempt=$((attempt+1))
    if gh release create "$tag" "$f" \
        --repo "$REPO" \
        --title "$base" \
        --notes "Auto-uploaded from $WATCH_DIR" >/dev/null 2>&1; then
      echo "[$(date +%H:%M:%S)] ✓ $tag"
      echo "$f" >> "$LOG_FILE"
      mv "$f" "$UPLOADED_DIR/$base"
      return 0
    fi
    echo "[$(date +%H:%M:%S)] upload failed (attempt $attempt/$max); retrying in $((attempt * 5))s"
    sleep $((attempt * 5))
  done

  echo "[$(date +%H:%M:%S)] ✗ giving up on $base" >&2
  return 1
}

handle_path() {
  local f="$1"
  [ -f "$f" ] || return 0
  is_video "$f" || return 0
  already_uploaded "$f" && return 0
  # Skip files in the uploaded/ subdir.
  case "$f" in
    "$UPLOADED_DIR"/*) return 0 ;;
  esac
  upload_one "$f" || true
}

# ---- initial sweep ----

shopt -s nullglob
for f in "$WATCH_DIR"/*; do
  handle_path "$f"
done
shopt -u nullglob

[ $ONCE -eq 1 ] && exit 0

# ---- watch loop ----

if command -v fswatch >/dev/null 2>&1; then
  fswatch -0 --event Created --event Updated --event Renamed "$WATCH_DIR" \
    | while IFS= read -r -d '' f; do
        handle_path "$f"
      done
else
  inotifywait -m -e close_write -e moved_to --format '%w%f' "$WATCH_DIR" \
    | while read -r f; do
        handle_path "$f"
      done
fi
