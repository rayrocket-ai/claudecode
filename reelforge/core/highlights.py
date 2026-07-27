"""What the brain returns, and how clips get ranked.

The division of labour here is the whole design. The language model decides
**what is worth keeping** -- which moment is a hook, where a thought begins and
ends, which take was the good one. It never decides **how to cut it**: shot
lengths, breath padding, zoom cadence, caption grouping and emoji density are
craft rules, they live in :mod:`compose`, and they are read from the playbook so
they can be learned.

That split is what makes the system improvable. Taste that lives in a prompt is
invisible and unversioned; taste that lives in a rules file can be diffed,
explained, and corrected.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# The schema handed to the brain. Kept flat and small on purpose: every optional
# nesting level is another thing a model can get subtly wrong, and everything
# here has to survive being round-tripped through JSON.
HIGHLIGHTS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["clips"],
    "properties": {
        "clips": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["start", "end", "hook", "why", "scores"],
                "properties": {
                    "start": {"type": "number", "description": "source seconds"},
                    "end": {"type": "number"},
                    "hook": {
                        "type": "string",
                        "description": "the opening line, verbatim from the transcript",
                    },
                    "why": {
                        "type": "string",
                        "description": "one sentence: why this works as a standalone clip",
                    },
                    "title": {"type": "string"},
                    "emphasis": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "source timestamps of the strongest beats",
                    },
                    "drop": {
                        "type": "array",
                        "description": "spans to cut from inside the clip",
                        "items": {
                            "type": "object",
                            "required": ["start", "end", "reason"],
                            "properties": {
                                "start": {"type": "number"},
                                "end": {"type": "number"},
                                "reason": {
                                    "type": "string",
                                    "enum": ["filler", "repeat", "tangent", "dead-air"],
                                },
                            },
                        },
                    },
                    "scores": {
                        "type": "object",
                        "required": ["hook", "self_contained", "payoff", "quotable"],
                        "properties": {
                            "hook": {"type": "number", "minimum": 0, "maximum": 10},
                            "self_contained": {"type": "number", "minimum": 0, "maximum": 10},
                            "payoff": {"type": "number", "minimum": 0, "maximum": 10},
                            "quotable": {"type": "number", "minimum": 0, "maximum": 10},
                        },
                    },
                },
            },
        }
    },
}

# How the four scores combine into one ranking.
#
# `hook` dominates because short-form attention is decided in the first second
# and nothing later recovers a weak opening. `self_contained` is next: a clip
# that needs context the viewer does not have reads as confusing regardless of
# how good the content is. `payoff` and `quotable` are real but secondary --
# they make a clip good rather than watched.
SCORE_WEIGHTS = {
    "hook": 0.40,
    "self_contained": 0.30,
    "payoff": 0.20,
    "quotable": 0.10,
}


@dataclass
class Drop:
    start: float
    end: float
    reason: str = "filler"


@dataclass
class Clip:
    start: float
    end: float
    hook: str = ""
    why: str = ""
    title: str = ""
    emphasis: list[float] = field(default_factory=list)
    drop: list[Drop] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def raw_duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def kept_duration(self) -> float:
        """Duration after the internal drops are removed."""
        dropped = sum(
            min(d.end, self.end) - max(d.start, self.start)
            for d in self.drop
            if d.end > self.start and d.start < self.end
        )
        return max(0.0, self.raw_duration - dropped)

    def score(self, *, target_seconds: tuple[float, float] = (15.0, 59.0)) -> float:
        """Weighted rank, penalised for falling outside the useful length band.

        Length is a gate rather than a weight. A brilliant 4-second clip is not
        a reel and a brilliant 3-minute one is not either, so length scales the
        result instead of adding to it -- otherwise a high content score would
        drag through clips that cannot be posted.
        """
        base = sum(SCORE_WEIGHTS[k] * float(self.scores.get(k, 0)) for k in SCORE_WEIGHTS)
        low, high = target_seconds
        duration = self.kept_duration
        if duration < low:
            # Ramp rather than cliff: a 14s clip is nearly fine, a 5s one is not.
            base *= max(0.1, duration / low)
        elif duration > high:
            base *= max(0.1, high / duration)
        return round(base, 4)

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Clip":
        return cls(
            start=float(d["start"]),
            end=float(d["end"]),
            hook=d.get("hook", ""),
            why=d.get("why", ""),
            title=d.get("title", ""),
            emphasis=[float(t) for t in d.get("emphasis", [])],
            drop=[Drop(float(x["start"]), float(x["end"]), x.get("reason", "filler"))
                  for x in d.get("drop", [])],
            scores={k: float(v) for k, v in (d.get("scores") or {}).items()},
        )


def parse(payload: dict) -> list[Clip]:
    """Read the brain's output into clips, discarding anything unusable.

    Tolerant by design. A model that returns nine good clips and one with a
    reversed timestamp should give us nine clips, not an exception -- the
    alternative is re-running an expensive analysis over an hour of video
    because of one malformed entry.
    """
    clips = []
    for raw in payload.get("clips", []):
        try:
            clip = Clip.from_dict(raw)
        except (KeyError, TypeError, ValueError):
            continue
        if clip.raw_duration <= 0:
            continue
        clips.append(clip)
    return clips


def rank(clips: list[Clip], *, count: int, target_seconds: tuple[float, float],
         min_gap: float = 5.0) -> list[Clip]:
    """Best ``count`` clips, avoiding near-duplicates of the same moment.

    Overlap suppression matters more than it looks: asked for the best moments
    of a talk, a model will happily return the same strong passage three times
    with slightly different boundaries. Three near-identical reels is a worse
    outcome than two distinct ones.
    """
    ordered = sorted(clips, key=lambda c: c.score(target_seconds=target_seconds),
                     reverse=True)
    chosen: list[Clip] = []
    for clip in ordered:
        if len(chosen) >= count:
            break
        if any(clip.start < c.end + min_gap and c.start < clip.end + min_gap
               for c in chosen):
            continue
        chosen.append(clip)
    return chosen
