"""Sound effects, synthesised rather than licensed.

Every effect here is generated from noise and sine waves at render time. That
is a deliberate choice over shipping a folder of WAVs:

- **Nothing to license.** A sample pack downloaded from a forum is a copyright
  question waiting to happen on a channel that monetises. Synthesised audio has
  no provenance problem.
- **Nothing to download.** The box may be behind a restrictive network, and an
  editor that cannot render because a CDN is unreachable is not much of an
  editor.
- **Deterministic.** Each effect seeds its own generator from its name, so the
  same effect is byte-identical every run. That is what lets the cache key be
  the name and nothing else, and it means a re-render never quietly changes the
  audio.
- **Tunable.** Wanting the whoosh a little darker is a number here, not a
  request to a sound designer.

The catalogue is small on purpose. Six effects cover the cuts, emphasis and
reveals that short-form actually uses; a library of two hundred is a browsing
problem, not a capability.
"""

from __future__ import annotations

import hashlib
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SAMPLE_RATE = 48_000

#: Bumped when synthesis changes, so cached WAVs from an older formula are not
#: silently reused. Without this a tweak to the whoosh would only reach
#: machines that happened to have a cold cache.
SYNTH_VERSION = 1


@dataclass(frozen=True)
class Effect:
    name: str
    duration: float
    description: str
    #: Where the effect sits relative to the moment it marks. A whoosh reads as
    #: covering a cut only if it *starts before* it -- placed exactly on the
    #: frame it sounds like a mistake immediately after. Negative means early.
    lead: float = 0.0


CATALOGUE: dict[str, Effect] = {
    "whoosh": Effect("whoosh", 0.55, "Air movement over a cut or a fast push-in",
                     lead=-0.18),
    "whoosh_down": Effect("whoosh_down", 0.55, "Downward sweep, for a reveal landing",
                          lead=-0.18),
    "impact": Effect("impact", 0.70, "Low thump under a hard cut or a title landing",
                     lead=-0.02),
    "pop": Effect("pop", 0.16, "Small pop for an emoji or a caption word",
                  lead=-0.03),
    "click": Effect("click", 0.06, "Tight tick for a rapid list or a beat"),
    "riser": Effect("riser", 1.60, "Tension build into a reveal", lead=-1.50),
    "ding": Effect("ding", 0.90, "Bright bell for a point landing", lead=-0.02),
}


# ---------------------------------------------------------------------------
# building blocks
# ---------------------------------------------------------------------------

def _rng(name: str) -> np.random.Generator:
    """A generator seeded from the effect name -- same name, same noise, always."""
    digest = hashlib.blake2b(name.encode(), digest_size=8).digest()
    return np.random.default_rng(int.from_bytes(digest, "big"))


def _t(duration: float, sample_rate: int) -> np.ndarray:
    return np.arange(int(duration * sample_rate), dtype=np.float64) / sample_rate


def _env(t: np.ndarray, *, attack: float, decay: float, curve: float = 3.0) -> np.ndarray:
    """Attack-decay envelope.

    The attack is linear and the decay exponential because that is how physical
    sounds behave -- an exponential decay is the single biggest difference
    between "a sound effect" and "a beep".
    """
    out = np.ones_like(t)
    if attack > 0:
        rising = t < attack
        out[rising] = t[rising] / attack
    tail = np.clip(t - attack, 0.0, None)
    span = max(decay, 1e-6)
    return out * np.exp(-curve * tail / span)


def _sweep_lowpass(x: np.ndarray, cutoff: np.ndarray, sample_rate: int) -> np.ndarray:
    """One-pole lowpass with a per-sample cutoff.

    A biquad would be cleaner but a one-pole is enough: what sells a whoosh is
    the *motion* of the filter, not the steepness of its skirt. Written as an
    explicit loop because the coefficient changes every sample, which is
    exactly the case numpy cannot vectorise.
    """
    alpha = 1.0 - np.exp(-2.0 * np.pi * np.clip(cutoff, 20.0, sample_rate / 2.2) / sample_rate)
    out = np.empty_like(x)
    state = 0.0
    for i in range(x.shape[0]):
        state += alpha[i] * (x[i] - state)
        out[i] = state
    return out


def _stereo(mono: np.ndarray, width: float = 0.0) -> np.ndarray:
    """Duplicate to stereo, optionally with a small Haas-style spread."""
    if width <= 0:
        return np.stack([mono, mono], axis=1)
    delay = max(1, int(width * SAMPLE_RATE))
    right = np.concatenate([np.zeros(delay), mono[:-delay]])
    return np.stack([mono, right], axis=1)


def _normalise(stereo: np.ndarray, peak: float = 0.89) -> np.ndarray:
    """Scale to a fixed peak so gains in the EDL mean the same thing per effect."""
    high = float(np.max(np.abs(stereo))) if stereo.size else 0.0
    if high < 1e-9:
        return stereo
    return stereo * (peak / high)


# ---------------------------------------------------------------------------
# the effects
# ---------------------------------------------------------------------------

def _whoosh(duration: float, sample_rate: int, *, rising: bool) -> np.ndarray:
    t = _t(duration, sample_rate)
    noise = _rng("whoosh").standard_normal(t.shape[0])
    progress = t / max(t[-1], 1e-6)
    # A wide sweep is what makes it read as movement rather than as hiss.
    low, high = 300.0, 6500.0
    cutoff = low + (high - low) * (progress if rising else (1.0 - progress))
    band = _sweep_lowpass(noise, cutoff, sample_rate)
    band -= _sweep_lowpass(band, cutoff * 0.25, sample_rate)  # hollow out the low end
    shaped = band * _env(t, attack=duration * 0.35, decay=duration * 0.65, curve=2.4)
    return _normalise(_stereo(shaped, width=0.004))


def _impact(duration: float, sample_rate: int) -> np.ndarray:
    t = _t(duration, sample_rate)
    # A falling pitch is what makes a thump feel like weight landing rather
    # than a tone starting.
    pitch = 78.0 * np.exp(-3.2 * t)
    body = np.sin(2 * np.pi * np.cumsum(pitch) / sample_rate)
    body *= _env(t, attack=0.004, decay=duration * 0.8, curve=3.4)
    transient = _rng("impact").standard_normal(t.shape[0])
    transient = _sweep_lowpass(transient, np.full_like(t, 2200.0), sample_rate)
    transient *= _env(t, attack=0.001, decay=0.05, curve=6.0) * 0.5
    return _normalise(_stereo(body + transient))


def _pop(duration: float, sample_rate: int) -> np.ndarray:
    t = _t(duration, sample_rate)
    pitch = 780.0 * np.exp(-9.0 * t)
    tone = np.sin(2 * np.pi * np.cumsum(pitch) / sample_rate)
    tone *= _env(t, attack=0.002, decay=duration * 0.7, curve=5.0)
    return _normalise(_stereo(tone))


def _click(duration: float, sample_rate: int) -> np.ndarray:
    t = _t(duration, sample_rate)
    noise = _rng("click").standard_normal(t.shape[0])
    noise = noise - _sweep_lowpass(noise, np.full_like(t, 1400.0), sample_rate)
    return _normalise(_stereo(noise * _env(t, attack=0.0005, decay=0.012, curve=7.0)))


def _riser(duration: float, sample_rate: int) -> np.ndarray:
    t = _t(duration, sample_rate)
    progress = t / max(t[-1], 1e-6)
    noise = _rng("riser").standard_normal(t.shape[0])
    cutoff = 250.0 + 7200.0 * progress ** 2
    air = _sweep_lowpass(noise, cutoff, sample_rate)
    air -= _sweep_lowpass(air, cutoff * 0.3, sample_rate)
    pitch = 220.0 * (2.0 ** (2.2 * progress))
    tone = np.sin(2 * np.pi * np.cumsum(pitch) / sample_rate) * 0.35
    # Amplitude grows with the pitch so the build lands rather than plateaus --
    # but it must not still be at full amplitude on its last sample, which
    # would click. It peaks just before the end and releases fast, which is
    # also musically right: the riser hands over to whatever it was building
    # towards rather than fighting it.
    peak_at = 0.93
    rising = np.clip(progress / peak_at, 0.0, 1.0) ** 1.8
    releasing = np.clip((progress - peak_at) / (1.0 - peak_at), 0.0, 1.0)
    swell = rising * (1.0 - releasing) ** 2
    return _normalise(_stereo((air + tone) * swell, width=0.006))


def _ding(duration: float, sample_rate: int) -> np.ndarray:
    t = _t(duration, sample_rate)
    # An inharmonic partial is what separates a bell from an organ.
    fundamental = np.sin(2 * np.pi * 1180.0 * t) * _env(t, attack=0.002, decay=duration, curve=3.0)
    partial = np.sin(2 * np.pi * 1180.0 * 2.76 * t) * _env(
        t, attack=0.002, decay=duration * 0.45, curve=4.0) * 0.42
    return _normalise(_stereo(fundamental + partial, width=0.003))


_SYNTH = {
    "whoosh": lambda d, sr: _whoosh(d, sr, rising=True),
    "whoosh_down": lambda d, sr: _whoosh(d, sr, rising=False),
    "impact": _impact,
    "pop": _pop,
    "click": _click,
    "riser": _riser,
    "ding": _ding,
}


class UnknownEffect(KeyError):
    """Raised for a name not in the catalogue -- never silently substituted."""


def synth(name: str, *, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Generate one effect as float stereo in [-1, 1]."""
    effect = CATALOGUE.get(name)
    if effect is None:
        raise UnknownEffect(
            f"no sound effect named {name!r}; have {sorted(CATALOGUE)}"
        )
    return _SYNTH[name](effect.duration, sample_rate)


# ---------------------------------------------------------------------------
# caching to disk
# ---------------------------------------------------------------------------

def cache_path(cache_dir: Path, name: str, sample_rate: int = SAMPLE_RATE) -> Path:
    return cache_dir / "sfx" / f"{name}-{sample_rate}-v{SYNTH_VERSION}.wav"


def write_wav(samples: np.ndarray, dst: Path, sample_rate: int = SAMPLE_RATE) -> Path:
    """Write float stereo as 16-bit PCM, atomically."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    tmp = dst.with_suffix(dst.suffix + ".partial")
    with wave.open(str(tmp), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
    tmp.replace(dst)
    return dst


def render(name: str, cache_dir: Path, *, sample_rate: int = SAMPLE_RATE) -> Path:
    """Return a WAV for ``name``, synthesising it once and caching it."""
    dst = cache_path(cache_dir, name, sample_rate)
    if dst.exists():
        return dst
    return write_wav(synth(name, sample_rate=sample_rate), dst, sample_rate)


def suggest_for_transition(kind: str) -> str | None:
    """Which effect suits a transition, or ``None`` to leave it silent.

    A plain cut gets nothing. Adding a whoosh to every cut is the single most
    common way an edit starts sounding like a template, and the restraint
    belongs in the default rather than in a note in the docs.
    """
    return {"whip": "whoosh", "dissolve": "whoosh_down", "fade": None, "cut": None}.get(kind)
