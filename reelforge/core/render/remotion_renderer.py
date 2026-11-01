"""Render an EDL with Remotion.

The default engine. Remotion draws each frame as a React composition in a
headless browser, which buys what an ffmpeg filter graph cannot do well:
spring physics on graphics, real typography on captions, colour emoji drawn
natively, and motion that can be reasoned about as code.

The division of labour is strict. **Python decides, Remotion draws.** Every
decision -- which source frames survive, where the crop window sits, when each
caption card appears and which word is lit, when the music ducks -- is resolved
here into frame numbers, using the *same* functions the ffmpeg engine uses
(``filters.crop_window``, ``ass.group_words``, the transition-boundary rule).
The composition in ``reelforge/remotion/`` receives finished numbers and draws
them. That is what makes the two engines frame shots identically, and what
keeps QC repairing the EDL rather than the pixels.

Two stages after the browser:

1. ``remotion render`` produces the picture and a mixed audio track.
2. One ffmpeg pass normalises loudness with the video stream copied, not
   re-encoded. Remotion has no loudness normaliser, and the platform target
   (-16 LUFS short-form, -14 YouTube) is part of the EDL's contract.

Costs, stated plainly: a browser screenshotting every frame is slower than an
ffmpeg filter graph -- roughly two to four minutes for a 30-second reel on a
4-core box, under a minute on an Apple Silicon Mac. When Remotion is not
installed the renderer says so and :mod:`engine` falls back to ffmpeg; it
never silently renders a different-looking video.
"""

from __future__ import annotations

import json
import zlib
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path

from .. import media
from ..edl import EDL, CaptionWord
from ..hardware import Profile
from . import ass, filters, sfx
from .ffmpeg_renderer import RenderError, RenderResult, _transition_boundaries

log = logging.getLogger("reelforge.render.remotion")

#: The Remotion project. In the repository, next to the Python package, so it
#: versions with everything else.
DEFAULT_PROJECT = Path(__file__).resolve().parents[2] / "remotion"

#: Overlay compositions the Edit composition can draw inline, under both the
#: HyperFrames spelling and the Remotion component spelling.
GRAPHIC_ALIASES = {
    "lower-third": "lower-third", "LowerThird": "lower-third",
    "callout": "callout", "Callout": "callout",
    "kinetic": "kinetic", "Kinetic": "kinetic",
    "progress": "progress", "Progress": "progress",
}

#: Emoji size as a fraction of frame height -- the same as the ffmpeg engine.
EMOJI_SIZE = 0.09
#: Speech closer together than this is one window for ducking. Without the
#: merge the music would swell back up between every pair of words.
SPEECH_MERGE_GAP = 0.35
#: How far the music drops under speech. A sidechain compressor at the
#: ffmpeg engine's 9:1 ratio lands in the same place on typical dialogue.
DUCK_DB = 12.0

FONT_STACK = 'Inter, "DejaVu Sans", "Noto Sans", system-ui, sans-serif'


class RemotionUnavailable(RenderError):
    """Remotion cannot run here. The message must say how to fix it."""


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------

def project_dir() -> Path:
    explicit = os.environ.get("REELFORGE_REMOTION_DIR")
    return Path(explicit) if explicit else DEFAULT_PROJECT


def find_browser() -> Path | None:
    """A Chrome *headless shell*, if one is installed.

    Specifically the headless shell, not desktop Chrome. Chrome removed the old
    headless mode from its main binary in version 132, and Remotion drives the
    browser in that mode -- point it at desktop Chrome and the browser dies on
    launch with nothing more useful than "Closed with 1 signal". That exact
    failure cost a session before it was understood.

    Returns ``None`` when there is none, in which case Remotion downloads its
    own copy on first render (once, ~100 MB) -- fine on a Mac or a server,
    impossible on a network that blocks remotion.media.
    """
    explicit = os.environ.get("REELFORGE_REMOTION_BROWSER")
    if explicit and Path(explicit).exists():
        return Path(explicit)
    root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    candidates: list[Path] = []
    if root:
        base = Path(root)
        candidates += sorted(base.glob("chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell"))
        candidates += sorted(base.glob("chromium_headless_shell-*/chrome-linux/headless_shell"))
    return candidates[-1] if candidates else None


def available(project: Path | None = None) -> tuple[bool, str]:
    """Whether the Remotion engine can run, and if not, how to fix it."""
    project = project or project_dir()
    if shutil.which("npx") is None:
        return False, ("Node.js is not installed (no npx). Install Node 18+ "
                       "(brew install node, or apt install nodejs).")
    if not (project / "node_modules" / "remotion").is_dir():
        return False, (f"Remotion packages are not installed in {project}. "
                       f"Run: cd {project} && npm install")
    if not (project / "src" / "index.ts").is_file():
        return False, f"no Remotion entry point at {project / 'src' / 'index.ts'}"
    return True, "ok"


# --------------------------------------------------------------------------
# small pure helpers
# --------------------------------------------------------------------------

def frames(seconds: float, fps: float) -> int:
    return int(round(seconds * fps))


def ass_colour_to_css(value: str) -> str:
    """ASS colours are ``&HAABBGGRR`` -- blue first. CSS wants ``#RRGGBB``."""
    raw = value.strip().lstrip("&").lstrip("Hh").rjust(8, "0")[-8:]
    bb, gg, rr = raw[2:4], raw[4:6], raw[6:8]
    return f"#{rr}{gg}{bb}".upper()


def speech_windows(words: list[CaptionWord], *, gap: float = SPEECH_MERGE_GAP
                   ) -> list[tuple[float, float]]:
    """Spans of output time where someone is speaking, short gaps merged."""
    spans: list[tuple[float, float]] = []
    for word in sorted(words, key=lambda w: w.start):
        if spans and word.start - spans[-1][1] <= gap:
            spans[-1] = (spans[-1][0], max(spans[-1][1], word.end))
        else:
            spans.append((word.start, word.end))
    return spans


VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


def _even_px(value: float) -> int:
    return int(round(value / 2)) * 2


def db_to_linear(db: float) -> float:
    return round(10 ** (db / 20.0), 5)


# --------------------------------------------------------------------------
# staging assets into the job's public dir
# --------------------------------------------------------------------------

@dataclass
class Staged:
    """Files placed where the composition can load them, by public name."""

    public: Path
    source: str = ""
    music: str | None = None
    sfx: dict[str, str] = field(default_factory=dict)
    broll: dict[int, str] = field(default_factory=dict)
    assets: dict[str, str] = field(default_factory=dict)
    """Top-panel images, videos and prompt results, original path -> public name."""
    warnings: list[str] = field(default_factory=list)


def _place(src: Path, dst: Path) -> None:
    """Hard-link when possible, copy otherwise.

    Remotion's bundler copies the public dir into each bundle. A hard link
    makes that copy free for a multi-gigabyte source; a symlink would not
    survive the copy. Copy is the fallback across filesystems.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def stage(edl: EDL, job: Path) -> Staged:
    public = job / "public"
    public.mkdir(parents=True, exist_ok=True)
    staged = Staged(public=public)

    source = Path(edl.source)
    staged.source = f"source{source.suffix.lower() or '.mp4'}"
    _place(source, public / staged.source)

    if edl.audio.music:
        music = Path(edl.audio.music)
        if music.exists():
            # Looped and trimmed to the edit's exact length up front, so the
            # composition plays one file once and its volume curve maps
            # one-to-one onto output frames -- no reasoning about how a looped
            # player numbers frames on its second pass.
            staged.music = "music.wav"
            media.run([
                "ffmpeg", "-hide_banner", "-nostdin", "-y",
                "-stream_loop", "-1", "-i", str(music),
                "-t", f"{edl.duration:.3f}", "-ac", "2", "-ar", "48000",
                "-c:a", "pcm_s16le", str(public / staged.music),
            ])
        else:
            staged.warnings.append(f"music bed not found: {music}")

    cache = job / "sfx-cache"
    for cue in edl.sfx:
        if cue.name in staged.sfx:
            continue
        try:
            wav = sfx.render(cue.name, cache)
        except sfx.UnknownEffect as exc:
            staged.warnings.append(str(exc))
            continue
        name = f"sfx-{cue.name}.wav"
        _place(wav, public / name)
        staged.sfx[cue.name] = name

    for clip in edl.layout.top:
        for raw in (clip.asset, clip.result):
            if not raw or raw in staged.assets:
                continue
            path = Path(raw)
            if not path.exists():
                staged.warnings.append(f"top-panel asset not found: {path}")
                continue
            name = f"top-{len(staged.assets)}{path.suffix.lower() or '.png'}"
            _place(path, public / name)
            staged.assets[raw] = name

    for framing in edl.framing:
        for shot in framing.shots:
            raw = shot.angle
            if not raw or raw in staged.assets:
                continue
            path = Path(raw)
            if not path.exists():
                staged.warnings.append(f"generated angle not found, shot falls back to "
                                       f"the source framing: {path}")
                continue
            name = f"angle-{len(staged.assets)}{path.suffix.lower() or '.mp4'}"
            _place(path, public / name)
            staged.assets[raw] = name

    for index, slot in enumerate(edl.broll):
        if not slot.source:
            continue
        path = Path(slot.source)
        if not path.exists():
            staged.warnings.append(f"b-roll source not found: {path}")
            continue
        name = f"broll-{index}{path.suffix.lower() or '.mp4'}"
        _place(path, public / name)
        staged.broll[index] = name

    return staged


# --------------------------------------------------------------------------
# EDL -> props
# --------------------------------------------------------------------------

def _window(info: media.MediaInfo, region, focus: tuple[float, float], zoom: float) -> dict:
    fx = min(1.0, max(0.0, focus[0]))
    fy = min(1.0, max(0.0, focus[1]))
    w = filters.crop_window(info.width, info.height, region, (fx, fy), max(1.0, zoom))
    return {"x": w.x, "y": w.y, "w": w.w, "h": w.h}


def shot_states(shot) -> tuple[tuple[float, float], float, tuple[float, float], float]:
    """(focus, zoom) at the shot's first and last frame, from its move."""
    f0 = tuple(shot.focus)
    z0 = shot.zoom
    a = shot.amount
    if shot.move in ("push", "punch"):
        return f0, z0, f0, z0 * (1 + a)
    if shot.move == "pull":
        return f0, z0 * (1 + a), f0, z0
    if shot.move == "pan":
        return (f0[0] - a / 2, f0[1]), z0, (f0[0] + a / 2, f0[1]), z0
    if shot.move == "tilt":
        return (f0[0], f0[1] - a / 2), z0, (f0[0], f0[1] + a / 2), z0
    return f0, z0, f0, z0


# A punch lands in about a third of a second -- a beat, not a move. Every other
# move runs the whole shot, eased at both ends like a dolly that starts and
# stops under control.
PUNCH_FRAMES = 10


def shot_props(seg, framing, info, region, start_s: float, end_s: float, fps: int,
               staged: Staged, warnings: list[str]) -> list[dict]:
    """The segment's shots as Remotion props, or [] for a single-shot segment.

    Frame boundaries come from cumulative output time, like the segments', so
    a shot cut lands on the same frame the caption word it was snapped to does.
    """
    if not framing.shots:
        return []
    seg_from = frames(start_s, fps)
    seg_len = max(1, frames(end_s, fps) - seg_from)
    out = []
    for i, shot in enumerate(framing.shots):
        a = frames(start_s + shot.at, fps) - seg_from
        nxt = framing.shots[i + 1].at if i + 1 < len(framing.shots) else None
        b = (frames(start_s + nxt, fps) - seg_from) if nxt is not None else seg_len
        a, b = max(0, min(a, seg_len - 1)), max(1, min(b, seg_len))
        if b <= a:
            continue
        f0, z0, f1, z1 = shot_states(shot)
        angle = staged.assets.get(shot.angle) if shot.angle else None
        out.append({
            "from": a,
            "duration": b - a,
            "size": shot.size,
            # Source frames skipped before this shot: the segment's own trim
            # plus however much of the segment has already played.
            "trimBefore": frames(seg.src_in, fps) + int(round(a * seg.speed)),
            "windowFrom": _window(info, region, f0, z0),
            "windowTo": _window(info, region, f1, z1),
            "moveFrames": min(PUNCH_FRAMES, b - a) if shot.move == "punch" else b - a,
            "ease": "outCubic" if shot.move == "punch" else "inOutCubic",
            "drift": round(shot.drift, 5),
            # crc32, not hash(): str hashes change per process, and a render
            # must be a pure function of its EDL.
            "seed": (zlib.crc32(seg.id.encode()) + i * 131) % 1000,
            "peek": shot.peek,
            "angle": angle,
            "angleTrimBefore": frames(shot.angle_in, fps),
            "angleRate": round(shot.angle_rate, 4),
        })
    return out


def build_props(edl: EDL, info: media.MediaInfo, staged: Staged) -> tuple[dict, list[str]]:
    """Resolve an EDL into the composition's props, all in frames.

    Returns ``(props, warnings)``. Pure apart from reading ``staged`` -- no
    files are touched here, which is what makes it testable exhaustively.
    """
    target = edl.target
    fps = target.fps
    width, height = target.width, target.height
    warnings: list[str] = list(staged.warnings)
    total = frames(edl.duration, fps)

    # --- segments ----------------------------------------------------------
    boundaries = _transition_boundaries(edl)
    split = edl.layout.kind == "split"
    top_h = _even_px(height * edl.layout.ratio) if split else 0
    # In a split layout the speaker is drawn into the lower region, so their
    # crop is computed for *that* region's shape -- framed for the space they
    # actually have rather than a 9:16 window squashed into it.
    region = replace(target, aspect=f"{width}:{height - top_h}") if split else target
    segments = []
    elapsed = 0.0
    for seg in edl.segments:
        start_s, end_s = elapsed, elapsed + seg.out_duration
        # Frame boundaries from cumulative time, never from summed per-segment
        # rounding -- otherwise a dozen cuts drift the edit a few frames out of
        # step with the captions placed in exact output time.
        start_f, end_f = frames(start_s, fps), frames(end_s, fps)
        framing = edl.framing_for(seg.id)
        animate = framing.mode == "punch" and abs(framing.zoom_to - framing.zoom_from) > 1e-3
        if animate:
            low = min(framing.zoom_from, framing.zoom_to)
            zoom_from, zoom_to = framing.zoom_from / low, framing.zoom_to / low
        else:
            low = framing.zoom_to
            zoom_from = zoom_to = 1.0
        window = filters.crop_window(info.width, info.height, region, framing.focus, low)
        full = filters.crop_window(info.width, info.height, target, framing.focus, low)
        segments.append({
            "id": seg.id,
            "from": start_f,
            "duration": max(1, end_f - start_f),
            "trimBefore": frames(seg.src_in, fps),
            "playbackRate": round(seg.speed, 4),
            "crop": {"x": window.x, "y": window.y, "w": window.w, "h": window.h},
            "cropFull": {"x": full.x, "y": full.y, "w": full.w, "h": full.h},
            "animate": animate,
            "zoomFrom": round(zoom_from, 5),
            "zoomTo": round(zoom_to, 5),
            "ease": framing.ease,
            "fadeIn": frames(boundaries.get(round(start_s, 2), 0.0), fps),
            "fadeOut": frames(boundaries.get(round(end_s, 2), 0.0), fps),
            # No fade here. Remotion applies volume once per video frame, so
            # any ramp it draws is a staircase -- and each stair is itself a
            # discontinuity that clicks. Splices are smoothed sample by sample
            # in the ffmpeg pass instead (see splice_filter).
            "audioFade": 0,
            "shots": shot_props(seg, framing, info, region, start_s, end_s, fps, staged, warnings),
        })
        elapsed = end_s

    # --- captions ----------------------------------------------------------
    style = ass.STYLES.get(edl.captions.style, ass.STYLES["karaoke-bold"])
    pages = []
    if edl.captions.enabled and edl.captions.words:
        for group in ass.group_words(edl.captions.words, style, target):
            first, last = group[0], group[-1]
            start_f = frames(first.start, fps)
            pages.append({
                "from": start_f,
                "duration": max(1, frames(last.end, fps) - start_f),
                "words": [{"text": w.text, "start": frames(w.start, fps),
                           "end": max(frames(w.start, fps) + 1, frames(w.end, fps))}
                          for w in group],
            })
    position = edl.captions.position if edl.captions.position is not None else style.position
    boxed = style.name == "seam"
    if boxed and split and edl.captions.position is None:
        # The seam caption lives on the line between panel and speaker.
        position = edl.layout.ratio
    captions = {
        "enabled": bool(edl.captions.enabled and pages),
        "pages": pages,
        "style": {
            "fontSize": int(round(height * style.size_ratio)),
            "color": ass_colour_to_css(style.primary),
            "highlight": ass_colour_to_css(style.highlight),
            "outline": ass_colour_to_css(style.outline),
            # ASS outlines grow outward; a CSS stroke straddles the edge and
            # paint-order puts half of it under the fill, so it is doubled.
            "outlineWidth": round(2 * style.outline_w * height / 1920, 2),
            "positionY": round(position, 4),
            "anchor": "center" if boxed else "bottom",
            "box": boxed,
            "marginX": int(round(width * style.margin_ratio)),
            "fontFamily": FONT_STACK,
        },
    }

    # --- layout ------------------------------------------------------------
    top = []
    for clip in edl.layout.top if split else []:
        src = staged.assets.get(clip.asset, "") if clip.asset else ""
        if clip.kind in ("image", "video") and not src:
            warnings.append(f"top-panel {clip.kind} at {clip.at}s has no usable asset, skipped")
            continue
        result = staged.assets.get(clip.result, "") if clip.result else ""
        dur_f = max(1, frames(clip.dur, fps))
        top.append({
            "kind": clip.kind,
            "from": frames(clip.at, fps),
            "duration": dur_f,
            "src": src,
            "panFrom": list(clip.pan_from),
            "panTo": list(clip.pan_to),
            "text": clip.text,
            "result": result,
            "resultIsVideo": Path(clip.result).suffix.lower() in VIDEO_EXTS if clip.result else False,
            "label": clip.label or ("WRITE THIS" if clip.kind == "prompt" else ""),
            "resultLabel": clip.result_label or ("TO GET THIS." if clip.kind == "prompt" else ""),
            "reveal": max(1, int(round(dur_f * min(max(clip.reveal, 0.1), 0.95)))),
        })
    layout = {"kind": "split" if split else "full", "topHeight": top_h,
              "background": edl.layout.background, "top": top}

    end_card = None
    if edl.end_card is not None:
        card = edl.end_card
        start_f = frames(card.at, fps)
        end_card = {"from": start_f, "duration": max(1, min(total, frames(card.at + card.dur, fps)) - start_f),
                    "keyword": card.keyword, "subtitle": card.subtitle, "handle": card.handle,
                    "outro": frames(card.outro, fps), "accent": card.accent}

    # --- overlays ----------------------------------------------------------
    overlays = []
    for ov in edl.overlays:
        start_f = frames(ov.at, fps)
        dur_f = max(1, frames(ov.dur, fps))
        if ov.type == "emoji":
            if not ov.glyph:
                warnings.append(f"emoji overlay at {ov.at}s has no glyph, skipped")
                continue
            overlays.append({"kind": "emoji", "from": start_f, "duration": dur_f,
                             "glyph": ov.glyph, "anchor": ov.anchor,
                             "size": int(round(height * EMOJI_SIZE)), "anim": ov.anim})
        elif ov.type in ("hyperframes", "remotion"):
            comp = GRAPHIC_ALIASES.get(ov.comp)
            if comp is None:
                warnings.append(
                    f"overlay composition {ov.comp!r} is not built in "
                    f"(have {sorted(set(GRAPHIC_ALIASES.values()))}), skipped")
                continue
            overlays.append({"kind": "graphic", "from": start_f, "duration": dur_f,
                             "comp": comp, "props": dict(ov.props)})
        else:
            warnings.append(f"overlay type {ov.type!r} not yet supported, skipped")

    # --- b-roll ------------------------------------------------------------
    broll = [{"from": frames(slot.start, fps), "duration": max(1, frames(slot.dur, fps)),
              "src": staged.broll[i]}
             for i, slot in enumerate(edl.broll) if i in staged.broll]

    # --- music -------------------------------------------------------------
    music = None
    if staged.music:
        base = db_to_linear(edl.audio.music_gain_db)
        windows = []
        if edl.audio.duck:
            windows = [[frames(a, fps), frames(b, fps)]
                       for a, b in speech_windows(edl.captions.words)]
            if not windows:
                warnings.append("music ducking asked for but there are no word "
                                "timings to duck under; bed plays at a flat level")
        music = {
            "src": staged.music,
            "volume": base,
            "duckVolume": db_to_linear(edl.audio.music_gain_db - DUCK_DB) if edl.audio.duck else base,
            "windows": windows,
            "attack": max(1, frames(edl.audio.duck_attack_ms / 1000, fps)),
            "release": max(1, frames(edl.audio.duck_release_ms / 1000, fps)),
        }

    # --- sound effects -----------------------------------------------------
    effects = []
    for cue in edl.sfx:
        name = staged.sfx.get(cue.name)
        if name is None:
            continue
        # `at` is where the effect lands; playback starts earlier by its lead.
        start_f = frames(cue.at + sfx.CATALOGUE[cue.name].lead, fps)
        effects.append({"src": name, "from": max(0, start_f),
                        "trimBefore": max(0, -start_f),
                        "volume": db_to_linear(cue.gain_db)})

    props = {
        "fps": fps,
        "width": width,
        "height": height,
        "durationInFrames": max(1, total),
        "source": {"src": staged.source, "width": info.width, "height": info.height},
        "segments": segments,
        "captions": captions,
        "overlays": overlays,
        "broll": broll,
        "music": music,
        "sfx": effects,
        "layout": layout,
        "endCard": end_card,
    }
    return props, warnings


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def render_cmd(project: Path, props: Path, public: Path, out: Path, *,
               concurrency: int, draft: bool, browser: Path | None,
               hardware: bool = False) -> list[str]:
    cmd = [
        "npx", "--no-install", "remotion", "render", "src/index.ts", "Edit", str(out),
        f"--props={props}",
        f"--public-dir={public}",
        f"--concurrency={max(1, concurrency)}",
        "--codec=h264",
        f"--crf={28 if draft else 18}",
        f"--x264-preset={'veryfast' if draft else 'medium'}",
        "--audio-codec=aac",
        "--overwrite",
        "--log=error",
    ]
    if browser is not None:
        cmd.append(f"--browser-executable={browser}")
    if hardware:
        # VideoToolbox on Apple Silicon. "if-possible" falls back to software
        # rather than failing a render on a machine without it.
        cmd.append("--hardware-acceleration=if-possible")
    return cmd


def cut_times(props: dict) -> list[float]:
    """Output seconds of every splice between two segments."""
    fps = props["fps"]
    return [round(seg["from"] / fps, 4) for seg in props["segments"][1:]]


def splice_filter(cuts: list[float], half: float) -> str:
    """A V-shaped volume dip, ``half`` seconds each side, centred on every splice.

    Two spans of speech joined at arbitrary sample values click; pulling the
    level to zero at the join and back over ~20 ms removes the step without an
    audible gap -- what the ffmpeg engine's afade pair does per segment. The
    terms are summed, not nested, so a vlog with hundreds of cuts does not
    build an expression ffmpeg cannot parse; ``asetnsamples`` makes the
    volume re-evaluate every 1 ms, so the ramp is smooth, not a staircase.
    """
    if not cuts or half <= 0:
        return ""
    terms = "+".join(f"max(0,1-abs(t-{c:.4f})/{half:.4f})" for c in cuts)
    return f"asetnsamples=n=48:p=0,volume='max(0,1-({terms}))':eval=frame,"


def loudness_cmd(src: Path, dst: Path, loudness: float, *,
                 cuts: list[float] | None = None, half: float = 0.02) -> list[str]:
    """Smooth the splices and normalise loudness, with the picture copied untouched."""
    return [
        "ffmpeg", "-hide_banner", "-nostdin", "-y", "-i", str(src),
        "-map", "0:v", "-map", "0:a?", "-c:v", "copy",
        "-af", f"{splice_filter(cuts or [], half)}loudnorm=I={loudness}:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst),
    ]


# --------------------------------------------------------------------------
# the entry point -- same signature as ffmpeg_renderer.render
# --------------------------------------------------------------------------

def render(edl: EDL, dst: Path, profile: Profile, *, draft: bool = False,
           workdir: Path | None = None, keep_intermediates: bool = False) -> RenderResult:
    if not edl.segments:
        raise RenderError("EDL has no segments")
    ok, why = available()
    if not ok:
        raise RemotionUnavailable(why)
    if not media.available():
        raise RenderError("ffmpeg/ffprobe not found -- run scripts/install.sh")

    src = Path(edl.source)
    if not src.exists():
        raise RenderError(f"source not found: {src}")
    info = media.probe(src)

    job = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="reelforge-rm-"))
    job.mkdir(parents=True, exist_ok=True)
    try:
        staged = stage(edl, job)
        props, warnings = build_props(edl, info, staged)
        props_path = job / "props.json"
        props_path.write_text(json.dumps(props), encoding="utf-8")

        raw = job / "remotion.mp4"
        cmd = render_cmd(
            project_dir(), props_path, staged.public, raw,
            concurrency=getattr(profile, "render_parallelism", 2),
            draft=draft, browser=find_browser(),
            hardware=getattr(profile, "encoder", "") == "h264_videotoolbox",
        )
        log.info("remotion: %d frames", props["durationInFrames"])
        proc = subprocess.run(cmd, cwd=project_dir(), capture_output=True, text=True)
        if proc.returncode != 0 or not raw.exists():
            detail = (proc.stderr or proc.stdout).strip()[-1500:]
            raise RenderError(f"remotion render failed:\n{detail}")

        dst.parent.mkdir(parents=True, exist_ok=True)
        half = max(0.01, edl.audio.fade_ms / 1000) if edl.audio.fade_ms > 0 else 0.0
        media.run(loudness_cmd(raw, dst, edl.target.loudness,
                               cuts=cut_times(props), half=half))
    finally:
        if not keep_intermediates and workdir is None:
            shutil.rmtree(job, ignore_errors=True)

    return RenderResult(output=dst, edl_path=None, duration=edl.duration,
                        segments=len(edl.segments), warnings=warnings)


# --------------------------------------------------------------------------
# preview in Remotion Studio
# --------------------------------------------------------------------------

def preview_cmd(project: Path, props: Path, public: Path, *, port: int = 3000,
                open_browser: bool = True) -> list[str]:
    """Remotion Studio on an edit: a browser player with a timeline.

    Every segment, caption card, graphic and sound effect shows up as its own
    named track, so the edit can be scrubbed, played, and inspected frame by
    frame before -- or instead of -- waiting for a full render.
    """
    cmd = ["npx", "--no-install", "remotion", "studio", "src/index.ts",
           f"--props={props}", f"--public-dir={public}", f"--port={port}"]
    if not open_browser:
        cmd.append("--no-open")
    return cmd


def prepare_preview(edl: EDL, workdir: Path) -> tuple[Path, Path, list[str]]:
    """Stage an edit for Studio exactly as a render would. Returns paths.

    Same staging and same props as :func:`render`, so what Studio shows is
    what a render will produce -- a preview built any other way would be a
    second renderer, and two renderers drift.
    """
    src = Path(edl.source)
    if not src.exists():
        raise RenderError(f"source not found: {src}")
    workdir.mkdir(parents=True, exist_ok=True)
    staged = stage(edl, workdir)
    props, warnings = build_props(edl, media.probe(src), staged)
    props_path = workdir / "props.json"
    props_path.write_text(json.dumps(props), encoding="utf-8")
    return props_path, staged.public, warnings
