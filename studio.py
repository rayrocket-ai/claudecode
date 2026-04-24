#!/usr/bin/env python3
"""Studio — one entry point for the video editing pipeline.

Subcommands:
    studio.py prep   <input.mp4> [--engine scribe|whisper] [--model base]
    studio.py render <edl.json>  -o out.mp4 [--preview]
    studio.py pack   <edit-dir>

Example full pipeline, from raw camera file to a production MP4:

    python studio.py prep raw/interview.mp4 --engine scribe
    # edit edl.json by hand or via an agent using .claude/skills/video-editing/SKILL.md
    python studio.py render edl.json -o output/final.mp4

`prep` runs: silence cut -> transcribe -> filler cut -> re-transcribe -> pack.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PIPELINE = ROOT / "video_pipeline"


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True)


def cmd_prep(args: argparse.Namespace) -> None:
    in_path = Path(args.input).resolve()
    if not in_path.exists():
        sys.exit(f"Input not found: {in_path}")

    basename = in_path.stem
    out_dir = PIPELINE / "output" / basename
    out_dir.mkdir(parents=True, exist_ok=True)

    silenced = out_dir / "silenced.mp4"
    cleaned = out_dir / "cleaned.mp4"

    print("=== [1/5] Cutting silence ===")
    run(["python3", str(PIPELINE / "cut_silence.py"), str(in_path), str(silenced)])

    print("=== [2/5] Transcribing (pre-filler) ===")
    transcribe_cmd = ["python3", str(PIPELINE / "transcribe.py"), str(silenced)]
    if args.engine == "scribe":
        transcribe_cmd += ["--engine", "scribe"]
    else:
        transcribe_cmd += ["--engine", "whisper", "--model", args.model]
    run(transcribe_cmd)

    print("=== [3/5] Cutting fillers ===")
    filler_cmd = ["python3", str(PIPELINE / "cut_fillers.py"), str(silenced), str(cleaned)]
    if args.cut_discourse:
        filler_cmd.append("--cut-discourse")
    run(filler_cmd)

    print("=== [4/5] Re-transcribing cleaned cut ===")
    retranscribe_cmd = ["python3", str(PIPELINE / "transcribe.py"), str(cleaned)]
    if args.engine == "scribe":
        retranscribe_cmd += ["--engine", "scribe"]
    else:
        retranscribe_cmd += ["--engine", "whisper", "--model", args.model]
    run(retranscribe_cmd)

    print("=== [5/5] Packing phrase-level markdown ===")
    run(
        ["python3", str(PIPELINE / "pack_transcripts.py"),
         "--glob", str(out_dir / "cleaned.words.json"),
         "-o", str(out_dir / "takes_packed.md")],
    )

    print()
    print(f"Done. Artifacts in: {out_dir}")
    print(f"  - {silenced.name}            (silence removed)")
    print(f"  - {cleaned.name}             (silence + fillers removed)")
    print(f"  - cleaned.words.json  (word-level timings)")
    print(f"  - cleaned.srt         (subtitles)")
    print(f"  - takes_packed.md     (phrase-level reading artifact)")
    print()
    print("Next:")
    print("  - Draft an EDL (see .claude/skills/video-editing/SKILL.md)")
    print(f"  - python3 studio.py render edl.json -o {out_dir}/final.mp4")
    print("  - Or open in Remotion: cd video_remotion && npm run start")


def cmd_render(args: argparse.Namespace) -> None:
    cmd = ["python3", str(PIPELINE / "render.py"), args.edl, "-o", args.output]
    if args.preview:
        cmd.append("--preview")
    if args.no_loudnorm:
        cmd.append("--no-loudnorm")
    run(cmd)


def cmd_pack(args: argparse.Namespace) -> None:
    run(
        ["python3", str(PIPELINE / "pack_transcripts.py"),
         "--edit-dir", str(Path(args.edit_dir).resolve())],
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Video editing studio entry point")
    subs = ap.add_subparsers(dest="command", required=True)

    p = subs.add_parser("prep", help="transcribe, cut silence + fillers, pack")
    p.add_argument("input")
    p.add_argument("--engine", choices=["whisper", "scribe"], default="whisper")
    p.add_argument("--model", default="base",
                   help="Whisper model size (whisper engine only)")
    p.add_argument("--cut-discourse", action="store_true",
                   help="Also cut like/you know/I mean/sort of")
    p.set_defaults(func=cmd_prep)

    p = subs.add_parser("render", help="render an EDL to final MP4")
    p.add_argument("edl")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--preview", action="store_true")
    p.add_argument("--no-loudnorm", action="store_true")
    p.set_defaults(func=cmd_render)

    p = subs.add_parser("pack", help="pack transcripts into takes_packed.md")
    p.add_argument("edit_dir")
    p.set_defaults(func=cmd_pack)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
