"""FFmpeg filter graph construction.

Pure string building, no execution -- so the graphs are unit-tested on a machine
with no ffmpeg. This is deliberate: a wrong filter graph is the most common and
most expensive bug in a video pipeline, and it is invisible until you watch the
output.

Two things here are worth knowing before editing:

**Sizes are computed in Python, not in ffmpeg expressions.** We probe the source
anyway, so emitting `crop=1080:1920:420:0` instead of a tower of `iw`/`ih`
arithmetic makes the graphs readable and the tests meaningful.

**A static zoom is just a tighter crop.** Only a genuinely animated move takes
the more expensive path below, and that path deliberately avoids `zoompan` --
see the measurements at the top of the module body.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..edl import Audio, Framing, Segment, Target

# Animated zoom deliberately does NOT use ffmpeg's `zoompan`.
#
# zoompan is the obvious tool and it is a trap. Measured on a 4-core box,
# rendering one 5-second 1080x1920 push-in:
#
#     crop + scale, no zoom            6.2 s
#     ... with zoompan               167 s+  (killed before finishing)
#     ... with scale(eval=frame)       5.2 s
#
# More than 27x slower, and because segments render in parallel the slowest one
# gates the entire job -- a single punch-in would cost more than the rest of the
# reel combined.
#
# The replacement is a time-varying `scale` followed by a fixed-size centre
# `crop`. It is faster than not zooming at all (a zoomed frame carries less
# detail, so x264 has less to encode) and it is also *smoother*: zoompan snaps
# its pan to whole pixels, whereas scaling is continuous, so the stepping
# zoompan is known for simply does not arise.


@dataclass(frozen=True)
class CropWindow:
    w: int
    h: int
    x: int
    y: int

    def as_filter(self) -> str:
        return f"crop={self.w}:{self.h}:{self.x}:{self.y}"


def _even(n: float) -> int:
    """Round a *dimension* down to an even integer, never below 2.

    h264 chroma subsampling rejects odd dimensions, and the error ffmpeg emits
    for it names neither the filter nor the dimension.
    """
    return max(2, int(n) // 2 * 2)


def _even_offset(n: float) -> int:
    """Round an *offset* down to an even integer, allowing zero.

    Separate from :func:`_even` on purpose: a dimension of 0 is invalid, but an
    offset of 0 is exactly what a crop flush against the frame edge needs. Using
    the dimension rule here nudges edge crops 2px inward, which is invisible in
    a single frame and shows up as a drift when the subject is at the border.
    """
    return max(0, int(n) // 2 * 2)


def base_crop(src_w: int, src_h: int, target: Target) -> tuple[int, int]:
    """Largest window of the target aspect that fits inside the source."""
    if src_w <= 0 or src_h <= 0:
        raise ValueError("source dimensions must be positive")
    aw, ah = (int(n) for n in target.aspect.split(":"))
    want = aw / ah
    if src_w / src_h > want:
        return _even(src_h * want), _even(src_h)      # source is wider: pillar
    return _even(src_w), _even(src_w / want)          # source is taller: letter


def crop_window(src_w: int, src_h: int, target: Target, focus: tuple[float, float],
                zoom: float = 1.0) -> CropWindow:
    """Crop window of the target aspect, centred on ``focus``, at ``zoom``.

    Clamped to stay inside the frame. Clamping rather than letting the window
    run off the edge is what stops a subject near the frame border producing
    black bars down one side.
    """
    bw, bh = base_crop(src_w, src_h, target)
    w, h = _even(bw / max(0.01, zoom)), _even(bh / max(0.01, zoom))
    x = _even_offset(min(max(focus[0] * src_w - w / 2, 0), max(0, src_w - w)))
    y = _even_offset(min(max(focus[1] * src_h - h / 2, 0), max(0, src_h - h)))
    return CropWindow(w, h, x, y)


def ease_expr(kind: str, progress: str) -> str:
    """An ffmpeg expression easing ``progress`` (0..1) into 0..1."""
    p = f"clip({progress},0,1)"
    if kind == "linear":
        return p
    if kind == "inOutCubic":
        return f"if(lt({p},0.5),4*pow({p},3),1-pow(-2*{p}+2,3)/2)"
    return f"(1-pow(1-{p},3))"       # outCubic: fast start, gentle settle


def zoom_expr(framing: Framing, out_duration: float) -> str:
    """Scale factor over time, normalised so it never drops below 1.

    The widest point of the move is baked into the base crop, so what remains
    is always a magnification of at least 1x. That normalisation is what lets a
    pull-out (zoom_to < zoom_from) use exactly the same code path as a push-in:
    without it, a factor below 1 would ask `crop` for a region larger than its
    input and fail.
    """
    z_min = min(framing.zoom_from, framing.zoom_to)
    start = framing.zoom_from / z_min
    end = framing.zoom_to / z_min
    eased = ease_expr(framing.ease, f"t/{max(0.001, out_duration):.4f}")
    return f"({start:.5f}+({end:.5f}-{start:.5f})*{eased})"


def video_chain(src_w: int, src_h: int, target: Target, framing: Framing,
                out_duration: float, *, speed: float = 1.0) -> str:
    """The per-segment video filter chain."""
    parts: list[str] = []

    animating = abs(framing.zoom_to - framing.zoom_from) > 1e-3 and framing.mode == "punch"

    if not animating:
        # Static path: a tighter crop *is* the zoom. Nothing to animate.
        window = crop_window(src_w, src_h, target, framing.focus, framing.zoom_to)
        parts.append(window.as_filter())
        parts.append(f"scale={target.width}:{target.height}:flags=bicubic")
    else:
        # Animated path. Crop at the widest point of the move -- centred on the
        # subject -- then magnify over time and take a fixed centre window. The
        # output size stays constant, which is what the encoder requires, while
        # the sampled region shrinks, which is what the eye reads as a push-in.
        window = crop_window(src_w, src_h, target, framing.focus,
                             min(framing.zoom_from, framing.zoom_to))
        parts.append(window.as_filter())
        z = zoom_expr(framing, out_duration)
        parts.append(
            f"scale=w='{target.width}*{z}':h='{target.height}*{z}'"
            f":eval=frame:flags=bicubic"
        )
        parts.append(f"crop={target.width}:{target.height}")

    if abs(speed - 1.0) > 1e-3:
        parts.append(f"setpts={1 / speed:.6f}*PTS")
    # setsar is not cosmetic: concat refuses to join streams whose sample aspect
    # ratios differ, and sources with non-square pixels will otherwise poison a
    # single segment and fail the whole join.
    parts.append("setsar=1")
    parts.append(f"fps={target.fps}")
    return ",".join(parts)


def audio_chain(out_duration: float, audio: Audio, *, speed: float = 1.0) -> str:
    """The per-segment audio filter chain.

    The fades are the entire reason cuts do not click. Splicing two segments at
    arbitrary sample values leaves a step discontinuity, which reproduces as a
    pop; a 20 ms ramp at each boundary is inaudible as a fade and completely
    removes it.
    """
    parts: list[str] = []
    if abs(speed - 1.0) > 1e-3:
        # atempo is only stable within 0.5-2.0, so larger changes are chained.
        remaining, factors = speed, []
        while remaining > 2.0:
            factors.append(2.0)
            remaining /= 2.0
        while remaining < 0.5:
            factors.append(0.5)
            remaining /= 0.5
        factors.append(remaining)
        parts += [f"atempo={f:.6f}" for f in factors]

    fade = max(0.0, audio.fade_ms / 1000)
    if fade > 0 and out_duration > fade * 2:
        parts.append(f"afade=t=in:st=0:d={fade:.3f}")
        parts.append(f"afade=t=out:st={out_duration - fade:.3f}:d={fade:.3f}")

    # Normalise layout and rate so concat never sees mismatched streams.
    parts.append("aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo")
    return ",".join(parts)


def dip_filters(fade_in: float, fade_out: float, out_duration: float) -> list[str]:
    """Fade filters implementing a transition as a dip at a segment boundary.

    Deliberately *not* `xfade`. A crossfade overlaps its two inputs, which
    shortens the result by the transition duration -- and every caption,
    overlay and chapter after that point is timed in output seconds and would
    silently drift by exactly that much. One transition would desynchronise the
    rest of the video.

    Fading the tail of one segment and the head of the next preserves duration
    exactly, keeps the timing contract intact, and for the case that actually
    matters -- softening a jump cut in a locked-off shot -- a brief dip reads
    better than a cross-dissolve anyway.
    """
    parts = []
    if fade_in > 0:
        parts.append(f"fade=t=in:st=0:d={fade_in:.3f}")
    if fade_out > 0 and out_duration > fade_out:
        parts.append(f"fade=t=out:st={out_duration - fade_out:.3f}:d={fade_out:.3f}")
    return parts


def segment_cmd(src: str, seg: Segment, framing: Framing, target: Target,
                audio: Audio, dst: str, *, src_w: int, src_h: int,
                has_audio: bool, encode_args: list[str],
                fade_in: float = 0.0, fade_out: float = 0.0) -> list[str]:
    """Render one segment to an intermediate file.

    Segments are rendered independently so they can run in parallel across
    cores -- on a CPU-only box that is a far bigger win than any encoder tuning
    -- and then joined without re-encoding.
    """
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        # -ss before -i seeks by keyframe index rather than decoding from zero,
        # and stays frame-accurate because we re-encode. On an hour-long source
        # this is the difference between seconds and minutes per segment.
        "-ss", f"{seg.src_in:.3f}",
        "-t", f"{seg.src_duration:.3f}",
        "-i", src,
    ]
    chain = video_chain(src_w, src_h, target, framing, seg.out_duration,
                        speed=seg.speed)
    dips = dip_filters(fade_in, fade_out, seg.out_duration)
    if dips:
        chain = ",".join([chain, *dips])
    cmd += ["-filter:v", chain]
    if has_audio:
        cmd += ["-filter:a", audio_chain(seg.out_duration, audio, speed=seg.speed)]
    else:
        # Silent segments still need a track, or concat produces a file whose
        # audio stops partway through.
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                "-shortest", "-map", "0:v", "-map", "1:a"]

    cmd += encode_args
    cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    cmd += ["-video_track_timescale", "90000", dst]
    return cmd


def concat_cmd(list_file: str, dst: str) -> list[str]:
    """Join rendered segments without re-encoding."""
    return [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy",
        # Segment boundaries leave gaps in the timestamp sequence that some
        # players read as stalls; this rewrites them into a continuous run.
        "-fflags", "+genpts",
        dst,
    ]


def finish_cmd(src: str, dst: str, target: Target, *, subtitles: str | None,
               overlays: list[tuple[str, float, float, str, str]],
               encode_args: list[str]) -> list[str]:
    """Burn captions and overlays, normalise loudness, and encode the final.

    Done in one pass over the joined video rather than per segment, because
    caption and overlay times are in *output* space -- applying them per segment
    would mean re-deriving every timestamp against a moving origin.
    """
    inputs = ["-i", src]
    for path, *_ in overlays:
        inputs += ["-i", path]

    steps: list[str] = []
    label = "0:v"
    for index, (_path, at, dur, x, y) in enumerate(overlays, start=1):
        nxt = f"v{index}"
        # x and y must be quoted: an animated position contains commas (from
        # `clip(v,0,1)`), and ffmpeg reads an unquoted comma as the end of the
        # filter -- producing a parse error that points at the *next* filter and
        # never mentions the expression that actually caused it.
        steps.append(
            f"[{label}][{index}:v]overlay=x='{x}':y='{y}'"
            f":enable='between(t,{at:.3f},{at + dur:.3f})'[{nxt}]"
        )
        label = nxt

    if subtitles:
        nxt = "vsub"
        # force_style is intentionally absent: styling lives in the ASS file so
        # a caption look can be reviewed and diffed rather than buried in a
        # command line.
        steps.append(f"[{label}]subtitles='{subtitles}'[{nxt}]")
        label = nxt

    filter_complex = ";".join(steps) if steps else ""

    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y", *inputs]
    if filter_complex:
        cmd += ["-filter_complex", filter_complex, "-map", f"[{label}]"]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", "0:a?"]
    # Single-pass loudnorm drifts slightly versus a measured two-pass run, but
    # it is well inside what platforms re-normalise anyway, and it halves the
    # render time of the one stage that cannot be parallelised.
    cmd += ["-filter:a", f"loudnorm=I={target.loudness}:TP=-1.5:LRA=11"]
    cmd += encode_args
    cmd += ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst]
    return cmd


def anchor_position(anchor: str, target: Target, size: int, margin: int = 48) -> tuple[str, str]:
    """Overlay x/y expressions for a named corner, respecting margins."""
    right = target.width - size - margin
    bottom = target.height - size - margin
    return {
        "tl": (str(margin), str(margin)),
        "tr": (str(right), str(margin)),
        "bl": (str(margin), str(bottom)),
        "br": (str(right), str(bottom)),
        "c": (str((target.width - size) // 2), str((target.height - size) // 2)),
    }[anchor]
