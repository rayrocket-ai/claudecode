"""Command-line entry point.

Slash commands, the MCP server (phase 9), and the watcher are all thin wrappers
over the same functions in ``core``. This module is one of those wrappers -- it
must not contain editorial logic, only argument handling and reporting.

    python3 -m reelforge.cli prepare  <video>
    python3 -m reelforge.cli compose  <video> --highlights h.json --count 3
    python3 -m reelforge.cli render   <edl.json> [--draft]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .core import compose as composer
from .core import hardware, highlights, media
from .core.analyze import Signals, analyze
from .core.cache import Cache, content_key
from .core.edl import EDL, Target, validate
from .core.playbook import load as load_playbook
from .core.render import ffmpeg_renderer
from .core.transcribe import Transcript


def _root() -> Path:
    return Path(os.environ.get("REELFORGE_ROOT", "~/reelforge")).expanduser()


def _load_context(src: Path):
    """Cache, key, transcript and signals for a source. None where absent."""
    cache = Cache(_root() / ".cache")
    key = content_key(src)
    words = cache.read_json(key, "words.json")
    signals = cache.read_json(key, "signals.json")
    return (
        cache,
        key,
        Transcript.from_dict(words) if words else None,
        Signals.from_dict(signals) if signals else None,
    )


# --------------------------------------------------------------------------
# prepare
# --------------------------------------------------------------------------

def cmd_prepare(args) -> int:
    src = Path(args.video).expanduser().resolve()
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 2

    cache, key, transcript, signals = _load_context(src)
    profile = hardware.profile(_root())
    info = media.probe(src)

    report = {
        "source": str(src),
        "key": key,
        "duration": round(info.duration, 2),
        "resolution": f"{info.width}x{info.height}",
        "has_audio": info.has_audio,
        "transcript_ready": transcript is not None,
        "signals_ready": signals is not None,
    }

    if not info.has_audio:
        report["note"] = ("no audio track -- reels are cut from what is said, "
                          "so there is nothing to work from here")
        print(json.dumps(report, indent=2))
        return 1

    if transcript is None or signals is None:
        # Estimate before starting, so the caller can decide whether to wait.
        rate = 8.0 if profile.whisper_device == "cpu" else 40.0
        report["estimated_seconds"] = int(info.duration / rate)
        print(json.dumps(report, indent=2))

        if not args.wait:
            print("\nnot warm yet. Re-run with --wait to transcribe now, or "
                  "let the watcher pick it up.", file=sys.stderr)
            return 1

        from .core.transcribe import transcribe as run_transcribe
        if transcript is None:
            audio = cache.path(key, "audio.wav")
            if not audio.exists():
                media.run(media.extract_audio_cmd(src, audio))
            result = run_transcribe(
                audio, model=profile.whisper_model, device=profile.whisper_device,
                compute_type=profile.whisper_compute, workers=profile.transcribe_workers,
            )
            cache.write_json(key, "words.json", result.as_dict())
            audio.unlink(missing_ok=True)
        if signals is None:
            analyze(src, cache, key)
        report["transcript_ready"] = report["signals_ready"] = True

    print(json.dumps(report, indent=2))
    return 0


# --------------------------------------------------------------------------
# compose
# --------------------------------------------------------------------------

def cmd_compose(args) -> int:
    src = Path(args.video).expanduser().resolve()
    cache, key, transcript, signals = _load_context(src)

    if transcript is None:
        print("error: no transcript cached -- run `prepare --wait` first",
              file=sys.stderr)
        return 2
    signals = signals or Signals(duration=transcript.duration)

    payload = json.loads(Path(args.highlights).read_text())
    clips = highlights.parse(payload)
    if not clips:
        print("error: no usable clips in the highlights file", file=sys.stderr)
        return 2

    book = load_playbook(_root() / "memory" / "playbook.md")
    if args.style:
        book.caption_style = args.style

    chosen = highlights.rank(clips, count=args.count,
                             target_seconds=book.target_seconds)

    outdir = Path(args.outdir).expanduser() if args.outdir else _root() / "outbox"
    outdir.mkdir(parents=True, exist_ok=True)
    stem = src.stem[:40]

    written = []
    for index, clip in enumerate(chosen, start=1):
        target = Target(platform="reels", aspect=args.aspect, width=args.width,
                        fps=args.fps, max_dur=book.max_seconds,
                        loudness=book.loudness)
        edl = composer.compose(clip, str(src), transcript, signals, target, book)

        problems = validate(edl, source_duration=transcript.duration)
        if not edl.segments:
            print(f"  skipped clip {index}: nothing survived the cuts",
                  file=sys.stderr)
            continue

        path = outdir / f"{stem}-reel{index}.edl.json"
        edl.save(path)
        written.append({
            "rank": index,
            "edl": str(path),
            "hook": clip.hook,
            "why": clip.why,
            "score": clip.score(target_seconds=book.target_seconds),
            "duration": edl.duration,
            "segments": len(edl.segments),
            "cuts": [f"{d.reason} {d.start:.1f}-{d.end:.1f}" for d in clip.drop],
            "problems": problems,
        })

    print(json.dumps({"reels": written}, indent=2))
    return 0 if written else 1


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

def cmd_render(args) -> int:
    edl_path = Path(args.edl).expanduser().resolve()
    edl = EDL.load(edl_path)

    problems = validate(edl)
    blocking = [p for p in problems if "exceeds the" not in p]
    if blocking:
        print("error: EDL has problems:\n  " + "\n  ".join(blocking), file=sys.stderr)
        return 2

    dst = Path(args.out).expanduser() if args.out else edl_path.with_suffix("").with_suffix(".mp4")
    profile = hardware.profile(_root())

    result = ffmpeg_renderer.render(edl, dst, profile, draft=args.draft)
    print(json.dumps({
        "output": str(result.output),
        "duration": result.duration,
        "segments": result.segments,
        "draft": args.draft,
        "warnings": result.warnings,
    }, indent=2))
    return 0


# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reelforge")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="probe and warm the cache for a source")
    p.add_argument("video")
    p.add_argument("--wait", action="store_true",
                   help="transcribe now instead of leaving it to the watcher")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("compose", help="rank highlights and write EDLs")
    p.add_argument("video")
    p.add_argument("--highlights", required=True)
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--style", default=None)
    p.add_argument("--aspect", default="9:16")
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--outdir", default=None)
    p.set_defaults(func=cmd_compose)

    p = sub.add_parser("render", help="render an EDL to video")
    p.add_argument("edl")
    p.add_argument("--out", default=None)
    p.add_argument("--draft", action="store_true",
                   help="fast encode for review; use the default for finals")
    p.set_defaults(func=cmd_render)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (media.FFmpegError, ffmpeg_renderer.RenderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
