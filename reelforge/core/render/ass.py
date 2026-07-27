"""ASS subtitle generation for word-level captions.

Captions are the single biggest visual difference between raw footage and
something that reads as edited, and word-level timing is what makes them feel
alive rather than pasted on.

Two decisions worth stating plainly:

**Emoji are not drawn here.** libass renders colour emoji only when fontconfig
cooperates, and on a headless server it usually does not -- failing silently by
drawing tofu or nothing at all. Emoji go through PNG overlays in the filter
graph instead, where the result is deterministic. This file handles text only.

**Styling lives in the ASS file, not in a `force_style` argument.** A caption
look you can open, read, and diff is worth far more than one buried in a
command line.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..edl import CaptionWord, Target

# Safe areas. Platform chrome -- the caption, the username, the share tray --
# covers roughly the bottom fifth and the top eighth of a vertical video. Text
# placed inside those zones is not small, it is invisible.
SAFE_TOP = 0.14
SAFE_BOTTOM = 0.20


@dataclass(frozen=True)
class CaptionStyle:
    name: str = "karaoke-bold"
    font: str = "Inter"
    size_ratio: float = 0.055        # of frame height
    primary: str = "&H00FFFFFF"      # ASS is &HAABBGGRR -- not RGB
    highlight: str = "&H0000E5FF"    # amber, on the current word
    outline: str = "&H00000000"
    outline_w: float = 3.5
    shadow: float = 0.0
    bold: int = -1                   # ASS booleans are -1/0
    max_words: int = 4
    position: float = 0.72           # vertical centre, fraction of height
    margin_ratio: float = 0.06       # horizontal margin, fraction of width

    def max_chars(self, target: "Target") -> int:
        """Characters that actually fit on one line at this size.

        Derived rather than fixed. A hardcoded count is wrong the moment the
        font size or the output width changes -- at 0.055 of a 1920px frame the
        glyphs are 105px tall, and a nominal 22 characters overflows a 1080px
        frame by a comfortable margin. Getting this wrong is invisible in the
        EDL and obvious in the render.
        """
        usable = target.width * (1 - 2 * self.margin_ratio)
        # 0.52 em is a good average advance for a bold humanist sans; the -1
        # keeps a descender or a wide capital from being the one that spills.
        advance = target.height * self.size_ratio * 0.52
        return max(8, int(usable / advance) - 1)


STYLES = {
    "karaoke-bold": CaptionStyle(),
    "clean": CaptionStyle(name="clean", highlight="&H00FFFFFF", outline_w=2.0,
                          size_ratio=0.045),
    "punch": CaptionStyle(name="punch", size_ratio=0.07, max_words=3,
                          highlight="&H004CFF4C", outline_w=4.0),
}


def _ts(seconds: float) -> str:
    """ASS timestamps are ``H:MM:SS.cc`` -- centiseconds, one digit of hours."""
    seconds = max(0.0, seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{int(s):02d}.{int(round(s % 1 * 100)):02d}"


def group_words(words: list[CaptionWord], style: CaptionStyle,
                target: Target) -> list[list[CaptionWord]]:
    """Group words into on-screen phrases.

    Grouped by *both* word count and character count. Word count alone puts
    "internationalisation strategies" on one line and overflows; character
    count alone splits "I do" across two cards.

    A pause also breaks a group -- when a speaker stops, the caption should
    stop with them rather than straddling the silence.
    """
    max_chars = style.max_chars(target)
    groups: list[list[CaptionWord]] = []
    current: list[CaptionWord] = []
    chars = 0

    for word in words:
        gap = word.start - current[-1].end if current else 0.0
        too_long = chars + len(word.text) + 1 > max_chars
        too_many = len(current) >= style.max_words
        if current and (too_long or too_many or gap > 0.7):
            groups.append(current)
            current, chars = [], 0
        current.append(word)
        chars += len(word.text) + 1

    if current:
        groups.append(current)
    return groups


def header(target: Target, style: CaptionStyle) -> str:
    size = int(round(target.height * style.size_ratio))
    # ASS vertical margin is measured from the bottom for bottom-aligned text.
    margin_v = int(round(target.height * (1 - style.position)))
    margin_h = int(round(target.width * style.margin_ratio))
    return "\n".join([
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {target.width}",
        f"PlayResY: {target.height}",
        "WrapStyle: 2",              # no automatic wrapping -- we group above
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: RF,{style.font},{size},{style.primary},{style.highlight},"
        f"{style.outline},&H64000000,{style.bold},0,0,0,100,100,0,0,1,"
        f"{style.outline_w},{style.shadow},2,{margin_h},{margin_h},{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ])


def _escape(text: str) -> str:
    """Neutralise ASS markup in transcribed speech.

    A brace in a transcript would otherwise open an override block and silently
    swallow the rest of the line.
    """
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def dialogue_lines(groups: list[list[CaptionWord]], style: CaptionStyle) -> list[str]:
    """One Dialogue event per phrase, with per-word highlight timing."""
    lines = []
    for group in groups:
        start, end = group[0].start, group[-1].end
        # Concatenated with no separator: the word spacing is carried inside the
        # text runs. Joining the pieces with a space instead would insert one
        # between an override block and the next, and any transformation of the
        # assembled string risks eating a brace -- at which point libass stops
        # seeing override tags and prints them as literal text.
        pieces: list[str] = []
        for index, word in enumerate(group):
            # Karaoke durations are centiseconds and *relative* to the previous
            # word, so a gap has to be carried explicitly or the highlight
            # drifts ahead of the speech.
            previous_end = group[index - 1].end if index else word.start
            lead = max(0, int(round((word.start - previous_end) * 100)))
            hold = max(1, int(round((word.end - word.start) * 100)))
            if lead:
                pieces.append(f"{{\\k{lead}}}")
            text = _escape(word.text)
            if index:
                text = " " + text
            pieces.append(f"{{\\kf{hold}}}{text}")
        lines.append(
            f"Dialogue: 0,{_ts(start)},{_ts(end)},RF,,0,0,0,,{''.join(pieces)}"
        )
    return lines


def build(words: list[CaptionWord], target: Target, style_name: str = "karaoke-bold") -> str:
    """Render a complete ASS file for a caption track."""
    style = STYLES.get(style_name, STYLES["karaoke-bold"])
    if not words:
        return header(target, style) + "\n"
    groups = group_words(words, style, target)
    return "\n".join([header(target, style), *dialogue_lines(groups, style)]) + "\n"


def safe_area(target: Target) -> tuple[int, int]:
    """Pixel rows outside which text will be covered by platform UI."""
    return int(target.height * SAFE_TOP), int(target.height * (1 - SAFE_BOTTOM))
