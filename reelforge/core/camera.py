"""A virtual camera crew for footage shot from one angle.

One locked-off camera, edited as if three were rolling: the voice runs on
unbroken while the picture cuts between a wide, a medium, a close-up, an
extreme close-up and a detail of the hands, each shot carrying its own slow
move (push, pull, pan, a handheld sway, a soft foreground edge as if shot
past an object). This is how a single-camera talking head is cut to look
produced, and it is what the "shot from one angle" reference does with the
shots that the pixels already contain.

What pixels cannot contain -- a true side angle, a view from above, an orbit,
a different room -- needs a generative video model. :func:`export_requests`
and :func:`ingest_angles` are the bridge: they cut the exact spans to send to
such a tool, then lock what comes back onto the voice.

Editing grammar, enforced rather than hoped for:

* Picture cuts land on the start of a word, preferably after a pause or the
  end of a sentence -- a cut that lands mid-word reads as a glitch.
* Consecutive shots differ in size by at least 25% (the single-camera version
  of the 30-degree rule); anything less reads as a jump cut, not a new camera.
* No two consecutive shots share a move, and moves are slow -- a camera that
  is always pushing stops reading as a camera.
* Close-ups never magnify the source beyond ``max_upscale``: a 1080p source
  cannot make a sharp extreme close-up, and the planner says so instead of
  rendering mush.
"""

from __future__ import annotations

import copy
import json
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import media
from .analyze import Signals
from .edl import EDL, Shot
from .render import filters

# zoom over the base crop (the largest window of the target aspect the source holds)
SIZES: dict[str, float] = {"wide": 1.0, "medium": 1.3, "close": 1.75, "extreme": 2.4, "detail": 2.0}
MIN_SIZE_RATIO = 1.25


@dataclass
class Style:
    name: str
    shot_len: tuple[float, float]          # seconds, min and max between picture cuts
    order: tuple[str, ...]                 # size rotation when nothing else decides
    drift: dict[str, float]                # handheld sway by size
    moves: dict[str, tuple[str, ...]]      # allowed moves by size, tried in order
    peek_every: float = 0.0                # seconds between foreground-edge shots; 0 = never
    detail_every: int = 3                  # at most one detail shot per this many shots


STYLES: dict[str, Style] = {
    # Fast, social: a new camera every 2-3.5 s, punchy sizes, light sway.
    "multicam": Style(
        name="multicam", shot_len=(1.8, 3.4),
        order=("wide", "close", "medium", "extreme", "medium", "close"),
        drift={"wide": 0.004, "medium": 0.003, "close": 0.0, "extreme": 0.0, "detail": 0.004},
        moves={"wide": ("push", "static"), "medium": ("pan", "static", "push"),
               "close": ("static", "push"), "extreme": ("static", "pull"),
               "detail": ("pan", "tilt")},
        peek_every=9.0,
    ),
    # Handheld documentary: longer takes, constant gentle sway, few moves.
    "documentary": Style(
        name="documentary", shot_len=(3.0, 5.5),
        order=("medium", "close", "wide", "close"),
        drift={"wide": 0.008, "medium": 0.008, "close": 0.006, "extreme": 0.005, "detail": 0.009},
        moves={"wide": ("static", "push"), "medium": ("static", "pan"),
               "close": ("static", "push"), "extreme": ("static",), "detail": ("pan", "static")},
        peek_every=0.0, detail_every=4,
    ),
    # Cinematic: locked-off frames that glide -- dolly pushes, slow pans, depth.
    "cinematic": Style(
        name="cinematic", shot_len=(2.6, 4.6),
        order=("wide", "close", "medium", "extreme"),
        drift={k: 0.0 for k in SIZES},
        moves={"wide": ("push", "pan"), "medium": ("pan", "pull"), "close": ("push", "static"),
               "extreme": ("pull", "static"), "detail": ("pan", "tilt")},
        peek_every=7.0,
    ),
}

AMOUNTS = {"push": 0.07, "pull": 0.07, "pan": 0.07, "tilt": 0.05, "punch": 0.12, "static": 0.0}


@dataclass
class Plan:
    edl: EDL
    notes: list[str] = field(default_factory=list)
    shots: int = 0
    max_zoom: float = 0.0


# --------------------------------------------------------------------------
# resolution
# --------------------------------------------------------------------------

def max_zoom(info: media.MediaInfo, edl: EDL, max_upscale: float) -> float:
    """The tightest magnification the source can take before it goes soft."""
    base_w, _ = filters.base_crop(info.width, info.height, edl.target)
    return max(1.0, max_upscale * base_w / max(1, edl.target.width))


def sizes_for(limit: float) -> dict[str, float]:
    """Shot sizes that fit under ``limit``, squeezed but still distinct.

    When the source is too small for the full ladder, the ladder is compressed
    into what is available rather than clipped -- clipping would collapse
    close and extreme into the same frame and every cut between them would be
    a jump cut.
    """
    top = max(SIZES.values())
    if limit >= top:
        return dict(SIZES)
    out = {}
    for name, z in SIZES.items():
        out[name] = round(1.0 + (z - 1.0) * (limit - 1.0) / (top - 1.0), 3)
    return out


# --------------------------------------------------------------------------
# where to cut
# --------------------------------------------------------------------------

def cut_candidates(words, seg_start: float, seg_end: float) -> list[tuple[float, float]]:
    """(time from segment start, quality) for every word start inside the segment.

    Quality favours the start of a sentence, then a word after a pause.
    """
    out = []
    prev_end = None
    prev_text = ""
    for w in words:
        if w.start <= seg_start + 0.05 or w.start >= seg_end - 0.05:
            prev_end, prev_text = w.end, w.text
            continue
        gap = w.start - prev_end if prev_end is not None else 0.0
        q = 1.0
        if prev_text.rstrip().endswith((".", "?", "!", ",", ":", ";")):
            q += 2.0
        q += min(2.0, gap / 0.15)
        out.append((round(w.start - seg_start, 3), q))
        prev_end, prev_text = w.end, w.text
    return out


def choose_cuts(candidates, length: float, lo: float, hi: float, seed: int) -> list[float]:
    """Picture-cut times inside one segment, every ``lo``-``hi`` seconds, on words."""
    cuts: list[float] = []
    last = 0.0
    k = seed
    while True:
        k += 1
        target = lo + (hi - lo) * ((math.sin(k * 12.9898) * 43758.5453) % 1.0)
        window = [(t, q) for t, q in candidates if last + lo * 0.8 <= t <= last + hi * 1.15
                  and t <= length - 0.7]
        if window:
            # Best word near the target length; quality breaks near-ties.
            t, _ = max(window, key=lambda c: c[1] - abs(c[0] - (last + target)) * 1.5)
        elif not candidates and last + target <= length - 0.7:
            t = round(last + target, 3)      # no words (music, b-roll): cut on time
        else:
            break
        cuts.append(t)
        last = t
    return cuts


# --------------------------------------------------------------------------
# where the hands are
# --------------------------------------------------------------------------

def motion_focus(src: Path, t: float, face: tuple[float, float]) -> tuple[float, float, float] | None:
    """Centre and strength of movement away from the face around ``t``.

    Two small greyscale frames a quarter-second apart, differenced; the face's
    neighbourhood is blanked so talking does not count as action. A strong
    result means hands, tools or objects are moving -- a detail shot of them
    is the "insert" a second camera would have caught.
    """
    try:
        import numpy as np
    except ImportError:
        return None
    w, h = 96, 96
    grabs = []
    for at in (t, t + 0.25):
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-ss", f"{max(0.0, at):.3f}",
             "-i", str(src), "-frames:v", "1", "-vf", f"scale={w}:{h},format=gray",
             "-f", "rawvideo", "-"], capture_output=True, check=False)
        if proc.returncode != 0 or len(proc.stdout) < w * h:
            return None
        grabs.append(np.frombuffer(proc.stdout[: w * h], dtype=np.uint8).astype("float32").reshape(h, w))
    diff = np.abs(grabs[1] - grabs[0])
    fx, fy = int(face[0] * w), int(face[1] * h)
    diff[max(0, fy - int(0.22 * h)):fy + int(0.2 * h), max(0, fx - int(0.16 * w)):fx + int(0.16 * w)] = 0
    cutoff = np.percentile(diff, 98)
    if cutoff < 12:                       # nothing moving beyond sensor noise
        return None
    ys, xs = np.nonzero(diff >= cutoff)
    weights = diff[ys, xs]
    cx = float((xs * weights).sum() / weights.sum()) / w
    cy = float((ys * weights).sum() / weights.sum()) / h
    return round(cx, 3), round(cy, 3), round(float(cutoff) / 255, 3)


# --------------------------------------------------------------------------
# the plan
# --------------------------------------------------------------------------

def _framing_focus(size: str, face: tuple[float, float]) -> tuple[float, float]:
    x, y = face
    if size == "wide":
        return (0.5 + (x - 0.5) * 0.5, 0.5)
    if size == "medium":
        return (x, min(1.0, y + 0.1))     # headroom: eyes on the upper third
    if size == "close":
        return (x, min(1.0, y + 0.05))
    return (x, y)


def plan(edl: EDL, info: media.MediaInfo, signals: Signals | None, *, style: str = "multicam",
         max_upscale: float = 2.6, src: Path | None = None) -> Plan:
    """Return a copy of ``edl`` with a shot list on every segment.

    ``src`` enables detail shots (it is read to find moving hands); without
    it the plan uses face framing only.
    """
    if style not in STYLES:
        raise ValueError(f"unknown camera style {style!r}; use one of {', '.join(STYLES)}")
    st = STYLES[style]
    out = copy.deepcopy(edl)
    notes: list[str] = []
    limit = max_zoom(info, out, max_upscale)
    sizes = sizes_for(limit)
    if limit < SIZES["extreme"]:
        notes.append(f"source is {info.width}x{info.height}: close-ups capped at {limit:.2f}x to stay "
                     f"sharp (sizes squeezed to fit). Film in 4K for real close-ups.")
    if sizes["medium"] / sizes["wide"] < 1.12:
        notes.append("the source has almost no room to reframe at this output size; "
                     "shots will mostly differ by their moves")

    words = out.captions.words
    elapsed = 0.0
    last_size = ""
    last_move = ""
    since_peek = 1e9
    since_detail = 99
    rot = 0
    count = 0
    for si, seg in enumerate(out.segments):
        framing = out.framing_for(seg.id)
        if framing not in out.framing:
            out.framing.append(framing)
        length = seg.out_duration
        cands = cut_candidates(words, elapsed, elapsed + length)
        cuts = choose_cuts(cands, length, *st.shot_len, seed=si * 7 + len(seg.id))
        starts = [0.0] + cuts
        shots: list[Shot] = []
        for k, at in enumerate(starts):
            end = starts[k + 1] if k + 1 < len(starts) else length
            src_t = seg.src_in + (at + (end - at) / 2) * seg.speed
            face = signals.focus_at(src_t) if signals else framing.focus
            emphasis = framing.mode == "punch" and k == 0
            size = None

            if count == 0:
                size = "close"                 # the hook: start on the face
            elif emphasis:
                size = "extreme" if last_size != "extreme" else "close"
            elif src is not None and since_detail >= st.detail_every and end - at >= 1.2:
                hit = motion_focus(src, src_t, face)
                if hit and hit[2] >= 0.12:
                    size = "detail"
                    face = (hit[0], hit[1])
            if size is None:
                for _ in range(len(st.order)):
                    cand = st.order[rot % len(st.order)]
                    rot += 1
                    if cand != last_size and _distinct(sizes, cand, last_size):
                        size = cand
                        break
                size = size or ("wide" if last_size != "wide" else "close")

            move = "punch" if emphasis else next(
                (m for m in st.moves[size] if m != last_move), st.moves[size][0])
            peek = ""
            if st.peek_every and since_peek >= st.peek_every and size in ("wide", "medium", "detail") \
                    and end - at >= 1.5:
                peek = "right" if face[0] < 0.5 else "left"   # the edge away from the subject
                since_peek = 0.0
            focus = face if size == "detail" else _framing_focus(size, face)
            shots.append(Shot(at=round(at, 3), size=size, focus=(round(focus[0], 4), round(focus[1], 4)),
                              zoom=sizes[size], move=move, amount=AMOUNTS[move],
                              drift=st.drift.get(size, 0.0), peek=peek))
            since_peek += end - at
            since_detail = 0 if size == "detail" else since_detail + 1
            last_size, last_move = size, move
            count += 1
        framing.shots = shots
        elapsed += length
    return Plan(edl=out, notes=notes, shots=count, max_zoom=round(limit, 3))


def _distinct(sizes: dict[str, float], a: str, b: str) -> bool:
    if not b:
        return True
    za, zb = sizes[a], sizes[b]
    return max(za, zb) / min(za, zb) >= MIN_SIZE_RATIO or {a, b} == {"detail", "wide"}


# --------------------------------------------------------------------------
# generated angles: the shots pixels cannot contain
# --------------------------------------------------------------------------

ANGLE_PROMPTS = (
    "Same person, same words and movements. Camera moved to the left side, 45 degrees, eye level.",
    "Same person, same words and movements. High angle, camera looking down from above.",
    "Same person, same words and movements. Slow orbit around the subject.",
    "Same person, same words and movements. Shot from behind a foreground object, shallow depth of field.",
    "Same person, same words and movements. Low angle, camera slightly below eye level.",
)
MANIFEST = "angles.json"


def shot_spans(edl: EDL) -> list[dict]:
    """Every shot with its source span: what a generated angle must cover."""
    rows = []
    for seg in edl.segments:
        framing = edl.framing_for(seg.id)
        for i, shot in enumerate(framing.shots):
            end = framing.shots[i + 1].at if i + 1 < len(framing.shots) else seg.out_duration
            rows.append({"seg": seg.id, "shot": i, "size": shot.size,
                         "src_in": round(seg.src_in + shot.at * seg.speed, 3),
                         "src_out": round(seg.src_in + end * seg.speed, 3),
                         "dur": round(end - shot.at, 3)})
    return rows


def pick_for_angles(edl: EDL, count: int) -> list[dict]:
    """The shots most worth regenerating: long enough to show off, spread out."""
    spans = [r for r in shot_spans(edl) if r["dur"] >= 1.5 and not (r["seg"] == edl.segments[0].id
                                                                     and r["shot"] == 0)]
    if not spans:
        return []
    spans.sort(key=lambda r: r["src_in"])
    if len(spans) <= count:
        return spans
    step = len(spans) / count
    return [max(spans[int(i * step):int((i + 1) * step)], key=lambda r: r["dur"]) for i in range(count)]


def export_requests(edl: EDL, outdir: Path, *, count: int = 3, location: str = "") -> list[dict]:
    """Cut the spans to send to a generative video tool, with a prompt for each."""
    outdir.mkdir(parents=True, exist_ok=True)
    picks = pick_for_angles(edl, count)
    rows = []
    for n, r in enumerate(picks):
        name = f"angle-{n + 1:02d}"
        prompt = ANGLE_PROMPTS[n % len(ANGLE_PROMPTS)]
        if location:
            prompt += f" Set the scene in {location}; keep the face, expression and lip movement identical."
        clip = outdir / f"{name}.mp4"
        media.run(["ffmpeg", "-hide_banner", "-nostdin", "-y", "-ss", f"{r['src_in']:.3f}",
                   "-to", f"{r['src_out']:.3f}", "-i", edl.source,
                   "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac",
                   "-movflags", "+faststart", str(clip)])
        # The clip's real length, not the span's: an encoder pads a few frames,
        # and the generated clip's time scale must be measured against what
        # was actually sent, or lip-sync drifts by exactly that padding.
        rows.append({**r, "name": name, "request": str(clip), "prompt": prompt,
                     "request_dur": round(media.probe(clip).duration, 3)})
    (outdir / MANIFEST).write_text(json.dumps({"source": edl.source, "angles": rows}, indent=2) + "\n",
                                   encoding="utf-8")
    return rows


VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".webm")


def find_result(name: str, dirs: list[Path]) -> Path | None:
    for d in dirs:
        for ext in VIDEO_EXTS:
            for cand in (d / f"{name}{ext}", d / f"{name}-result{ext}"):
                if cand.exists():
                    return cand
    return None


def ingest_angles(edl: EDL, manifest_path: Path, results: Path, *,
                  probe=media.probe) -> tuple[EDL, list[str]]:
    """Lock generated clips onto the shots they were made from.

    Matched by source time, not by shot index, so the shot list can be
    re-planned after export without sending the wrong clip to the wrong shot.
    The clip is time-stretched to the shot's exact length, which is what
    keeps generated lip movement on the original voice; a clip that would
    need more than 20% stretch is refused, because by then it is out of sync.
    """
    out = copy.deepcopy(edl)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    notes: list[str] = []
    spans = shot_spans(out)
    for row in manifest.get("angles", []):
        result = find_result(row["name"], [results])
        if result is None:
            notes.append(f"{row['name']}: no generated clip yet in {results}")
            continue
        match = next((s for s in spans if abs(s["src_in"] - row["src_in"]) < 0.06
                      and abs(s["src_out"] - row["src_out"]) < 0.06), None)
        if match is None:
            notes.append(f"{row['name']}: no shot covers {row['src_in']}-{row['src_out']}s any more "
                         "(the plan changed since export); re-export or re-plan")
            continue
        clip_dur = probe(result).duration
        sent = float(row.get("request_dur") or match["dur"])
        # Tools return clips a little longer or shorter than what they were
        # given. Playing at generated/sent keeps every frame where the voice
        # expects it; the shot then uses the first ``dur`` seconds of that.
        rate = clip_dur / max(0.01, sent)
        if not 0.8 <= rate <= 1.2:
            notes.append(f"{row['name']}: generated clip is {clip_dur:.2f}s for a {sent:.2f}s "
                         "request -- too far off to stay in sync; regenerate at the request's length")
            continue
        shot = out.framing_for(match["seg"]).shots[match["shot"]]
        shot.angle, shot.angle_in, shot.angle_rate = str(result.resolve()), 0.0, round(rate, 4)
        shot.size, shot.move, shot.amount, shot.peek = "angle", "static", 0.0, ""
        notes.append(f"{row['name']}: placed at {match['seg']} shot {match['shot'] + 1}"
                     + (f", stretched {rate:.3f}x" if abs(rate - 1) > 0.005 else ""))
    return out, notes
