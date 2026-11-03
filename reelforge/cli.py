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


def _load_env_file() -> None:
    """Read ``KEY=value`` lines from ``~/.reelforge/env`` into the environment.

    This is where the Anthropic key lives on the box: one file, mode 600,
    never pasted into a chat or a shell history. Values already in the
    environment win, so an explicit ``export`` still overrides the file.
    Nothing is ever printed -- not even which keys were found.
    """
    path = Path(os.environ.get("REELFORGE_ENV_FILE", "~/.reelforge/env")).expanduser()
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


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


def _warm(src: Path, cache, key: str, transcript, signals, profile):
    """Transcribe and analyse whatever is not cached yet. Returns both."""
    if transcript is None:
        from .core.transcribe import transcribe as run_transcribe

        audio = cache.path(key, "audio.wav")
        if not audio.exists():
            media.run(media.extract_audio_cmd(src, audio))
        result = run_transcribe(
            audio, model=profile.whisper_model, device=profile.whisper_device,
            compute_type=profile.whisper_compute, workers=profile.transcribe_workers,
        )
        cache.write_json(key, "words.json", result.as_dict())
        audio.unlink(missing_ok=True)
        transcript = Transcript.from_dict(result.as_dict())
    if signals is None:
        signals = analyze(src, cache, key)
    return transcript, signals


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

        _warm(src, cache, key, transcript, signals, profile)
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

    outdir = Path(args.outdir).expanduser() if args.outdir else _root() / "outbox"
    written = _compose_reels(src, transcript, signals, clips, book,
                             count=args.count, aspect=args.aspect, width=args.width,
                             fps=args.fps, outdir=outdir)
    print(json.dumps({"reels": written}, indent=2))
    return 0 if written else 1


def _compose_reels(src: Path, transcript, signals, clips, book, *, count: int,
                   aspect: str, width: int, fps: int, outdir: Path) -> list[dict]:
    """Rank clips, compose one EDL per reel, save them. Returns one row each."""
    chosen = highlights.rank(clips, count=count, target_seconds=book.target_seconds)
    outdir.mkdir(parents=True, exist_ok=True)
    stem = src.stem[:40]

    written = []
    for index, clip in enumerate(chosen, start=1):
        target = Target(platform="reels", aspect=aspect, width=width,
                        fps=fps, max_dur=book.max_seconds,
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
    return written


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

    outdir = Path(args.outdir).expanduser() if args.outdir else _root() / "outbox"
    edl, report = _produce_episode(src, cache, key, transcript, signals, episode,
                                   aspect=args.aspect, width=args.width,
                                   fps=args.fps, outdir=outdir)
    if edl is None:
        print("error: nothing survived the cuts", file=sys.stderr)
        return 1

    if not args.no_render:
        from .core.render import engine as engines

        engine_name, render_fn, engine_warnings = engines.choose(args.engine)
        result = render_fn(
            edl, outdir / f"{src.stem[:40]}-episode.mp4",
            hardware.profile(_root()), draft=args.draft)
        report["output"] = str(result.output)
        report["engine"] = engine_name
        report["warnings"] = engine_warnings + result.warnings

    print(json.dumps(report, indent=2))
    return 0


def _produce_episode(src: Path, cache, key: str, transcript, signals, episode, *,
                     aspect: str, width: int, fps: int, outdir: Path):
    """Compose an episode and write its EDL, subtitles and description.

    Returns ``(edl, report)``, or ``(None, {})`` when nothing survived.
    """
    book = load_playbook(_root() / "memory" / "playbook.md")
    target = Target(platform="youtube", aspect=aspect, width=width,
                    fps=fps, max_dur=None, loudness=-14.0)

    edl = compose_episode(episode, str(src), transcript, signals, target, book)
    if not edl.segments:
        return None, {}

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
    return edl, report


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
        from .core.render import engine as engines

        engine_name, render_fn, engine_warnings = engines.choose(args.engine)
        result = render_fn(edl, dst, profile, draft=args.draft)
        print(json.dumps({
            "output": str(result.output),
            "engine": engine_name,
            "duration": result.duration,
            "segments": result.segments,
            "draft": args.draft,
            "warnings": engine_warnings + result.warnings,
        }, indent=2))
        return 0

    report = _render_edl(edl_path, edl, dst, profile, draft=args.draft,
                         engine=args.engine, qc_passes=args.qc_passes)
    print(json.dumps(report, indent=2))
    return 0 if report["qc_clean"] else 1


def _render_edl(edl_path: Path, edl: EDL, dst: Path, profile, *, draft: bool,
                engine: str | None, qc_passes: int) -> dict:
    """Render with the QC repair loop and write the repaired EDL back."""
    # QC needs the transcript to check for mid-word cuts -- the single most
    # audible fault. Without it every other check still runs.
    transcript = None
    src = Path(edl.source)
    if src.exists():
        _, _, transcript, _ = _load_context(src)

    book = load_playbook(_root() / "memory" / "playbook.md")
    run = qc_mod.render_with_qc(edl, dst, profile, transcript=transcript,
                                book=book, draft=draft,
                                max_passes=qc_passes, engine=engine)

    # The repaired EDL is written back: it is what was actually rendered, and
    # leaving the old one on disk would make the EDL lie about the output.
    if run.changes:
        run.edl.save(edl_path)

    return {
        "output": str(run.output),
        "engine": run.engine,
        "duration": run.edl.duration,
        "segments": len(run.edl.segments),
        "draft": draft,
        "warnings": run.warnings,
        "qc_passes": run.passes,
        "qc_clean": run.clean,
        "repairs": run.changes,
        "remaining": [str(f) for f in run.findings],
    }


# --------------------------------------------------------------------------

def cmd_study(args) -> int:
    """Measure a reference video and report what it implies for the playbook."""
    import datetime as _dt
    import tempfile

    from .core import study

    src = Path(args.video)
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 2

    # The same memory edit, compose and feedback read. This used to default
    # to the repository's own memory/ folder, so a style learned with
    # --apply landed in a playbook no edit ever loaded.
    memory = Path(args.memory).expanduser() if args.memory else _root() / "memory"
    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="reelforge-study-"))
    when = _dt.date.today().isoformat()

    reading = study.measure(src, workdir, name=args.name, when=when)
    study.save(reading, memory)

    everything = study.load_all(memory)
    suggestions = study.suggest(everything)
    report = study.render_report(reading, suggestions, total_references=len(everything))

    reports = study.references_dir(memory)
    reports.mkdir(parents=True, exist_ok=True)
    report_path = reports / f"{reading.name}.md"
    report_path.write_text(report, encoding="utf-8")

    if args.apply:
        study.apply(suggestions, memory, when=when)

    if args.json:
        print(json.dumps({
            "reading": json.loads(reading.to_json()),
            "suggestions": [s.__dict__ for s in suggestions],
            "references": len(everything),
            "applied": bool(args.apply),
            "report": str(report_path),
            "frames": str(workdir),
        }, indent=2))
    else:
        print(report)
        print(f"report: {report_path}")
        print(f"frames: {workdir}")
        if args.apply:
            print(f"applied to {memory / 'playbook.md'}")
    return 0


def cmd_transcript(args) -> int:
    """Print a cached transcript the way the brain reads it.

    ``[mm:ss.s] text`` lines broken where the speaker pauses, plus the
    non-verbal signals -- exactly the material ``reelforge edit`` sends to the
    model, so a person (or the video-editor agent in Claude Code) can make the
    same decision by reading it.
    """
    from .core import agent as agent_mod

    src = Path(args.video).expanduser().resolve()
    _, _, transcript, signals = _load_context(src)
    if transcript is None:
        print("error: no transcript cached -- run `reelforge prepare --wait` first",
              file=sys.stderr)
        return 2
    print("## Signals\n")
    print(agent_mod.signals_summary(signals))
    print("\n## Transcript\n")
    print(agent_mod.transcript_text(transcript))
    return 0


def cmd_preview(args) -> int:
    """Open an edit in Remotion Studio to watch and scrub it in the browser."""
    import subprocess

    from .core.render import remotion_renderer as rm

    edl_path = Path(args.edl).expanduser().resolve()
    edl = EDL.load(edl_path)
    ok, why = rm.available()
    if not ok:
        print(f"error: {why}", file=sys.stderr)
        return 2

    workdir = _root() / ".preview" / edl_path.name.replace(".edl.json", "")
    props, public, warnings = rm.prepare_preview(edl, workdir)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    url = f"http://localhost:{args.port}/Edit"
    print(f"Opening {edl_path.name} in Remotion Studio at {url}")
    print("Play, scrub the timeline, and click any track to inspect it.")
    print("Press Ctrl+C here to close it.")
    try:
        subprocess.run(rm.preview_cmd(rm.project_dir(), props, public, port=args.port,
                                      open_browser=not args.no_open),
                       cwd=rm.project_dir())
    except KeyboardInterrupt:
        pass
    return 0


def cmd_edit(args) -> int:
    """The standalone editor agent: video in, finished edit out.

    One command does what ``/reels`` or ``/vlog`` do inside Claude Code --
    transcribe, let the brain decide, compose, render with QC -- by calling the
    Claude API directly. The brain's decision is written to disk *before*
    anything is composed, so it can be read, corrected, and replayed with
    ``--decision`` without paying for another call.
    """
    from .core import agent as agent_mod

    src = Path(args.video).expanduser().resolve()
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 2
    info = media.probe(src)
    if not info.has_audio:
        print("error: no audio track -- edits are cut from what is said, so "
              "there is nothing to work from here", file=sys.stderr)
        return 1

    profile = hardware.profile(_root())
    cache, key, transcript, signals = _load_context(src)
    if transcript is None or signals is None:
        print(f"transcribing {src.name} ({info.duration:.0f}s) -- the first run "
              "also downloads the speech model", file=sys.stderr)
        transcript, signals = _warm(src, cache, key, transcript, signals, profile)
    signals = signals or Signals(duration=transcript.duration)

    memory = _root() / "memory"
    book = load_playbook(memory / "playbook.md")
    if args.style:
        book.caption_style = args.style
    profile_path = memory / "style-profile.md"
    style_profile = profile_path.read_text(encoding="utf-8") if profile_path.exists() else None

    outdir = Path(args.outdir).expanduser() if args.outdir else _root() / "outbox"
    outdir.mkdir(parents=True, exist_ok=True)
    stem = src.stem[:40]
    brain = agent_mod.Brain(model=args.model)
    usage: dict = {"model": "replayed from --decision"}

    try:
        if args.mode == "reels":
            if args.decision:
                payload = json.loads(Path(args.decision).read_text())
                clips = highlights.parse(payload)
                if not clips:
                    print("error: no usable clips in the decision file", file=sys.stderr)
                    return 2
            else:
                decision = brain.find_clips(transcript, signals, count=args.count,
                                            book=book, style_profile=style_profile)
                payload, clips, usage = decision.payload, decision.clips, decision.usage()
            decision_path = outdir / f"{stem}-highlights.json"
            decision_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            rows = _compose_reels(src, transcript, signals, clips, book,
                                  count=args.count, aspect=args.aspect or "9:16",
                                  width=args.width or 1080, fps=args.fps, outdir=outdir)
            if not args.no_render:
                for row in rows:
                    edl_path = Path(row["edl"])
                    row["render"] = _render_edl(
                        edl_path, EDL.load(edl_path),
                        edl_path.with_suffix("").with_suffix(".mp4"), profile,
                        draft=args.draft, engine=args.engine, qc_passes=args.qc_passes)
            report = {"mode": "reels", "source": str(src),
                      "decision": str(decision_path), "usage": usage, "reels": rows}
            renders = [r["render"] for r in rows if "render" in r]
        else:
            if args.decision:
                payload = json.loads(Path(args.decision).read_text())
            else:
                decision = brain.shape_episode(transcript, signals,
                                               style_profile=style_profile)
                payload, usage = decision.payload, decision.usage()
            decision_path = outdir / f"{stem}-episode.json"
            decision_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            episode = Episode(payload)
            if args.no_cold_open:
                episode.cold_open = None
            edl, episode_report = _produce_episode(
                src, cache, key, transcript, signals, episode,
                aspect=args.aspect or "16:9", width=args.width or 1920,
                fps=args.fps, outdir=outdir)
            if edl is None:
                print("error: nothing survived the cuts", file=sys.stderr)
                return 1
            renders = []
            if not args.no_render:
                edl_path = Path(episode_report["edl"])
                episode_report["render"] = _render_edl(
                    edl_path, edl, outdir / f"{stem}-episode.mp4", profile,
                    draft=args.draft, engine=args.engine, qc_passes=args.qc_passes)
                renders = [episode_report["render"]]
            report = {"mode": "vlog", "source": str(src),
                      "decision": str(decision_path), "usage": usage, **episode_report}
    except agent_mod.AgentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report_path = outdir / f"{stem}-{args.mode}-report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report"] = str(report_path)
    print(json.dumps(report, indent=2))
    return 0 if all(r.get("qc_clean", True) for r in renders) else 1


def _text_arg(value: str | None) -> str:
    """A text option, or the contents of a file when given as @path."""
    if not value:
        return ""
    if value.startswith("@"):
        return Path(value[1:]).expanduser().read_text(encoding="utf-8")
    return value


def _style_profile() -> str | None:
    path = _root() / "memory" / "style-profile.md"
    return path.read_text(encoding="utf-8") if path.exists() else None


def cmd_post(args) -> int:
    """Lay out an edit as a post: showcase, explainer or full, with an end card."""
    from .core import agent as agent_mod
    from .core import brand as brand_mod
    from .core import post as post_mod

    edl_path = Path(args.edl).expanduser().resolve()
    edl = EDL.load(edl_path)
    brand = brand_mod.load(_root() / "memory")
    stem = edl_path.name.replace(".edl.json", "").replace(".json", "")
    spec_path = Path(args.spec).expanduser().resolve() if args.spec else None
    usage: dict = {"model": "spec given"}

    if spec_path is not None:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        base = spec_path.parent
    else:
        assets = [str(Path(a).expanduser().resolve()) for a in args.assets or []]
        missing = [a for a in assets if not Path(a).exists()]
        if missing:
            print("error: assets not found:\n  " + "\n  ".join(missing), file=sys.stderr)
            return 2
        try:
            decision = agent_mod.Brain(model=args.model).design_post(
                post_mod.post_request(edl, assets, keyword=args.keyword, offer=args.offer),
                style_profile=_style_profile())
        except agent_mod.AgentError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        spec, usage = decision.payload, decision.usage()
        spec_path = edl_path.with_name(f"{stem}.post.json")
        spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        base = None
    if args.format:
        spec["format"] = args.format
    if args.keyword and spec.get("end_card"):
        spec["end_card"]["keyword"] = args.keyword
    elif args.keyword:
        spec["end_card"] = {"keyword": args.keyword, "subtitle": args.offer or ""}

    try:
        laid_out, notes = post_mod.apply(edl, spec, brand, base=base)
    except post_mod.PostError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    problems = [p for p in validate(laid_out) if "exceeds the" not in p]
    out_path = edl_path.with_name(f"{stem}-{spec.get('format', 'full')}.edl.json")
    laid_out.save(out_path)
    report: dict = {"edl": str(out_path), "spec": str(spec_path), "format": spec.get("format"),
                    "why": spec.get("why", ""), "notes": notes, "problems": problems,
                    "usage": usage}
    if args.render:
        if problems:
            print(json.dumps(report, indent=2))
            print("error: the laid-out EDL has problems; not rendering", file=sys.stderr)
            return 2
        report["render"] = _render_edl(out_path, laid_out, out_path.with_suffix("").with_suffix(".mp4"),
                                       hardware.profile(_root()), draft=args.draft,
                                       engine=args.engine or "remotion", qc_passes=args.qc_passes)
    print(json.dumps(report, indent=2))
    return 0 if not problems else 1


def _reel_words(path: Path, profile) -> str:
    """What a reel says: from an EDL's captions, a text file, or a video's transcript."""
    from .core import agent as agent_mod
    from .core import post as post_mod

    if path.name.endswith(".json"):
        return post_mod.edit_text(EDL.load(path))
    if path.suffix.lower() in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    cache, key, transcript, signals = _load_context(path)
    if transcript is None:
        print(f"transcribing {path.name}", file=sys.stderr)
        transcript, _ = _warm(path, cache, key, transcript, signals, profile)
    return agent_mod.transcript_text(transcript)


def cmd_carousel(args) -> int:
    """Write and draw Instagram carousels, from a brief or from a reel that worked."""
    from .core import agent as agent_mod
    from .core import brand as brand_mod
    from .core import carousel as car

    memory = _root() / "memory"
    brand = brand_mod.load(memory)
    if args.handle:
        brand.handle = args.handle
    keyword = (args.keyword or "").strip().upper() or None
    outdir = Path(args.outdir).expanduser() if args.outdir else _root() / "outbox" / "carousels"
    usage: dict = {"model": "replayed from --decision"}

    if args.decision:
        payload = json.loads(Path(args.decision).expanduser().read_text(encoding="utf-8"))
        keyword = keyword or (payload.get("keyword") or "").upper() or None
    else:
        context = _text_arg(args.context)
        if not context and (memory / "context.md").exists():
            context = (memory / "context.md").read_text(encoding="utf-8")
        if args.from_reel:
            src = Path(args.from_reel).expanduser().resolve()
            if not src.exists():
                print(f"error: {src} not found", file=sys.stderr)
                return 2
            request = car.reel_request(transcript=_reel_words(src, hardware.profile(_root())),
                                       context=context, variants=args.variants,
                                       keyword=keyword, offer=args.offer)
        else:
            problem, idea = _text_arg(args.problem), _text_arg(args.idea)
            missing = [n for n, v in (("--problem", problem), ("--context", context),
                                      ("--idea", idea)) if not v.strip()]
            if missing:
                print("error: a carousel brief needs " + ", ".join(missing)
                      + " (or use --from-reel with a reel that performed). "
                      "--context defaults to ~/reelforge/memory/context.md.", file=sys.stderr)
                return 2
            request = car.brief_request(problem=problem, context=context, idea=idea,
                                        variants=args.variants, keyword=keyword, offer=args.offer)
        try:
            decision = agent_mod.Brain(model=args.model).write_carousel(
                request, style_profile=_style_profile())
        except agent_mod.AgentError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        payload, usage = decision.payload, decision.usage()

    try:
        plans, notes = car.parse(payload)
    except car.CarouselError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rows = []
    for n, plan in enumerate(plans, 1):
        folder = outdir / f"{n:02d}-{car.slug(plan.angle, f'carousel-{n}')}"
        car.save(plan, folder, keyword)
        row = {"folder": str(folder), "angle": plan.angle, "slides": len(plan.slides),
               "hook": plan.slides[0].headline.replace("*", "")}
        if not args.no_render:
            try:
                row["images"] = [str(p) for p in car.render(plan, folder, brand, keyword=keyword)]
            except car.CarouselError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
        rows.append(row)
    print(json.dumps({"carousels": rows, "keyword": keyword, "notes": notes, "usage": usage},
                     indent=2))
    return 0


def cmd_camera(args) -> int:
    """Plan a multicam shot list for footage shot from one angle."""
    from .core import camera

    edl_path = Path(args.edl).expanduser().resolve()
    edl = EDL.load(edl_path)
    src = Path(edl.source)
    if not src.exists():
        print(f"error: source not found: {src}", file=sys.stderr)
        return 2
    info = media.probe(src)
    _, _, _, signals = _load_context(src)
    if signals is None:
        print("note: no cached signals for this source -- framing on the frame centre. "
              "Run `reelforge prepare --wait` first for face-tracked shots.", file=sys.stderr)
    try:
        result = camera.plan(edl, info, signals, style=args.style, max_upscale=args.max_upscale,
                             src=None if args.no_detail else src, peek=args.peek)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    stem = edl_path.name.replace(".edl.json", "").replace(".json", "")
    out_path = edl_path.with_name(f"{stem}-camera.edl.json")
    problems = [p for p in validate(result.edl) if "exceeds the" not in p]
    result.edl.save(out_path)
    sizes: dict[str, int] = {}
    for f in result.edl.framing:
        for sh in f.shots:
            sizes[sh.size] = sizes.get(sh.size, 0) + 1
    report: dict = {"edl": str(out_path), "style": args.style, "shots": result.shots,
                    "sizes": sizes, "max_zoom": result.max_zoom, "notes": result.notes,
                    "problems": problems}
    if args.render and not problems:
        report["render"] = _render_edl(out_path, result.edl,
                                       out_path.with_suffix("").with_suffix(".mp4"),
                                       hardware.profile(_root()), draft=args.draft,
                                       engine=args.engine or "remotion", qc_passes=args.qc_passes)
    print(json.dumps(report, indent=2))
    return 0 if not problems else 1


def cmd_angles(args) -> int:
    """Hand shots to a generative video tool for new angles, and bring them back."""
    from .core import camera

    edl_path = Path(args.edl).expanduser().resolve()
    edl = EDL.load(edl_path)
    if not any(f.shots for f in edl.framing):
        print("error: this edit has no shot list -- run `reelforge camera` on it first",
              file=sys.stderr)
        return 2
    stem = edl_path.name.replace(".edl.json", "").replace(".json", "")
    folder = Path(args.dir).expanduser() if args.dir else edl_path.with_name(f"{stem}-angles")

    if args.action == "export":
        rows = camera.export_requests(edl, folder, count=args.count, location=args.location or "")
        print(json.dumps({"folder": str(folder), "requests": rows,
                          "next": "Generate each request in your video tool with its prompt, save the "
                                  "result into this folder under the same name (angle-01.mp4 ...), "
                                  f"then run: reelforge angles ingest {edl_path}"}, indent=2))
        return 0 if rows else 1

    manifest = folder / camera.MANIFEST
    if not manifest.exists():
        print(f"error: no {camera.MANIFEST} in {folder} -- run `reelforge angles export` first",
              file=sys.stderr)
        return 2
    results = Path(args.results).expanduser() if args.results else folder / "results"
    laid, notes = camera.ingest_angles(edl, manifest, results)
    out_path = edl_path.with_name(f"{stem}-angles.edl.json")
    laid.save(out_path)
    print(json.dumps({"edl": str(out_path), "notes": notes}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    _load_env_file()
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
    p.add_argument("--engine", choices=["auto", "remotion", "ffmpeg"], default=None,
                   help="renderer (default: auto -- Remotion when installed, else ffmpeg)")
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
    p.add_argument("--engine", choices=["auto", "remotion", "ffmpeg"], default=None,
                   help="renderer (default: auto -- Remotion when installed, else ffmpeg)")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("preview", help="open an edit in Remotion Studio to watch and scrub it")
    p.add_argument("edl")
    p.add_argument("--port", type=int, default=3000)
    p.add_argument("--no-open", action="store_true", help="do not open a browser")
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("transcript", help="print a cached transcript as the brain reads it")
    p.add_argument("video")
    p.set_defaults(func=cmd_transcript)

    p = sub.add_parser("edit", help="the standalone editor agent: video in, finished edit out")
    p.add_argument("video")
    p.add_argument("--mode", choices=["reels", "vlog"], default="reels",
                   help="reels: extract the best moments; vlog: tighten into an episode")
    p.add_argument("--count", type=int, default=3, help="reels to make")
    p.add_argument("--style", default=None, help="caption style: karaoke-bold, clean, punch")
    p.add_argument("--aspect", default=None, help="default 9:16 for reels, 16:9 for vlog")
    p.add_argument("--width", type=int, default=None)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--outdir", default=None)
    p.add_argument("--draft", action="store_true", help="fast encode for review")
    p.add_argument("--no-render", action="store_true", help="decide and compose only")
    p.add_argument("--no-cold-open", action="store_true")
    p.add_argument("--qc-passes", type=int, default=3)
    p.add_argument("--engine", choices=["auto", "remotion", "ffmpeg"], default=None,
                   help="renderer (default: auto -- Remotion when installed, else ffmpeg)")
    p.add_argument("--model", default=None,
                   help="Claude model for the editing decisions (default: $REELFORGE_MODEL "
                        "or claude-opus-5-5)")
    p.add_argument("--decision", default=None,
                   help="replay a saved highlights/episode JSON instead of calling the API")
    p.set_defaults(func=cmd_edit)

    p = sub.add_parser("post", help="lay out an edit as a post: showcase, explainer or full, with an end card")
    p.add_argument("edl")
    p.add_argument("--spec", default=None,
                   help="a post spec JSON (written by hand or by the post-designer agent); "
                        "without it Claude designs one from the edit and --assets")
    p.add_argument("--assets", nargs="*", default=None,
                   help="images/videos the designer may place in the top panel")
    p.add_argument("--format", choices=["showcase", "explainer", "full"], default=None,
                   help="override the spec's format")
    p.add_argument("--keyword", default=None, help="end-card comment keyword, e.g. EDIT")
    p.add_argument("--offer", default=None, help="what commenters get, for the end card")
    p.add_argument("--render", action="store_true", help="render the laid-out edit")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--qc-passes", type=int, default=3)
    p.add_argument("--engine", choices=["auto", "remotion", "ffmpeg"], default=None,
                   help="default remotion: the split layout and end card are drawn there")
    p.add_argument("--model", default=None)
    p.set_defaults(func=cmd_post)

    p = sub.add_parser("carousel", help="write and draw Instagram carousels")
    p.add_argument("--problem", default=None, help="the audience's problem (text or @file)")
    p.add_argument("--context", default=None,
                   help="who you are and what you sell (text or @file; "
                        "default ~/reelforge/memory/context.md)")
    p.add_argument("--idea", default=None,
                   help="a carousel idea that already worked (text or @file)")
    p.add_argument("--from-reel", default=None,
                   help="a reel that performed: video, EDL, or transcript .txt")
    p.add_argument("--variants", type=int, default=3, help="carousels to write, each a different angle")
    p.add_argument("--keyword", default=None, help="comment keyword for the last slide")
    p.add_argument("--offer", default=None, help="what commenters get")
    p.add_argument("--handle", default=None, help="override brand.json's handle for this run")
    p.add_argument("--outdir", default=None, help="default ~/reelforge/outbox/carousels")
    p.add_argument("--decision", default=None,
                   help="render a saved carousel JSON instead of calling the API")
    p.add_argument("--no-render", action="store_true", help="write the copy only")
    p.add_argument("--model", default=None)
    p.set_defaults(func=cmd_carousel)

    p = sub.add_parser("camera", help="a multicam shot list for footage shot from one angle")
    p.add_argument("edl")
    p.add_argument("--style", choices=["multicam", "documentary", "cinematic"], default="multicam")
    p.add_argument("--max-upscale", type=float, default=2.6,
                   help="sharpest magnification of the source allowed for close-ups")
    p.add_argument("--no-detail", action="store_true", help="skip detail shots of moving hands")
    p.add_argument("--peek", action="store_true",
                   help="add a soft dark foreground edge to some wide shots (off by default: "
                        "without a real object in frame it reads as a smudge)")
    p.add_argument("--render", action="store_true")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--qc-passes", type=int, default=3)
    p.add_argument("--engine", choices=["auto", "remotion", "ffmpeg"], default=None,
                   help="default remotion: shots inside segments are drawn there")
    p.set_defaults(func=cmd_camera)

    p = sub.add_parser("angles", help="AI-generated camera angles: export requests, ingest results")
    p.add_argument("action", choices=["export", "ingest"])
    p.add_argument("edl", help="an edit with a shot list (from `reelforge camera`)")
    p.add_argument("--count", type=int, default=3, help="shots to regenerate (export)")
    p.add_argument("--location", default=None,
                   help="put the speaker somewhere else, e.g. 'a penthouse with an ocean view'")
    p.add_argument("--dir", default=None, help="default: <edit>-angles/ beside the EDL")
    p.add_argument("--results", default=None, help="where generated clips are (default <dir>/results)")
    p.set_defaults(func=cmd_angles)

    p = sub.add_parser("study", help="learn a style from a reference video")
    p.add_argument("video")
    p.add_argument("--name", help="short name for the reference (default: file stem)")
    p.add_argument("--memory", default=None,
                   help="default: ~/reelforge/memory, shared with edit and feedback")
    p.add_argument("--workdir", help="where sampled frames go (default: temp dir)")
    p.add_argument("--apply", action="store_true",
                   help="write the suggested values into playbook.md with provenance")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_study)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (media.FFmpegError, ffmpeg_renderer.RenderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
