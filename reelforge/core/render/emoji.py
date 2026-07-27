"""Rasterise emoji to PNG for compositing.

Emoji are *not* drawn by libass. Colour emoji rendering there depends on
fontconfig resolving a CBDT/COLR font and on the libass build having been
compiled with the right support -- and when either is missing it fails
silently, drawing tofu boxes or nothing at all. On a headless server, which is
exactly what we run on, that is the common case rather than the edge case.

Compositing a PNG through ffmpeg's `overlay` filter always works, looks
identical everywhere, and has the side benefit that a PNG can be scaled and
animated by the filter graph in ways a subtitle glyph cannot.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

# Fonts that actually carry colour emoji bitmaps, most likely first.
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji-Regular.ttf",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    "/System/Library/Fonts/Apple Color Emoji.ttc",
]

# Noto Color Emoji is a bitmap font shipped at exactly 109px. FreeType refuses
# any other size for it, so we always rasterise at 109 and let ffmpeg scale.
NOTO_NATIVE_PX = 109


def find_font() -> Path | None:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return Path(candidate)
    if shutil.which("fc-match"):
        out = subprocess.run(
            ["fc-match", "-f", "%{file}", "emoji"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        if out and Path(out).exists():
            return Path(out)
    return None


def cache_path(cache_dir: Path, glyph: str, size: int) -> Path:
    # Keyed by codepoints rather than the glyph itself: a filename containing a
    # multi-codepoint emoji with a zero-width joiner is a portability problem
    # waiting to happen.
    key = "-".join(f"{ord(c):x}" for c in glyph)
    if len(key) > 60:                       # long ZWJ sequences
        key = hashlib.blake2b(glyph.encode(), digest_size=8).hexdigest()
    return cache_dir / f"{key}@{size}.png"


def render(glyph: str, size: int, cache_dir: Path) -> Path | None:
    """Rasterise one emoji to a transparent PNG, cached. None if unavailable."""
    dst = cache_path(cache_dir, glyph, size)
    if dst.exists():
        return dst

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    font_path = find_font()
    if font_path is None:
        return None

    try:
        font = ImageFont.truetype(str(font_path), NOTO_NATIVE_PX)
    except OSError:
        return None

    canvas = Image.new("RGBA", (NOTO_NATIVE_PX * 2, NOTO_NATIVE_PX * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        draw.text((NOTO_NATIVE_PX // 2, NOTO_NATIVE_PX // 2), glyph,
                  font=font, embedded_color=True)
    except (OSError, ValueError):
        return None

    box = canvas.getbbox()
    if box is None:                          # glyph missing from the font
        return None

    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.crop(box).resize((size, size), Image.LANCZOS).save(dst)
    return dst


def pop_expressions(at: float, dur: float, base_x: int, base_y: int,
                    size: int) -> tuple[str, str]:
    """Overlay x/y expressions giving a short overshoot-and-settle entrance.

    A static emoji that simply appears reads as a sticker pasted on. Growing it
    past its final size and letting it settle is the difference between an
    overlay and an animation -- and it costs nothing, because `overlay` already
    evaluates its position per frame.

    The scale itself is fixed by the PNG, so the pop is expressed as vertical
    travel: the glyph drops in and settles, which reads as weight.
    """
    rise = size * 0.35
    settle = min(0.28, dur * 0.4)
    progress = f"clip((t-{at:.3f})/{settle:.3f},0,1)"
    eased = f"(1-pow(1-{progress},3))"
    return str(base_x), f"{base_y}-{rise:.1f}*(1-{eased})"
