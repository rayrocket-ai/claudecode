"""Speech to word-level timestamps.

Everything downstream is built on this. A cut lands mid-word, a caption
desynchronises, or a filler word survives entirely because of the quality of
the word boundaries here -- so this is the one stage worth being fussy about.

Written as an adapter around faster-whisper. Swapping in a hosted engine
(ElevenLabs Scribe, Deepgram) for difficult audio means implementing
:func:`transcribe` and nothing else changes.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

# Words a viewer never notices missing, but always notices hearing. Matched
# case-insensitively against the word with punctuation stripped.
FILLERS = {
    "um", "umm", "uh", "uhh", "er", "erm", "ah", "hmm", "mm",
    "like", "basically", "actually", "literally", "right", "so", "yeah",
}
# The unconditional ones. "like" and "so" are only filler *sometimes* -- "I like
# it" and "so we shipped" are real speech -- so they are never cut on the word
# alone; the brain decides using surrounding context.
HARD_FILLERS = {"um", "umm", "uh", "uhh", "er", "erm", "erm", "hmm"}


@dataclass
class Word:
    text: str
    start: float
    end: float
    confidence: float = 1.0
    speaker: str | None = None

    @property
    def normalized(self) -> str:
        return re.sub(r"[^\w']", "", self.text).lower()

    @property
    def is_hard_filler(self) -> bool:
        return self.normalized in HARD_FILLERS

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class Transcript:
    words: list[Word]
    language: str
    duration: float
    model: str

    def as_dict(self) -> dict:
        return {
            "language": self.language,
            "duration": self.duration,
            "model": self.model,
            "words": [asdict(w) for w in self.words],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transcript":
        return cls(
            words=[Word(**w) for w in data["words"]],
            language=data["language"],
            duration=data["duration"],
            model=data["model"],
        )

    def text_between(self, start: float, end: float) -> str:
        return " ".join(w.text for w in self.words if w.start >= start and w.end <= end)

    def as_timestamped_lines(self, *, window: float = 8.0) -> str:
        """Compact ``[mm:ss] text`` rendering -- the brain's primary input.

        Word-level JSON is far too verbose to hand a model directly: an hour of
        speech is roughly 9,000 words and 40x that in JSON tokens. Grouping into
        windows keeps enough timing precision to locate a moment, and the exact
        word boundaries are looked up afterwards from the same data.
        """
        if not self.words:
            return ""
        lines, bucket, bucket_start = [], [], self.words[0].start
        for word in self.words:
            if word.start - bucket_start >= window and bucket:
                lines.append(f"[{_mmss(bucket_start)}] {' '.join(bucket)}")
                bucket, bucket_start = [], word.start
            bucket.append(word.text)
        if bucket:
            lines.append(f"[{_mmss(bucket_start)}] {' '.join(bucket)}")
        return "\n".join(lines)


def _mmss(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def transcribe(
    audio: Path,
    *,
    model: str = "distil-large-v3",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str | None = "en",
    workers: int = 1,
) -> Transcript:
    """Transcribe an audio file to word-level timestamps."""
    from faster_whisper import WhisperModel  # imported lazily: heavy, and
                                             # /reel-doctor must run without it

    whisper = WhisperModel(
        model, device=device, compute_type=compute_type, num_workers=workers
    )
    segments, info = whisper.transcribe(
        str(audio),
        language=language,
        word_timestamps=True,          # the entire point
        vad_filter=True,               # skip silence rather than hallucinating
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,  # stops one bad segment cascading
        beam_size=5,
    )

    words = [
        Word(
            text=w.word.strip(),
            start=round(w.start, 3),
            end=round(w.end, 3),
            confidence=round(getattr(w, "probability", 1.0), 3),
        )
        for segment in segments
        for w in (segment.words or [])
        if w.word.strip()
    ]

    return Transcript(
        words=words,
        language=info.language or language or "en",
        duration=round(info.duration, 3),
        model=model,
    )


# --------------------------------------------------------------------------
# derived signals -- pure functions over a transcript, unit-tested
# --------------------------------------------------------------------------

def filler_spans(transcript: Transcript, *, pad: float = 0.02) -> list[tuple[float, float]]:
    """Spans of unambiguous filler, safe to cut without reading context.

    Padded outward slightly: whisper tends to clip the leading consonant of a
    word, and a cut that lands a frame late leaves an audible stub of the "um".
    """
    return [
        (max(0.0, w.start - pad), w.end + pad)
        for w in transcript.words
        if w.is_hard_filler
    ]


def dead_air(
    transcript: Transcript, *, min_gap: float = 0.6, keep: float = 0.25
) -> list[tuple[float, float]]:
    """Gaps between words long enough to cut, minus a beat left for breath.

    Cutting a pause to zero makes speech sound machine-gunned. Leaving ``keep``
    seconds preserves the rhythm of natural speech while still removing the
    dead weight -- this is the difference between a tight edit and an
    exhausting one.
    """
    spans = []
    for prev, nxt in zip(transcript.words, transcript.words[1:]):
        gap = nxt.start - prev.end
        if gap >= min_gap:
            spans.append((prev.end + keep / 2, nxt.start - keep / 2))
    return spans


def repeated_takes(
    transcript: Transcript, *, window: int = 12, min_words: int = 4, similarity: float = 0.8
) -> list[tuple[float, float]]:
    """Spans where a phrase is restarted, keeping the last attempt.

    When someone flubs a line and says it again, the earlier attempt is the one
    to drop -- the retake is almost always the better read. Detection is
    deliberately conservative: normalised text similarity over a short sliding
    window, so it catches genuine restarts and not a speaker legitimately
    repeating themselves for emphasis.
    """
    words = transcript.words
    doomed: list[tuple[float, float]] = []
    i = 0
    while i < len(words) - min_words * 2:
        for span in range(min_words, min(window, (len(words) - i) // 2) + 1):
            a = [w.normalized for w in words[i:i + span]]
            b = [w.normalized for w in words[i + span:i + 2 * span]]
            if not a or not b:
                continue
            matches = sum(1 for x, y in zip(a, b) if x == y)
            if matches / span >= similarity:
                doomed.append((words[i].start, words[i + span - 1].end))
                i += span
                break
        else:
            i += 1
            continue
    return _merge(doomed)


def _merge(spans: Iterable[tuple[float, float]], *, gap: float = 0.05) -> list[tuple[float, float]]:
    ordered = sorted(spans)
    if not ordered:
        return []
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start - merged[-1][1] <= gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(a, b) for a, b in merged]
