#!/usr/bin/env python3
"""Reframe a video to 9:16 (1080x1920) for Reels/TikTok/Shorts.

Modes:
    blur  -- blurred background, original video centered (safe, universal)
    crop  -- center-crop (good for talking head framed to center)

Usage:
    python to_vertical.py <input> <output> [--mode blur|crop]
"""
import argparse
import subprocess
import sys
from pathlib import Path


def build_filter(mode: str) -> str:
    W, H = 1080, 1920
    if mode == "crop":
        return (
            f"scale=-2:{H},"
            f"crop={W}:{H}:(in_w-{W})/2:0"
        )
    # blur mode: background = blurred, fill-to-cover; foreground = letterboxed original
    return (
        f"split=2[bg][fg];"
        f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},gblur=sigma=30[bgblur];"
        f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];"
        f"[bgblur][fgs]overlay=(W-w)/2:(H-h)/2"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--mode", choices=["blur", "crop"], default="blur")
    args = ap.parse_args()

    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    vf = build_filter(args.mode)
    cmd = [
        "ffmpeg", "-y", "-i", str(in_path),
        "-filter_complex", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    print(f"Reframing to 9:16 ({args.mode} mode)...")
    subprocess.run(cmd, check=True)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
