#!/usr/bin/env python3
"""Split a long video into Reel-length chunks at natural sentence breaks.

Requires a <input>.segments.json produced by transcribe.py alongside the video.

Usage:
    python split_reels.py <input_video> <output_dir> [--min 30] [--max 60] [--target 45]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def pick_breakpoints(segments, min_len, max_len, target):
    """Greedy: accumulate segments until we pass `target`; end on nearest sentence boundary."""
    chunks = []
    start = None
    last_end = None
    for seg in segments:
        s, e, text = seg["start"], seg["end"], seg["text"]
        if start is None:
            start = s
        last_end = e
        dur = e - start
        ends_sentence = text.rstrip().endswith((".", "!", "?"))
        if dur >= target and ends_sentence:
            chunks.append((start, e))
            start = None
        elif dur >= max_len:
            chunks.append((start, e))
            start = None
    if start is not None and last_end is not None and last_end - start >= min_len:
        chunks.append((start, last_end))
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output_dir")
    ap.add_argument("--min", type=float, default=30.0)
    ap.add_argument("--max", type=float, default=60.0)
    ap.add_argument("--target", type=float, default=45.0)
    args = ap.parse_args()

    in_path = Path(args.input).resolve()
    segs_path = in_path.with_suffix("").with_suffix(".segments.json")
    if not segs_path.exists():
        segs_path = Path(str(in_path.with_suffix("")) + ".segments.json")
    if not segs_path.exists():
        print(f"Missing {segs_path}. Run transcribe.py first.", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    segments = json.loads(segs_path.read_text())
    chunks = pick_breakpoints(segments, args.min, args.max, args.target)
    print(f"Planning {len(chunks)} chunks")

    for i, (s, e) in enumerate(chunks, 1):
        dur = e - s
        out_file = out_dir / f"{in_path.stem}_reel_{i:02d}.mp4"
        print(f"  [{i:02d}] {s:7.2f} \u2192 {e:7.2f}  ({dur:5.2f}s)  {out_file.name}")
        cmd = [
            "ffmpeg", "-y", "-ss", f"{s}", "-to", f"{e}",
            "-i", str(in_path),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            str(out_file),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    print(f"Wrote {len(chunks)} chunks to {out_dir}")


if __name__ == "__main__":
    main()
