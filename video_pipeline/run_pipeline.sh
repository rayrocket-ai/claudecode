#!/usr/bin/env bash
# End-to-end prep pipeline for long-form video -> reel-ready chunks.
#
# Usage:
#   ./run_pipeline.sh <input_video> [model]
#
# model: Whisper size (tiny|base|small|medium|large-v3). Default: base.
#
# Outputs into video_pipeline/output/<basename>/:
#   cleaned.mp4               -- silence/filler trimmed
#   cleaned.srt               -- subtitles
#   cleaned.words.json        -- word-level timings
#   cleaned.segments.json     -- segment-level timings
#   reels/<basename>_reel_NN.mp4          -- 16:9 reel-length chunks
#   reels_vertical/<basename>_reel_NN.mp4 -- 9:16 Reel-ready

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <input_video> [whisper_model]" >&2
  exit 1
fi

INPUT="$1"
MODEL="${2:-base}"

if [ ! -f "$INPUT" ]; then
  echo "Input not found: $INPUT" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASENAME="$(basename "${INPUT%.*}")"
OUT_DIR="$SCRIPT_DIR/output/$BASENAME"
WORK="$OUT_DIR/work"
REELS="$OUT_DIR/reels"
REELS_V="$OUT_DIR/reels_vertical"

mkdir -p "$WORK" "$REELS" "$REELS_V"

CLEANED="$OUT_DIR/cleaned.mp4"

echo "=== [1/4] Cutting silence ==="
python3 "$SCRIPT_DIR/cut_silence.py" "$INPUT" "$CLEANED"

echo "=== [2/4] Transcribing (model=$MODEL) ==="
python3 "$SCRIPT_DIR/transcribe.py" "$CLEANED" --model "$MODEL"

echo "=== [3/4] Splitting to reel-length chunks ==="
python3 "$SCRIPT_DIR/split_reels.py" "$CLEANED" "$REELS"

echo "=== [4/4] Reframing each chunk to 9:16 ==="
for f in "$REELS"/*.mp4; do
  [ -e "$f" ] || continue
  name="$(basename "$f")"
  python3 "$SCRIPT_DIR/to_vertical.py" "$f" "$REELS_V/$name" --mode blur
done

echo
echo "Done. Outputs in: $OUT_DIR"
ls -la "$OUT_DIR"
echo
echo "Next step: import $REELS_V/*.mp4 into CapCut to add B-roll + animated captions."
echo "Use $OUT_DIR/cleaned.srt as a starting point for captions."
