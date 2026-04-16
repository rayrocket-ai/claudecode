#!/usr/bin/env python3
"""Transcribe a video/audio file to SRT with word-level timings.

Usage:
    python transcribe.py <input_video> [--model base|small|medium|large-v3] [--lang en]

Outputs next to the input:
    <name>.srt        -- subtitle file
    <name>.words.json -- word-level timings (for caption animation)
    <name>.segments.json -- segment-level timings (for chapter splits)
"""
import argparse
import json
import sys
from pathlib import Path


def format_ts(seconds: float) -> str:
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--model", default="base")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Missing dependency. Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    stem = in_path.with_suffix("")
    srt_path = Path(str(stem) + ".srt")
    words_path = Path(str(stem) + ".words.json")
    segs_path = Path(str(stem) + ".segments.json")

    print(f"Loading Whisper model: {args.model}")
    model = WhisperModel(args.model, device=args.device, compute_type="int8")

    print(f"Transcribing: {in_path.name}")
    segments, info = model.transcribe(
        str(in_path),
        language=args.lang,
        word_timestamps=True,
        vad_filter=True,
    )

    srt_lines = []
    all_words = []
    all_segs = []
    for idx, seg in enumerate(segments, 1):
        srt_lines.append(str(idx))
        srt_lines.append(f"{format_ts(seg.start)} --> {format_ts(seg.end)}")
        srt_lines.append(seg.text.strip())
        srt_lines.append("")
        all_segs.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
        if seg.words:
            for w in seg.words:
                all_words.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "prob": w.probability,
                })

    srt_path.write_text("\n".join(srt_lines))
    words_path.write_text(json.dumps(all_words, indent=2))
    segs_path.write_text(json.dumps(all_segs, indent=2))

    print(f"Detected language: {info.language} (prob {info.language_probability:.2f})")
    print(f"Wrote: {srt_path.name}")
    print(f"Wrote: {words_path.name}  ({len(all_words)} words)")
    print(f"Wrote: {segs_path.name}  ({len(all_segs)} segments)")


if __name__ == "__main__":
    main()
