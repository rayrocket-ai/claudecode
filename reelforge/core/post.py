"""Post formats: turn a finished edit into the layout it is published in.

Two formats studied from reference reels (docs/REFERENCE-FORMATS.md), plus
the plain one:

* **showcase** -- "write this -> get this". Split screen: a prompt types in a
  chat box on top, the result it produced springs in beside it, a pill on the
  seam says WRITE THIS then TO GET THIS. The speaker talks underneath.
* **explainer** -- split screen with one big diagram on top that the camera
  walks (pan and zoom) while the speaker explains it underneath.
* **full** -- the edit as cut, full frame.

Every format can end on a "Comment KEYWORD" card: the comment-to-DM lead
magnet both references close with.

A *post spec* is a small JSON document -- written by hand, by the
post-designer agent inside Claude Code, or by ``Brain.design_post`` -- and
:func:`apply` folds it into an EDL. Times in the spec are **output** seconds
(the edit's own clock, the same clock as its captions), because that is what
someone watching the edit points at: "show the diagram while she says
'pipeline'" is a time in the edit, not in the raw footage.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .brand import Brand
from .edl import EDL, EndCard, Layout, TopClip

FORMATS = ("showcase", "explainer", "full")

# Short-form platforms normalise to roughly -14 LUFS; both references were
# mastered at -13/-14. Mastering quieter just means the platform turns you up
# with its limiter instead of yours.
SOCIAL_LOUDNESS = -14.0

# An explainer still with no pan given drifts left to right and pushes in a
# little: enough motion to read as a camera, not enough to lose the reader.
DEFAULT_PAN = ((0.25, 0.5, 1.0), (0.75, 0.5, 1.12))

POST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["format", "why"],
    "properties": {
        "format": {"type": "string", "enum": list(FORMATS),
                   "description": "showcase: prompt -> result panels; explainer: a "
                                  "diagram walked by pan/zoom; full: no top panel"},
        "why": {"type": "string",
                "description": "One sentence: why this format fits what is said"},
        "ratio": {"type": "number", "minimum": 0.3, "maximum": 0.7,
                  "description": "Share of the height the top panel takes (default 0.5)"},
        "top": {
            "type": "array",
            "description": "Top-panel clips in output seconds, in order, not overlapping",
            "items": {
                "type": "object",
                "required": ["at", "dur", "kind"],
                "properties": {
                    "at": {"type": "number"},
                    "dur": {"type": "number"},
                    "kind": {"type": "string", "enum": ["image", "video", "prompt"]},
                    "asset": {"type": "string",
                              "description": "Path of an image/video from the asset list"},
                    "pan_from": {"type": "array", "items": {"type": "number"},
                                 "minItems": 3, "maxItems": 3,
                                 "description": "[x, y, zoom]: focus point 0-1 and scale"},
                    "pan_to": {"type": "array", "items": {"type": "number"},
                               "minItems": 3, "maxItems": 3},
                    "text": {"type": "string",
                             "description": "The prompt typed in the chat box (prompt clips)"},
                    "result": {"type": "string",
                               "description": "Asset shown as the prompt's result"},
                    "label": {"type": "string", "description": "Default WRITE THIS"},
                    "result_label": {"type": "string", "description": "Default TO GET THIS."},
                    "reveal": {"type": "number", "minimum": 0.2, "maximum": 0.9,
                               "description": "Fraction of the clip before the result appears"},
                },
            },
        },
        "end_card": {
            "type": "object",
            "required": ["keyword"],
            "properties": {
                "keyword": {"type": "string",
                            "description": "One word, uppercase, that viewers comment"},
                "subtitle": {"type": "string",
                             "description": "What they get, e.g. 'and I'll DM you the prompts'"},
                "dur": {"type": "number", "description": "Seconds at the end (default 3.5)"},
                "outro": {"type": "number", "description": "Final seconds of handle + logo (default 1)"},
            },
        },
        "caption_style": {"type": "string",
                          "description": "Override; split formats default to 'seam'"},
    },
}


class PostError(ValueError):
    """The spec cannot be applied. Says what is wrong."""


def _resolve(path: str, base: Path | None) -> str:
    if not path:
        return ""
    p = Path(path).expanduser()
    if not p.is_absolute() and base is not None:
        p = base / p
    return str(p.resolve())


def _triple(value, default) -> tuple[float, float, float]:
    if value is None:
        return default
    if len(value) != 3:
        raise PostError(f"a pan needs [x, y, zoom], got {value!r}")
    x, y, z = (float(v) for v in value)
    return (min(1.0, max(0.0, x)), min(1.0, max(0.0, y)), max(1.0, z))


def apply(edl: EDL, spec: dict, brand: Brand | None = None, *,
          base: Path | None = None) -> tuple[EDL, list[str]]:
    """Return a copy of ``edl`` laid out as ``spec`` says, plus notes on what was adjusted.

    Clips are clamped to the edit rather than rejected: a model that says a
    clip runs to 31s in a 30s edit meant "to the end", and refusing would
    turn a rounding error into a failed post.
    """
    brand = brand or Brand()
    fmt = spec.get("format", "full")
    if fmt not in FORMATS:
        raise PostError(f"unknown format {fmt!r}; use one of {', '.join(FORMATS)}")

    out = copy.deepcopy(edl)
    notes: list[str] = []
    total = out.duration
    if total <= 0:
        raise PostError("the edit has no duration; compose it before laying it out")

    if fmt == "full":
        out.layout = Layout()
    else:
        ratio = float(spec.get("ratio", 0.5))
        if not 0.3 <= ratio <= 0.7:
            notes.append(f"ratio {ratio} clamped to 0.3-0.7")
            ratio = min(0.7, max(0.3, ratio))
        top: list[TopClip] = []
        cursor = 0.0
        for i, raw in enumerate(sorted(spec.get("top") or [], key=lambda c: float(c["at"]))):
            kind = raw.get("kind", "image")
            at = max(float(raw["at"]), cursor)
            end = min(at + float(raw["dur"]), total)
            if end - at < 0.3:
                notes.append(f"top clip {i + 1} ({kind}) dropped: no room left in the edit")
                continue
            if at > float(raw["at"]) + 1e-6:
                notes.append(f"top clip {i + 1} moved to {at:.2f}s so clips do not overlap")
            clip = TopClip(at=round(at, 3), dur=round(end - at, 3), kind=kind,
                           asset=_resolve(raw.get("asset", ""), base),
                           text=str(raw.get("text", "")),
                           result=_resolve(raw.get("result", ""), base),
                           label=str(raw.get("label", "")),
                           result_label=str(raw.get("result_label", "")),
                           reveal=float(raw.get("reveal", 0.5)))
            pan_default = DEFAULT_PAN if fmt == "explainer" else ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0))
            clip.pan_from = _triple(raw.get("pan_from"), pan_default[0])
            clip.pan_to = _triple(raw.get("pan_to"), pan_default[1])
            if kind == "prompt" and not clip.text.strip():
                raise PostError(f"top clip {i + 1} is a prompt with no text to type")
            if kind in ("image", "video") and not clip.asset:
                raise PostError(f"top clip {i + 1} ({kind}) has no asset")
            top.append(clip)
            cursor = end
        if not top:
            notes.append("no top clips: the panel shows the background colour only")
        out.layout = Layout(kind="split", ratio=ratio, top=top)
        # Lower-thirds, kinetic text and emoji are placed in full-frame
        # coordinates; on a split they land across the seam or in the panel.
        # Neither reference uses them -- the seam captions and the panel do
        # that job -- so they go, and the note says so.
        if out.overlays:
            notes.append(f"{len(out.overlays)} overlay(s) removed: the split layout's panel "
                         "and seam captions replace them")
            out.overlays = []

    caption_style = spec.get("caption_style") or ("seam" if fmt != "full" else None)
    if caption_style:
        out.captions.style = caption_style
        out.captions.position = None     # the seam style places itself on the split line

    card = spec.get("end_card")
    if card:
        keyword = str(card.get("keyword", "")).strip().strip('"').upper()
        if not keyword:
            raise PostError("end_card needs a keyword")
        dur = min(float(card.get("dur", 3.5)), total * 0.4)
        out.end_card = EndCard(keyword=keyword, at=round(total - dur, 3), dur=round(dur, 3),
                               subtitle=str(card.get("subtitle", "")),
                               handle=brand.handle,
                               outro=min(float(card.get("outro", 1.0)), dur / 2),
                               accent=brand.accent)
        if dur < float(card.get("dur", 3.5)):
            notes.append(f"end card shortened to {dur:.1f}s so it does not swallow the edit")
    else:
        out.end_card = None

    if fmt != "full" or card:
        out.target.loudness = SOCIAL_LOUDNESS
    return out, notes


def edit_text(edl: EDL) -> str:
    """The edit's words on its own clock -- what a post designer reads."""
    lines: list[str] = []
    current: list[str] = []
    start = 0.0
    for word in edl.captions.words:
        if not current:
            start = word.start
        current.append(word.text.strip())
        if len(current) >= 10 or word.text.rstrip().endswith((".", "?", "!")):
            lines.append(f"[{start:5.1f}s] {' '.join(current)}")
            current = []
    if current:
        lines.append(f"[{start:5.1f}s] {' '.join(current)}")
    return "\n".join(lines)


def post_request(edl: EDL, assets: list[str], *, keyword: str | None = None,
                 offer: str | None = None) -> str:
    asset_lines = "\n".join(f"- {a}" for a in assets) or "- (none: use prompt clips or format full)"
    asks = []
    if keyword:
        asks.append(f"Use the end-card keyword {keyword.upper()}.")
    if offer:
        asks.append(f"Commenters get: {offer}")
    return (
        f"Lay out this {edl.duration:.1f}s edit as a post.\n\n"
        + (" ".join(asks) + "\n\n" if asks else "")
        + f"## Assets you may place\n\n{asset_lines}\n\n"
        "## What is said (output seconds)\n\n"
        f"{edit_text(edl) or '(no captions: lay it out from the asset list alone)'}\n"
    )
