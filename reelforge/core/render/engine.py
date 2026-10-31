"""Which renderer draws the edit.

Remotion by default; ffmpeg when asked, or when Remotion is not installed.
Both take the same EDL and return the same result, so everything upstream --
the brain, the composer, QC -- neither knows nor cares which one ran.

The fallback is loud. A video that quietly came out of a different engine
looks different (spring-animated graphics versus static ones, browser
typography versus libass), and someone comparing two renders deserves to know
why they differ. So falling back is a warning in the result, not a log line.

Choose with ``--engine`` or ``REELFORGE_ENGINE``: ``auto`` (default),
``remotion``, ``ffmpeg``.
"""

from __future__ import annotations

import os
from typing import Callable

from . import ffmpeg_renderer, remotion_renderer

ENGINES = ("auto", "remotion", "ffmpeg")


def choose(name: str | None = None) -> tuple[str, Callable, list[str]]:
    """Return ``(engine name, render function, warnings)``.

    ``remotion`` explicitly requested but unavailable raises -- asking for one
    engine and silently getting the other is the wrong kind of helpful.
    """
    name = (name or os.environ.get("REELFORGE_ENGINE") or "auto").lower()
    if name not in ENGINES:
        raise ValueError(f"unknown engine {name!r}; choose from {ENGINES}")

    if name == "ffmpeg":
        return "ffmpeg", ffmpeg_renderer.render, []

    ok, why = remotion_renderer.available()
    if ok:
        return "remotion", remotion_renderer.render, []
    if name == "remotion":
        raise remotion_renderer.RemotionUnavailable(why)
    return "ffmpeg", ffmpeg_renderer.render, [
        f"rendered with ffmpeg because Remotion is unavailable: {why}"
    ]
