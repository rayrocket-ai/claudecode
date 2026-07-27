"""Render an EDL to a finished video.

Three stages: segments render in parallel, join without re-encoding, then a
single finishing pass burns captions and overlays and normalises loudness.

The parallel segment stage is the point of the whole design. On a CPU-only box
it is worth far more than any encoder tuning -- eight segments across eight
lanes finish in roughly the time of the longest one, not the sum. Joining is
free because every segment is rendered to identical parameters, which is why
:mod:`filters` is so insistent about `setsar`, `fps` and `aformat`.
"""

from __future__ import annotations

import concurrent.futures
import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .. import media
from ..edl import EDL
from ..hardware import Profile
from . import ass, emoji, filters

log = logging.getLogger("reelforge.render")


@dataclass
class RenderResult:
    output: Path
    edl_path: Path | None
    duration: float
    segments: int
    warnings: list[str]


class RenderError(RuntimeError):
    pass


def render(
    edl: EDL,
    dst: Path,
    profile: Profile,
    *,
    draft: bool = False,
    workdir: Path | None = None,
    keep_intermediates: bool = False,
) -> RenderResult:
    """Render ``edl`` to ``dst``."""
    if not edl.segments:
        raise RenderError("EDL has no segments")
    if not media.available():
        raise RenderError("ffmpeg/ffprobe not found -- run scripts/install.sh")

    src = Path(edl.source)
    if not src.exists():
        raise RenderError(f"source not found: {src}")

    info = media.probe(src)
    encode_args = profile.draft_args if draft else profile.final_args
    warnings: list[str] = []

    temp_root = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="reelforge-"))
    temp_root.mkdir(parents=True, exist_ok=True)
    segdir = temp_root / "segments"
    segdir.mkdir(exist_ok=True)

    try:
        parts = _render_segments(edl, src, info, segdir, encode_args, profile)
        joined = _concat(parts, temp_root)
        subtitle_file = _write_captions(edl, temp_root)
        overlays, overlay_warnings = _prepare_overlays(edl, temp_root)
        warnings += overlay_warnings

        dst.parent.mkdir(parents=True, exist_ok=True)
        media.run(filters.finish_cmd(
            str(joined), str(dst), edl.target,
            subtitles=_escape_for_filter(subtitle_file) if subtitle_file else None,
            overlays=overlays, encode_args=encode_args,
        ))
    finally:
        if not keep_intermediates and workdir is None:
            shutil.rmtree(temp_root, ignore_errors=True)

    return RenderResult(
        output=dst,
        edl_path=None,
        duration=edl.duration,
        segments=len(edl.segments),
        warnings=warnings,
    )


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------

def _render_segments(edl: EDL, src: Path, info: media.MediaInfo, segdir: Path,
                     encode_args: list[str], profile: Profile) -> list[Path]:
    jobs = []
    for index, seg in enumerate(edl.segments):
        dst = segdir / f"{index:04d}.mp4"
        cmd = filters.segment_cmd(
            str(src), seg, edl.framing_for(seg.id), edl.target, edl.audio,
            str(dst), src_w=info.width, src_h=info.height,
            has_audio=info.has_audio, encode_args=encode_args,
        )
        jobs.append((seg.id, cmd, dst))

    lanes = max(1, min(profile.render_parallelism, len(jobs)))
    log.info("rendering %d segments across %d lanes", len(jobs), lanes)

    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=lanes) as pool:
        futures = {pool.submit(media.run, cmd): seg_id for seg_id, cmd, _ in jobs}
        for future in concurrent.futures.as_completed(futures):
            seg_id = futures[future]
            try:
                future.result()
            except Exception as exc:
                failures.append(f"{seg_id}: {exc}")

    if failures:
        # Report every failed segment, not just the first. One malformed
        # timestamp usually means several, and fixing them one render at a
        # time is unbearable on long sources.
        raise RenderError("segment render failed:\n" + "\n".join(failures))

    missing = [str(dst) for _, _, dst in jobs if not dst.exists()]
    if missing:
        raise RenderError(f"ffmpeg reported success but wrote nothing: {missing}")
    return [dst for _, _, dst in jobs]


def _concat(parts: list[Path], temp_root: Path) -> Path:
    joined = temp_root / "joined.mp4"
    list_file = temp_root / "concat.txt"
    # The concat demuxer treats a single quote as a delimiter; its escape is the
    # unusual '\'' sequence rather than a backslash.
    list_file.write_text(
        "\n".join(f"file '{str(p).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'"
                  for p in parts) + "\n"
    )
    media.run(filters.concat_cmd(str(list_file), str(joined)))
    return joined


def _write_captions(edl: EDL, temp_root: Path) -> Path | None:
    if not edl.captions.enabled or not edl.captions.words:
        return None
    path = temp_root / "captions.ass"
    path.write_text(ass.build(edl.captions.words, edl.target, edl.captions.style),
                    encoding="utf-8")
    return path


def _prepare_overlays(edl: EDL, temp_root: Path):
    """Rasterise emoji overlays and resolve their positions."""
    cache_dir = temp_root / "emoji"
    size = int(edl.target.height * 0.09)
    prepared, warnings = [], []

    for overlay in edl.overlays:
        if overlay.type != "emoji":
            # Remotion and HyperFrames overlays land in phase 7; skipping them
            # loudly is better than rendering a video that silently lacks them.
            warnings.append(f"overlay type {overlay.type!r} not yet supported, skipped")
            continue

        png = emoji.render(overlay.glyph, size, cache_dir)
        if png is None:
            warnings.append(
                f"no colour emoji font for {overlay.glyph!r}; overlay skipped "
                "(install fonts-noto-color-emoji)"
            )
            continue

        base_x, base_y = filters.anchor_position(overlay.anchor, edl.target, size)
        if overlay.anim == "pop":
            x, y = emoji.pop_expressions(overlay.at, overlay.dur,
                                         int(base_x), int(base_y), size)
        else:
            x, y = base_x, base_y
        prepared.append((str(png), overlay.at, overlay.dur, x, y))

    return prepared, warnings


def _escape_for_filter(path: Path) -> str:
    """Escape a path for use inside a filter argument.

    ffmpeg parses filter arguments twice, so a colon or backslash in a path --
    ordinary on any absolute Windows path and possible anywhere -- terminates
    the option early and produces a baffling error.
    """
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
