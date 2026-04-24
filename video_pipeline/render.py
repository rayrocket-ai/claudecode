#!/usr/bin/env python3
"""Render an EDL (Edit Decision List) to a final MP4.

Pipeline, in strict order (enforced by SKILL.md):
    1. Per-segment extract with color grade + 30ms audio fades.
    2. Lossless concat via the concat demuxer (-c copy).
    3. Overlay composition with PTS shift.
    4. Subtitles burned LAST.
    5. (optional) EBU R128 loudness normalization to -14 LUFS.

EDL schema: see .claude/skills/video-editing/SKILL.md

Usage:
    python render.py <edl.json> -o <out.mp4> [--preview] [--no-loudnorm]

--preview    720p, veryfast, lower CRF. Fast iteration.
--no-loudnorm  Skip loudness normalization.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ---------- color grade presets ----------
# Each returns a single `-vf` filter-graph string or "" for no grade.
GRADE_PRESETS: dict[str, str] = {
    "none": "",
    "warm_cinematic": (
        # Slight lift + warm bias + desaturate
        "eq=contrast=1.08:saturation=0.88:gamma_r=1.05:gamma_b=0.95,"
        "curves=preset=increase_contrast"
    ),
    "neutral_punch": "eq=contrast=1.1:saturation=1.05,curves=preset=increase_contrast",
    "cool_film": "eq=contrast=1.05:saturation=0.9:gamma_r=0.95:gamma_b=1.05",
    "bw": "hue=s=0,eq=contrast=1.1",
}


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd[:6])}{' ...' if len(cmd) > 6 else ''}")
    return subprocess.run(cmd, check=True, **kw)


def extract_segment(
    src: Path,
    start: float,
    end: float,
    out: Path,
    grade: str,
    audio_fade: float,
    preview: bool,
) -> None:
    """Extract [start,end] with color grade + audio fade-in/out baked in."""
    duration = end - start
    vf = GRADE_PRESETS.get(grade, "")
    af = (
        f"afade=t=in:st=0:d={audio_fade},"
        f"afade=t=out:st={max(0.0, duration - audio_fade):.3f}:d={audio_fade}"
    )
    crf = "22" if preview else "18"
    scale = "1280:-2" if preview else ""
    if scale:
        vf = f"{scale},{vf}" if vf else f"scale={scale}"

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-to", f"{end:.3f}",
        "-i", str(src),
    ]
    if vf:
        cmd += ["-vf", vf]
    cmd += [
        "-af", af,
        "-c:v", "libx264",
        "-preset", "veryfast" if preview else "medium",
        "-crf", crf,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out),
    ]
    run(cmd, capture_output=True)


def concat_segments(segments: list[Path], out: Path) -> None:
    """Concat via the concat demuxer with -c copy. Lossless."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for seg in segments:
            # Escape single quotes for ffmpeg concat format.
            p = str(seg).replace("'", "'\\''")
            f.write(f"file '{p}'\n")
        list_file = f.name
    try:
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy",
            "-movflags", "+faststart",
            str(out),
        ]
        run(cmd, capture_output=True)
    finally:
        Path(list_file).unlink(missing_ok=True)


def apply_overlays(base: Path, overlays: list[dict], out: Path) -> None:
    """Composite overlays on top of `base`.

    Each overlay must specify file, start_in_output, duration, and optional x/y.
    Overlays use setpts=PTS-STARTPTS+T/TB so animation frame 0 lines up with
    its start_in_output window.
    """
    if not overlays:
        shutil.copy(base, out)
        return

    inputs = ["-i", str(base)]
    for ov in overlays:
        inputs += ["-i", str(ov["file"])]

    # Build the filter graph.
    filter_parts = []
    last_video = "0:v"
    for i, ov in enumerate(overlays, start=1):
        start = float(ov["start_in_output"])
        duration = float(ov["duration"])
        x = ov.get("x", "(W-w)/2")
        y = ov.get("y", "(H-h)/2")
        # Shift overlay's timeline to land at `start`.
        filter_parts.append(
            f"[{i}:v]setpts=PTS-STARTPTS+{start}/TB[ov{i}]"
        )
        enable = f"between(t,{start},{start + duration})"
        new_label = f"tmp{i}"
        filter_parts.append(
            f"[{last_video}][ov{i}]overlay=x={x}:y={y}:"
            f"enable='{enable}':eof_action=pass[{new_label}]"
        )
        last_video = new_label

    filter_complex = ";".join(filter_parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{last_video}]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out),
    ]
    run(cmd, capture_output=True)


def burn_subtitles(base: Path, srt: Path, style: str, out: Path) -> None:
    """Burn subtitles LAST. Always after overlays. Style is a libass-compatible
    `force_style` string or one of our named presets."""
    presets = {
        "bold-overlay": (
            "FontName=Arial Black,FontSize=18,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "BorderStyle=1,Outline=3,Shadow=0,"
            "Alignment=2,MarginV=35"
        ),
        "natural-sentence": (
            "FontName=Arial,FontSize=16,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "BorderStyle=1,Outline=2,Shadow=1,"
            "Alignment=2,MarginV=60"
        ),
    }
    force_style = presets.get(style, style or presets["bold-overlay"])
    # Escape the path for libass: colons and backslashes.
    srt_arg = str(srt).replace(":", r"\:").replace("\\", r"\\\\")
    vf = f"subtitles='{srt_arg}':force_style='{force_style}'"

    cmd = [
        "ffmpeg", "-y", "-i", str(base),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out),
    ]
    run(cmd, capture_output=True)


def loudnorm(base: Path, out: Path) -> None:
    """EBU R128 two-pass loudness norm to -14 LUFS (social-media target)."""
    # First pass: measure.
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(base),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    # Extract JSON from stderr.
    txt = r.stderr
    brace_start = txt.rfind("{")
    if brace_start == -1:
        print("loudnorm measurement failed; skipping", file=sys.stderr)
        shutil.copy(base, out)
        return
    brace_end = txt.rfind("}")
    stats = json.loads(txt[brace_start:brace_end + 1])

    cmd = [
        "ffmpeg", "-y", "-i", str(base),
        "-af",
        f"loudnorm=I=-14:TP=-1.5:LRA=11:"
        f"measured_I={stats['input_i']}:"
        f"measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:"
        f"measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:"
        f"linear=true:print_format=summary",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        str(out),
    ]
    run(cmd, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl", help="Path to EDL JSON")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--preview", action="store_true",
                    help="720p fast render")
    ap.add_argument("--no-loudnorm", action="store_true")
    ap.add_argument("--keep-temp", action="store_true")
    args = ap.parse_args()

    edl_path = Path(args.edl).resolve()
    out_path = Path(args.output).resolve()
    edl = json.loads(edl_path.read_text())

    sources = {k: Path(v).resolve() for k, v in edl["sources"].items()}
    ranges = edl["ranges"]
    grade = edl.get("grade", "none")
    audio_fade = float(edl.get("audio_fade", 0.03))
    overlays = edl.get("overlays", [])
    subtitles = edl.get("subtitles")
    sub_style = edl.get("subtitle_style", "bold-overlay")

    if not ranges:
        sys.exit("EDL has no ranges.")

    work = Path(tempfile.mkdtemp(prefix="render_"))
    print(f"work dir: {work}")

    try:
        # 1. Per-segment extract
        segs: list[Path] = []
        for i, r in enumerate(ranges, 1):
            src = sources[r["source"]]
            seg_out = work / f"seg_{i:03d}.mp4"
            print(f"[{i:03d}] {r['source']}  {r['start']:.2f} -> {r['end']:.2f}  "
                  f"({r['end'] - r['start']:.2f}s)")
            extract_segment(src, float(r["start"]), float(r["end"]),
                            seg_out, grade, audio_fade, args.preview)
            segs.append(seg_out)

        # 2. Concat (lossless)
        concat_out = work / "concat.mp4"
        concat_segments(segs, concat_out)
        print(f"concat: {concat_out}")

        # 3. Overlays
        overlay_out = work / "overlays.mp4"
        apply_overlays(concat_out, overlays, overlay_out)
        print(f"overlays: {overlay_out}")

        # 4. Subtitles (LAST)
        sub_out = work / "subtitled.mp4"
        if subtitles:
            sub_path = (edl_path.parent / subtitles).resolve()
            if not sub_path.exists():
                print(f"subtitles not found: {sub_path}", file=sys.stderr)
                sys.exit(1)
            burn_subtitles(overlay_out, sub_path, sub_style, sub_out)
        else:
            shutil.copy(overlay_out, sub_out)

        # 5. Loudness norm
        final = work / "final.mp4"
        if args.no_loudnorm or args.preview:
            shutil.copy(sub_out, final)
        else:
            loudnorm(sub_out, final)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(final), str(out_path))
        print(f"\nWrote: {out_path}")
    finally:
        if args.keep_temp:
            print(f"(kept work dir: {work})")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
