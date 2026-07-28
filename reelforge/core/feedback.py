"""The part that learns.

Everything else in ReelForge is a fixed opinion about how video should be cut.
This is where those opinions change because you disagreed with them.

The design rests on one split, the same one used everywhere else: **the model
classifies, deterministic code decides.** A critique like "the captions sat too
low and there were way too many zooms" is natural language, and reading it is
exactly what a language model is good at. But *what a 'too many zooms' should do
to the punch cadence* is a rule -- it lives in :data:`ADJUSTMENTS`, it is
versioned, it is testable, and you can read it and disagree with it.

The alternative -- letting a model rewrite the playbook freely -- produces a
system that changes unpredictably and cannot explain itself, which is the exact
failure mode this whole project exists to avoid.

**Nothing becomes a rule the first time.** A one-off reaction to one clip is
noise; the same complaint twice is taste. Until then a correction is recorded
and applied to nothing.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .playbook import Playbook, render

# How many times you have to say something before it becomes a rule.
#
# One is too eager: every clip has something slightly wrong with it, and a
# playbook that swings on a single reaction never converges. Three is too slow
# to feel like it is listening. Two is the point where a preference has
# distinguished itself from a mood.
PROMOTION_THRESHOLD = 2


@dataclass(frozen=True)
class Adjustment:
    """What one kind of complaint does to one playbook field."""
    field: str
    delta: float                     # added per occurrence, in the field's units
    low: float
    high: float
    describe: str

    def apply(self, current: float) -> float:
        return round(min(self.high, max(self.low, current + self.delta)), 4)


# The complete vocabulary of corrections. An `(aspect, direction)` pair is all
# the critic agent has to produce; everything downstream is arithmetic.
#
# Directions are always from the viewer's point of view -- "captions too low"
# means they sat too low on screen, so the fix raises them.
ADJUSTMENTS: dict[tuple[str, str], Adjustment] = {
    ("captions", "too-low"): Adjustment(
        "caption_position", -0.05, 0.30, 0.85, "raise the captions"),
    ("captions", "too-high"): Adjustment(
        "caption_position", +0.05, 0.30, 0.85, "lower the captions"),

    ("zooms", "too-many"): Adjustment(
        "min_punch_gap", +1.5, 0.5, 30.0, "space the push-ins further apart"),
    ("zooms", "too-few"): Adjustment(
        "min_punch_gap", -1.0, 0.5, 30.0, "allow push-ins closer together"),
    ("zooms", "too-strong"): Adjustment(
        "punch_zoom", -0.04, 1.0, 1.5, "reduce how far a push-in travels"),
    ("zooms", "too-weak"): Adjustment(
        "punch_zoom", +0.04, 1.0, 1.5, "increase how far a push-in travels"),

    ("pacing", "too-tight"): Adjustment(
        "keep_pause", +0.08, 0.0, 1.0, "leave more of each pause"),
    ("pacing", "too-slack"): Adjustment(
        "keep_pause", -0.06, 0.0, 1.0, "tighten the pauses further"),

    ("emoji", "too-many"): Adjustment(
        "emoji_per_minute", -2.0, 0.0, 30.0, "use fewer emoji"),
    ("emoji", "too-few"): Adjustment(
        "emoji_per_minute", +2.0, 0.0, 30.0, "use more emoji"),

    ("hook", "too-slow"): Adjustment(
        "lead_in", -0.04, 0.0, 0.5, "start closer to the first word"),
    ("hook", "too-abrupt"): Adjustment(
        "lead_in", +0.04, 0.0, 0.5, "leave more air before the first word"),

    ("ending", "too-abrupt"): Adjustment(
        "lead_out", +0.10, 0.0, 1.5, "let the last word breathe"),
    ("ending", "too-long"): Adjustment(
        "lead_out", -0.06, 0.0, 1.5, "end sooner after the last word"),

    ("length", "too-long"): Adjustment(
        "max_seconds", -5.0, 10.0, 180.0, "cut shorter clips"),
    ("length", "too-short"): Adjustment(
        "max_seconds", +5.0, 10.0, 180.0, "allow longer clips"),

    ("cuts", "too-choppy"): Adjustment(
        "min_shot", +0.2, 0.3, 4.0, "hold each shot longer"),
    ("cuts", "too-static"): Adjustment(
        "min_shot", -0.1, 0.3, 4.0, "allow shorter shots"),
}

ASPECTS = sorted({aspect for aspect, _ in ADJUSTMENTS})


def directions_for(aspect: str) -> list[str]:
    return sorted(d for a, d in ADJUSTMENTS if a == aspect)


@dataclass
class Note:
    """One recorded correction."""
    aspect: str
    direction: str
    quote: str = ""                  # what was actually said, verbatim
    edl: str = ""
    origin: str = "user"             # "user" or "qc"
    ts: float = field(default_factory=lambda: time.time())

    @property
    def key(self) -> str:
        return f"{self.aspect}:{self.direction}"

    def as_dict(self) -> dict:
        return asdict(self)


class UnknownCorrection(ValueError):
    pass


def validate_note(aspect: str, direction: str) -> None:
    if (aspect, direction) not in ADJUSTMENTS:
        known = ", ".join(f"{a}/{d}" for a, d in sorted(ADJUSTMENTS))
        raise UnknownCorrection(
            f"no rule for {aspect!r}/{direction!r}. Known corrections: {known}"
        )


# --------------------------------------------------------------------------
# the decision log
# --------------------------------------------------------------------------

def append(log: Path, note: Note) -> None:
    validate_note(note.aspect, note.direction)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(note.as_dict()) + "\n")


def load(log: Path) -> list[Note]:
    """Read the log, skipping anything unreadable.

    Append-only and hand-editable, so a malformed line is a realistic outcome
    and must not cost the entire history of what you have taught it.
    """
    if not log.exists():
        return []
    notes = []
    for line in log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            data = json.loads(line)
            note = Note(**data)
            validate_note(note.aspect, note.direction)
        except (json.JSONDecodeError, TypeError, UnknownCorrection):
            continue
        notes.append(note)
    return notes


def counts(notes: list[Note], *, origin: str | None = None) -> dict[str, int]:
    tally: dict[str, int] = {}
    for note in notes:
        if origin and note.origin != origin:
            continue
        tally[note.key] = tally.get(note.key, 0) + 1
    return tally


# --------------------------------------------------------------------------
# promotion
# --------------------------------------------------------------------------

@dataclass
class Promotion:
    key: str
    field: str
    before: float
    after: float
    occurrences: int
    describe: str
    quote: str = ""

    def provenance(self, when: str) -> str:
        note = f"from feedback {when}: {self.describe}"
        if self.quote:
            note += f' -- "{self.quote[:70]}"'
        return f"{note} ({self.occurrences}x)"


def promote(notes: list[Note], book: Playbook, *,
            threshold: int = PROMOTION_THRESHOLD,
            already: dict[str, int] | None = None) -> tuple[Playbook, list[Promotion]]:
    """Turn repeated corrections into playbook changes.

    ``already`` records how many occurrences of each correction have previously
    been applied, so a note is never counted twice. Without it, re-running
    against the full log would compound every past correction on every run and
    the playbook would drift to its limits.
    """
    already = already or {}
    tally = counts(notes)
    promotions: list[Promotion] = []

    latest_quote = {}
    for note in notes:
        if note.quote:
            latest_quote[note.key] = note.quote

    for key, total in sorted(tally.items()):
        if total < threshold:
            continue
        applied = already.get(key, 0)
        pending = total - applied
        if pending <= 0:
            continue

        aspect, direction = key.split(":", 1)
        adjustment = ADJUSTMENTS[(aspect, direction)]
        before = float(getattr(book, adjustment.field))

        after = before
        for _ in range(pending):
            after = adjustment.apply(after)

        if abs(after - before) < 1e-9:
            continue                     # already at the limit; nothing to say

        # Preserve the field's type. fade_ms is an int and writing 22.4 into it
        # would produce a playbook that no longer round-trips through load().
        setattr(book, adjustment.field,
                int(round(after)) if isinstance(before, int) else after)
        promotions.append(Promotion(
            key=key, field=adjustment.field, before=before, after=after,
            occurrences=total, describe=adjustment.describe,
            quote=latest_quote.get(key, ""),
        ))

    return book, promotions


def pending(notes: list[Note], *, threshold: int = PROMOTION_THRESHOLD,
            already: dict[str, int] | None = None) -> dict[str, int]:
    """Corrections heard once, still short of becoming a rule.

    Worth surfacing: it tells you the system heard you and is waiting to see
    whether you meant it, rather than appearing to have ignored you.
    """
    already = already or {}
    return {k: v for k, v in counts(notes).items()
            if v < threshold and already.get(k, 0) == 0}


# --------------------------------------------------------------------------
# applying it
# --------------------------------------------------------------------------

APPLIED_FILE = "applied.json"


def apply_feedback(memory: Path, book: Playbook, *, when: str,
                   threshold: int = PROMOTION_THRESHOLD) -> tuple[Playbook, list[Promotion]]:
    """Read the log, promote what has earned it, and write the playbook back."""
    notes = load(memory / "decisions.jsonl")
    applied_path = memory / APPLIED_FILE
    already: dict[str, int] = {}
    if applied_path.exists():
        try:
            already = json.loads(applied_path.read_text())
        except json.JSONDecodeError:
            already = {}

    book, promotions = promote(notes, book, threshold=threshold, already=already)
    if not promotions:
        return book, []

    for promotion in promotions:
        already[promotion.key] = promotion.occurrences

    # Provenance accumulates across rounds. Rendering with only this round's
    # notes would erase the reason behind every rule learned previously --
    # leaving a playbook full of numbers nobody can account for, which is
    # exactly the state this file exists to prevent.
    provenance_path = memory / "provenance.json"
    provenance: dict[str, str] = {}
    if provenance_path.exists():
        try:
            provenance = json.loads(provenance_path.read_text())
        except json.JSONDecodeError:
            provenance = {}
    provenance.update({p.field: p.provenance(when) for p in promotions})

    memory.mkdir(parents=True, exist_ok=True)
    (memory / "playbook.md").write_text(render(book, provenance=provenance),
                                        encoding="utf-8")
    applied_path.write_text(json.dumps(already, indent=2), encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return book, promotions
