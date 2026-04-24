#!/usr/bin/env bash
# End-to-end prep pipeline for long-form video -> reel-ready chunks.
#
# Usage:
#   ./run_pipeline.sh <input_video> [model] [engine]
#
# model:  Whisper size (tiny|base|small|medium|large-v3). Default: base.
# engine: whisper (default, free/local) or scribe (ElevenLabs, preserves fillers).
#
# Outputs into video_pipeline/output/<basename>/:
#   silenced.mp4              -- silence trimmed
#   cleaned.mp4               -- silence + filler words trimmed
#   cleaned.srt               -- subtitles
#   cleaned.words.json        -- word-level timings
#   cleaned.segments.json     -- segment-level timings
#   reels/<basename>_reel_NN.mp4          -- 16:9 reel-length chunks
#   reels_vertical/<basename>_reel_NN.mp4 -- 9:16 Reel-ready

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <input_video> [whisper_model] [engine]" >&2
  exit 1
fi

INPUT="$1"
MODEL="${2:-base}"
ENGINE="${3:-whisper}"

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

SILENCED="$OUT_DIR/silenced.mp4"
CLEANED="$OUT_DIR/cleaned.mp4"

echo "=== [1/5] Cutting silence ==="
python3 "$SCRIPT_DIR/cut_silence.py" "$INPUT" "$SILENCED"

echo "=== [2/5] Transcribing (engine=$ENGINE, model=$MODEL) ==="
if [ "$ENGINE" = "scribe" ]; then
  python3 "$SCRIPT_DIR/transcribe.py" "$SILENCED" --engine scribe
else
  python3 "$SCRIPT_DIR/transcribe.py" "$SILENCED" --engine whisper --model "$MODEL"
fi

echo "=== [3/5] Cutting filler words ==="
python3 "$SCRIPT_DIR/cut_fillers.py" "$SILENCED" "$CLEANED"
# Re-transcribe the cleaned cut so downstream timings line up.
if [ "$ENGINE" = "scribe" ]; then
  python3 "$SCRIPT_DIR/transcribe.py" "$CLEANED" --engine scribe
else
  python3 "$SCRIPT_DIR/transcribe.py" "$CLEANED" --engine whisper --model "$MODEL"
fi

echo "=== [4/5] Splitting to reel-length chunks ==="
python3 "$SCRIPT_DIR/split_reels.py" "$CLEANED" "$REELS"

echo "=== [5/5] Reframing each chunk to 9:16 ==="
for f in "$REELS"/*.mp4; do
  [ -e "$f" ] || continue
  name="$(basename "$f")"
  python3 "$SCRIPT_DIR/to_vertical.py" "$f" "$REELS_V/$name" --mode blur
done

echo
echo "Done. Outputs in: $OUT_DIR"
ls -la "$OUT_DIR"
echo
echo "Next:"
echo "  - Remotion:    cd video_remotion && node scripts/import-words.js $OUT_DIR/cleaned.words.json && npm run start"
echo "  - Hyperframes: cd video_hyperframes && npx hyperframes preview"
echo "  - EDL render:  python video_pipeline/render.py <edl.json> -o final.mp4"
