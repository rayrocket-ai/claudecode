"""Command-line entry point.

Slash commands, the MCP server (phase 9), and the watcher are all thin wrappers
over the same functions in ``core``. This module is one of those wrappers -- it
must not contain editorial logic, only argument handling and reporting.

    reelforge prepare  <video>
    reelforge compose  <video> --highlights h.json --count 3
    reelforge render   <edl.json> [--draft]
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
from .core import feedback as fb
from .core import qc as qc_mod
from .core.render import ffmpeg_renderer
from .core.transcribe import Transcript
from .core import metadata as meta
from .core.vlog import Episode, compose_episode


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
# vlog
# --------------------------------------------------------------------------

def cmd_vlog(args) -> int:
    src = Path(args.video).expanduser().resolve()
    cache, key, transcript, signals = _load_context(src)

    if transcript is None:
        print("error: no transcript cached -- run `prepare --wait` first",
              file=sys.stderr)
        return 2
    signals = signals or Signals(duration=transcript.duration)

    episode = Episode(json.loads(Path(args.episode).read_text()))
    if args.no_cold_open:
        episode.cold_open = None

    book = load_playbook(_root() / "memory" / "playbook.md")
    target = Target(platform="youtube", aspect=args.aspect, width=args.width,
                    fps=args.fps, max_dur=None, loudness=-14.0)

    edl = compose_episode(episode, str(src), transcript, signals, target, book)
    if not edl.segments:
        print("error: nothing survived the cuts", file=sys.stderr)
        return 1

    outdir = Path(args.outdir).expanduser() if args.outdir else _root() / "outbox"
    outdir.mkdir(parents=True, exist_ok=True)
    stem = src.stem[:40]

    cold_open_len = (edl.segments[0].out_duration
                     if edl.segments and edl.segments[0].id == "cold" else 0.0)

    edl_path = edl.save(outdir / f"{stem}-episode.edl.json")
    problems = validate(edl, source_duration=transcript.duration)

    subs = meta.srt(edl)
    srt_path = None
    if subs:
        srt_path = outdir / f"{stem}-episode.srt"
        srt_path.write_text(subs, encoding="utf-8")

    chapters = meta.chapter_text(edl)
    desc = meta.description(edl, summary=episode.description, tags=episode.tags)
    (outdir / f"{stem}-episode.description.txt").write_text(desc, encoding="utf-8")

    frames = sorted((cache.dir_for(key) / "frames").glob("f-*.jpg"))
    thumbs = meta.thumbnail_candidates(frames, every_seconds=5.0)

    report = {
        "edl": str(edl_path),
        "srt": str(srt_path) if srt_path else None,
        "source_duration": round(transcript.duration, 1),
        "edit_duration": edl.duration,
        # A cold open *adds* time by replaying a moment, so comparing the edit
        # against the source understates what was actually cut -- and on a
        # heavily trimmed episode it can read as though nothing came out.
        "cold_open_seconds": round(cold_open_len, 1),
        "removed_from_body": round(
            transcript.duration - (edl.duration - cold_open_len), 1),
        "segments": len(edl.segments),
        "cold_open": cold_open_len > 0,
        "chapters": chapters.splitlines(),
        # An empty list when the producer supplied chapters means cutting
        # collapsed them below YouTube's minimum. Called out explicitly:
        # YouTube's own failure here is completely silent.
        "chapters_rejected": bool(episode.chapters) and not chapters,
        "chapters_rejected_why": (
            f"{len(episode.chapters)} proposed, but a {edl.duration:.0f}s edit "
            "cannot hold 3 chapters at 10s spacing"
        ) if episode.chapters and not chapters else None,
        "broll": [{"at": b.start, "dur": b.dur, "prompt": b.prompt} for b in edl.broll],
        "thumbnails": [{"at": t.at, "score": t.score, "why": t.reasons,
                        "path": str(t.path)} for t in thumbs],
        "title": episode.title,
        "problems": problems,
    }

    if not args.no_render:
        result = ffmpeg_renderer.render(
            edl, outdir / f"{stem}-episode.mp4",
            hardware.profile(_root()), draft=args.draft)
        report["output"] = str(result.output)
        report["warnings"] = result.warnings

    print(json.dumps(report, indent=2))
    return 0


# --------------------------------------------------------------------------
# watch
# --------------------------------------------------------------------------

def cmd_watch(args) -> int:
    """Run the inbox watcher.

    Exposed through the CLI so the systemd unit has one stable command to call
    rather than a module path that depends on the working directory.
    """
    from .server.watcher import main as watch_main

    argv = ["--root", str(args.root or _root()), "--settle", str(args.settle)]
    if args.once:
        argv.append("--once")
    return watch_main(argv)


# --------------------------------------------------------------------------
# feedback
# --------------------------------------------------------------------------

def cmd_feedback(args) -> int:
    import datetime

    memory = _root() / "memory"
    log = memory / "decisions.jsonl"

    parsed: list[fb.Note] = []
    for raw in args.note:
        parts = raw.split(":", 2)
        if len(parts) < 2:
            print(f"error: {raw!r} is not aspect:direction[:quote]", file=sys.stderr)
            return 2
        aspect, direction = parts[0].strip(), parts[1].strip()
        quote = parts[2].strip() if len(parts) > 2 else ""
        try:
            fb.validate_note(aspect, direction)
        except fb.UnknownCorrection as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        parsed.append(fb.Note(aspect=aspect, direction=direction, quote=quote,
                              edl=args.edl or "", origin=args.origin))

    for note in parsed:
        fb.append(log, note)

    book = load_playbook(memory / "playbook.md")
    when = args.when or datetime.date.today().isoformat()
    book, promotions = fb.apply_feedback(memory, book, when=when)

    waiting = fb.pending(fb.load(log))
    print(json.dumps({
        "recorded": [f"{n.aspect}/{n.direction}" for n in parsed],
        "applied": [{
            "rule": p.field,
            "from": p.before,
            "to": p.after,
            "means": p.describe,
            "heard": p.occurrences,
        } for p in promotions],
        # Surfaced explicitly: nothing changes the first time something is
        # said, and without being told, that reads as having been ignored.
        "waiting_for_a_second_mention": waiting,
        "playbook": str(memory / "playbook.md"),
    }, indent=2))
    return 0


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

def cmd_render(args) -> int:
    edl_path = Path(args.edl).expanduser().resolve()
    edl = EDL.load(edl_path)

    # Validation only blocks when QC is off. With QC on, most of what validate()
    # rejects -- flash shots, over-length, bad boundaries -- is precisely what
    # the repair loop exists to fix, so refusing to start would make the safety
    # net unreachable.
    if args.no_qc:
        problems = validate(edl)
        blocking = [p for p in problems if "exceeds the" not in p]
        if blocking:
            print("error: EDL has problems:\n  " + "\n  ".join(blocking),
                  file=sys.stderr)
            print("\nDrop --no-qc to let the repair loop fix these.",
                  file=sys.stderr)
            return 2

    dst = Path(args.out).expanduser() if args.out else edl_path.with_suffix("").with_suffix(".mp4")
    profile = hardware.profile(_root())

    if args.no_qc:
        result = ffmpeg_renderer.render(edl, dst, profile, draft=args.draft)
        print(json.dumps({
            "output": str(result.output),
            "duration": result.duration,
            "segments": result.segments,
            "draft": args.draft,
            "warnings": result.warnings,
        }, indent=2))
        return 0

    # QC needs the transcript to check for mid-word cuts -- the single most
    # audible fault. Without it every other check still runs.
    transcript = None
    src = Path(edl.source)
    if src.exists():
        _, _, transcript, _ = _load_context(src)

    book = load_playbook(_root() / "memory" / "playbook.md")
    run = qc_mod.render_with_qc(edl, dst, profile, transcript=transcript,
                                book=book, draft=args.draft,
                                max_passes=args.qc_passes)

    # The repaired EDL is written back: it is what was actually rendered, and
    # leaving the old one on disk would make the EDL lie about the output.
    if run.changes:
        run.edl.save(edl_path)

    print(json.dumps({
        "output": str(run.output),
        "duration": run.edl.duration,
        "segments": len(run.edl.segments),
        "draft": args.draft,
        "qc_passes": run.passes,
        "qc_clean": run.clean,
        "repairs": run.changes,
        "remaining": [str(f) for f in run.findings],
    }, indent=2))
    return 0 if run.clean else 1


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

    p = sub.add_parser("vlog", help="compose and render a long-form episode")
    p.add_argument("video")
    p.add_argument("--episode", required=True)
    p.add_argument("--no-cold-open", action="store_true")
    p.add_argument("--no-render", action="store_true",
                   help="write the EDL and metadata without encoding")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--outdir", default=None)
    p.set_defaults(func=cmd_vlog)

    p = sub.add_parser("watch", help="run the inbox watcher (used by systemd)")
    p.add_argument("--root", type=Path, default=None)
    p.add_argument("--once", action="store_true")
    p.add_argument("--settle", type=float, default=30.0)
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("feedback", help="record a critique and update the playbook")
    p.add_argument("--note", action="append", default=[], required=True,
                   metavar="ASPECT:DIRECTION[:QUOTE]",
                   help="e.g. captions:too-low:\"they sat too low\"")
    p.add_argument("--edl", default=None)
    p.add_argument("--origin", default="user", choices=["user", "qc"])
    p.add_argument("--when", default=None, help="date for provenance")
    p.set_defaults(func=cmd_feedback)

    p = sub.add_parser("render", help="render an EDL to video")
    p.add_argument("edl")
    p.add_argument("--out", default=None)
    p.add_argument("--draft", action="store_true",
                   help="fast encode for review; use the default for finals")
    p.add_argument("--no-qc", action="store_true",
                   help="skip inspection and repair")
    p.add_argument("--qc-passes", type=int, default=3)
    p.set_defaults(func=cmd_render)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (media.FFmpegError, ffmpeg_renderer.RenderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
