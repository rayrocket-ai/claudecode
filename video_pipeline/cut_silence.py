#!/usr/bin/env python3
"""Remove silent gaps from a video using ffmpeg's silencedetect.

Usage:
    python cut_silence.py <input> <output> [--threshold -30] [--min-silence 0.5] [--pad 0.1]

--threshold    dB below which audio is "silent" (default -30)
--min-silence  minimum silence duration in seconds to cut (default 0.5)
--pad          seconds of silence to keep on each side of speech (default 0.1)
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def detect_silence(path: str, threshold: float, min_silence: float):
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", path,
        "-af", f"silencedetect=noise={threshold}dB:d={min_silence}",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stderr
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--threshold", type=float, default=-30)
    ap.add_argument("--min-silence", type=float, default=0.5)
    ap.add_argument("--pad", type=float, default=0.1)
    args = ap.parse_args()

    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    duration = get_duration(str(in_path))
    print(f"Duration: {duration:.2f}s")
    print(f"Detecting silence (threshold={args.threshold}dB, min={args.min_silence}s)...")
    silences = detect_silence(str(in_path), args.threshold, args.min_silence)
    print(f"Found {len(silences)} silent regions")

    # Build keep windows = complement of silence regions, with padding.
    keep = []
    cursor = 0.0
    for s, e in silences:
        if e is None:
            e = duration
        s_pad = max(cursor, s - args.pad)
        e_pad = min(duration, e + args.pad)
        if s_pad > cursor:
            keep.append((cursor, s_pad))
        cursor = e_pad
    if cursor < duration:
        keep.append((cursor, duration))

    if not keep:
        print("Nothing to keep. Aborting.", file=sys.stderr)
        sys.exit(1)

    total_kept = sum(e - s for s, e in keep)
    print(f"Keeping {len(keep)} segments, total {total_kept:.2f}s "
          f"(cut {duration - total_kept:.2f}s)")

    # Build a concat demuxer filter_complex.
    parts = []
    for i, (s, e) in enumerate(keep):
        parts.append(
            f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}]"
        )
    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(keep)))
    filter_complex = ";".join(parts) + f";{concat_inputs}concat=n={len(keep)}:v=1:a=1[v][a]"

    cmd = [
        "ffmpeg", "-y", "-i", str(in_path),
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(out_path),
    ]
    print("Running ffmpeg...")
    subprocess.run(cmd, check=True)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
