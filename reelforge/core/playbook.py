"""Craft rules -- the part of the system that learns.

Everything here is a number that could reasonably be argued about: how long a
shot must be, how much breath to leave at a cut, how often a punch-in is too
often. Defaults are a starting position, not a house style.

The rules live in ``memory/playbook.md`` as human-readable lines with their
provenance attached, and :func:`load` reads them back. That file is the seam
where `/reel-feedback` writes what it has learned, which is what makes the
system improve rather than merely repeat.

Format is deliberately plain -- ``key: value`` with a trailing ``#`` comment --
so you can open it, disagree with a rule, and delete it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from pathlib import Path


@dataclass
class Playbook:
    # --- cutting ----------------------------------------------------------
    min_shot: float = 0.7
    """Shortest span that reads as a deliberate shot rather than a glitch."""

    lead_in: float = 0.12
    """Silence kept before the first word. Cutting flush to the syllable
    clips the attack of the consonant and sounds like a mistake."""

    lead_out: float = 0.25
    """Silence kept after the last word. A clip that ends the instant speech
    does feels truncated; a beat of air reads as an ending."""

    keep_pause: float = 0.22
    """What survives of a removed pause. Cutting a gap to zero machine-guns
    the delivery -- this is the difference between tight and exhausting."""

    min_gap_to_cut: float = 0.55
    """Below this, a pause is speech rhythm and removing it is audible."""

    # --- framing ----------------------------------------------------------
    punch_zoom: float = 1.14
    """How far a punch-in travels. Past about 1.25 on a 1080p source the
    softness becomes visible."""

    punch_duration: float = 1.6
    min_punch_gap: float = 3.0
    """Two push-ins close together read as a nervous camera operator."""

    hook_punch: bool = True
    """Open on a slow push. It gives the first second motion, which is what
    stops a thumb."""

    # --- captions ---------------------------------------------------------
    caption_style: str = "karaoke-bold"
    caption_position: float = 0.72
    captions_enabled: bool = True

    # --- overlays ---------------------------------------------------------
    emoji_per_minute: float = 6.0
    """Ceiling, not a target. Emoji punctuate; past this they are wallpaper."""

    emoji_min_gap: float = 2.5

    # --- audio ------------------------------------------------------------
    fade_ms: int = 20
    loudness: float = -16.0

    # --- length -----------------------------------------------------------
    min_seconds: float = 15.0
    max_seconds: float = 59.0

    @property
    def target_seconds(self) -> tuple[float, float]:
        return (self.min_seconds, self.max_seconds)


_LINE = re.compile(r"^\s*([a-z_]+)\s*:\s*([^#]+?)\s*(?:#.*)?$")


def load(path: Path | None) -> Playbook:
    """Read a playbook, falling back to defaults for anything absent.

    Unknown keys are ignored rather than rejected. The file is edited by hand
    and by an agent that is learning, and refusing to load a whole playbook
    because one line has a typo would mean losing every rule learned so far.
    """
    book = Playbook()
    if path is None or not Path(path).exists():
        return book

    known = {f.name: f.type for f in fields(Playbook)}
    for line in Path(path).read_text().splitlines():
        match = _LINE.match(line)
        if not match:
            continue
        key, raw = match.group(1), match.group(2).strip()
        if key not in known:
            continue
        try:
            current = getattr(book, key)
            if isinstance(current, bool):
                setattr(book, key, raw.lower() in {"true", "yes", "on", "1"})
            elif isinstance(current, int) and not isinstance(current, bool):
                setattr(book, key, int(float(raw)))
            elif isinstance(current, float):
                setattr(book, key, float(raw))
            else:
                setattr(book, key, raw)
        except (TypeError, ValueError):
            continue
    return book


def render(book: Playbook, *, provenance: dict[str, str] | None = None) -> str:
    """Write a playbook back out, preserving why each rule exists."""
    provenance = provenance or {}
    lines = [
        "# Playbook",
        "",
        "Craft rules the composer applies at render time. Each entry records",
        "where it came from, so a rule you no longer agree with can be traced",
        "and removed.",
        "",
        "Edited by `/reel-feedback` -- anything you say twice becomes a rule",
        "here -- and by hand whenever you like.",
        "",
    ]
    for f in fields(Playbook):
        value = getattr(book, f.name)
        note = provenance.get(f.name, "")
        lines.append(f"{f.name}: {value}" + (f"  # {note}" if note else ""))
    return "\n".join(lines) + "\n"
