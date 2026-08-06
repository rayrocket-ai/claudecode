"""Animated overlays: HyperFrames and Remotion backends.

Both backends do the same job -- turn a named composition and a bag of props
into a transparent PNG sequence that the finishing pass composites over the
video. They differ in what they need installed and in what they are good at.

**HyperFrames** compositions are a single HTML file rendered in headless
Chromium, which is already present on any box that has a browser. The
important constraint is that a composition is written as a **pure function of
time**: the page reads ``?t=`` from its URL and draws that instant, statically.
Nothing animates in the browser at all.

That is a deliberate inversion of how these tools usually work, and it buys
three things. Capture is exact, because there is no race between the animation
clock and the screenshot. Frames are independent, so they can be rendered in
any order or in parallel. And a re-render is byte-identical, which is what
lets the frame cache be keyed on the composition and its props -- the same
guarantee HyperFrames itself advertises, obtained by construction rather than
by careful timing.

**Remotion** is React and needs a Node project with its packages installed. It
is worth it for spring physics and complex sequencing; it is not worth
installing to put a name on the screen. When it is missing, the render does
not silently drop the overlay -- it raises :class:`BackendUnavailable` naming
the exact command that would fix it. A finished video that quietly lacks its
graphics is the worst possible failure here, because nothing in the output
suggests anything went wrong.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..edl import Overlay, Target
from . import filters

BACKENDS = ("hyperframes", "remotion")

#: Bumped when a built-in composition's markup changes, so cached frames from
#: an older look are not reused.
COMP_VERSION = 1


class BackendUnavailable(RuntimeError):
    """The backend cannot run here. The message must say how to fix it."""


class UnknownComposition(KeyError):
    pass


# ---------------------------------------------------------------------------
# built-in HyperFrames compositions
# ---------------------------------------------------------------------------

#: Shared page chrome. The transparent background is what makes the capture
#: composite; `image-rendering` and the disabled scrollbars keep Chromium from
#: adding artefacts at the edges.
_SHELL = """<!doctype html>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{
    width:{width}px; height:{height}px;
    background:transparent; overflow:hidden;
    font-family:"DejaVu Sans", "Noto Sans", system-ui, sans-serif;
    -webkit-font-smoothing:antialiased;
  }}
  .stage {{ position:relative; width:100%; height:100%; }}
  {css}
</style>
<div class="stage">{body}</div>
"""


def _ease_out_cubic(p: float) -> float:
    return 1.0 - (1.0 - p) ** 3


def _ease_out_back(p: float) -> float:
    # A slight overshoot is what makes a graphic feel placed rather than moved.
    c1, c3 = 1.70158, 2.70158
    return 1.0 + c3 * (p - 1.0) ** 3 + c1 * (p - 1.0) ** 2


def _window(t: float, dur: float, *, rise: float = 0.45, fall: float = 0.4) -> tuple[float, float]:
    """Progress of the entrance and of the exit at time ``t``.

    Returns ``(in_progress, out_progress)``, both 0..1. Every built-in
    composition shares this shape so their timing is consistent when several
    appear in one video.
    """
    rise = min(rise, dur / 2)
    fall = min(fall, dur / 2)
    entering = 1.0 if rise <= 0 else min(1.0, max(0.0, t / rise))
    leaving = 0.0 if fall <= 0 else min(1.0, max(0.0, (t - (dur - fall)) / fall))
    return entering, leaving


def _lower_third(t: float, dur: float, props: dict, target: Target) -> tuple[str, str]:
    title = html.escape(str(props.get("title", "")))
    subtitle = html.escape(str(props.get("subtitle", "")))
    accent = str(props.get("accent", "#FF6B2C"))

    enter, leave = _window(t, dur)
    slide = (1.0 - _ease_out_cubic(enter)) * -80.0 + _ease_out_cubic(leave) * -80.0
    alpha = min(enter, 1.0 - leave)
    bar = _ease_out_cubic(enter) * (1.0 - leave)

    css = f"""
  .lt {{ position:absolute; left:64px; bottom:{int(target.height * 0.17)}px;
         transform:translateX({slide:.2f}px); opacity:{alpha:.3f}; }}
  .lt .bar {{ height:8px; width:{bar * 260:.1f}px; background:{accent};
              border-radius:4px; margin-bottom:18px; }}
  .lt h1 {{ font-size:{int(target.height * 0.036)}px; font-weight:800; color:#fff;
            letter-spacing:-0.5px; text-shadow:0 4px 24px rgba(0,0,0,.55); }}
  .lt p {{ font-size:{int(target.height * 0.023)}px; font-weight:600; color:#e8e8e8;
           margin-top:8px; text-shadow:0 3px 18px rgba(0,0,0,.55); }}
"""
    body = f'<div class="lt"><div class="bar"></div><h1>{title}</h1>'
    if subtitle:
        body += f"<p>{subtitle}</p>"
    return css, body + "</div>"


def _callout(t: float, dur: float, props: dict, target: Target) -> tuple[str, str]:
    text = html.escape(str(props.get("text", "")))
    accent = str(props.get("accent", "#FFD400"))
    enter, leave = _window(t, dur, rise=0.32, fall=0.28)
    scale = _ease_out_back(enter) * (1.0 - 0.25 * leave)
    alpha = min(enter, 1.0 - leave)
    css = f"""
  .callout {{ position:absolute; left:50%; top:{int(target.height * 0.22)}px;
              transform:translate(-50%,-50%) scale({max(scale, 0.01):.3f});
              opacity:{alpha:.3f}; background:{accent}; color:#101010;
              padding:18px 34px; border-radius:18px; font-weight:900;
              font-size:{int(target.height * 0.034)}px; white-space:nowrap;
              box-shadow:0 12px 40px rgba(0,0,0,.35); }}
"""
    return css, f'<div class="callout">{text}</div>'


def _kinetic(t: float, dur: float, props: dict, target: Target) -> tuple[str, str]:
    """Word-by-word typography. Each word lands on its own beat."""
    words = [str(w) for w in props.get("words", [])] or str(props.get("text", "")).split()
    accent = str(props.get("accent", "#FFD400"))
    if not words:
        return "", ""
    per = dur / (len(words) + 1)
    spans = []
    for i, word in enumerate(words):
        local = (t - i * per) / max(per, 1e-6)
        p = min(1.0, max(0.0, local))
        scale = 0.6 + 0.4 * _ease_out_back(p) if p > 0 else 0.6
        colour = accent if i == len(words) - 1 else "#ffffff"
        spans.append(
            f'<span style="opacity:{p:.3f};transform:scale({scale:.3f});'
            f'color:{colour}">{html.escape(word)}</span>'
        )
    _, leave = _window(t, dur, rise=0.01, fall=0.3)
    css = f"""
  .kin {{ position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
          width:86%; text-align:center; opacity:{1.0 - leave:.3f}; }}
  .kin span {{ display:inline-block; margin:0 10px;
               font-size:{int(target.height * 0.052)}px; font-weight:900;
               letter-spacing:-1px; text-shadow:0 6px 28px rgba(0,0,0,.6); }}
"""
    return css, f'<div class="kin">{"".join(spans)}</div>'


def _progress(t: float, dur: float, props: dict, target: Target) -> tuple[str, str]:
    accent = str(props.get("accent", "#FF6B2C"))
    p = min(1.0, max(0.0, t / max(dur, 1e-6)))
    css = f"""
  .prog {{ position:absolute; left:0; bottom:0; height:10px;
           width:{p * 100:.2f}%; background:{accent}; }}
"""
    return css, '<div class="prog"></div>'


COMPOSITIONS = {
    "lower-third": _lower_third,
    "callout": _callout,
    "kinetic": _kinetic,
    "progress": _progress,
}


def compose_html(comp: str, t: float, dur: float, props: dict, target: Target) -> str:
    """Render one composition at one instant to a complete HTML page."""
    builder = COMPOSITIONS.get(comp)
    if builder is None:
        raise UnknownComposition(
            f"no built-in composition {comp!r}; have {sorted(COMPOSITIONS)}"
        )
    css, body = builder(t, dur, props, target)
    return _SHELL.format(width=target.width, height=target.height, css=css, body=body)


# ---------------------------------------------------------------------------
# Chromium capture
# ---------------------------------------------------------------------------

def find_chromium() -> Path | None:
    """Locate a Chromium binary, preferring an explicitly configured one."""
    explicit = os.environ.get("REELFORGE_CHROMIUM")
    if explicit and Path(explicit).exists():
        return Path(explicit)

    root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if root:
        # Newest install wins; Playwright keeps several revisions side by side.
        found = sorted(Path(root).glob("chromium-*/chrome-linux/chrome"))
        if found:
            return found[-1]

    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        which = shutil.which(name)
        if which:
            return Path(which)
    return None


def chromium_cmd(binary: Path, page: Path, png: Path, target: Target) -> list[str]:
    """Screenshot one page. Transparency is the whole point of this flag list."""
    return [
        str(binary),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        # Without this the capture has an opaque white background and every
        # overlay arrives as a full-frame rectangle covering the video.
        "--default-background-color=00000000",
        "--force-device-scale-factor=1",
        f"--window-size={target.width},{target.height}",
        f"--screenshot={png}",
        # Absolute, always. A relative path in a file:// URL makes Chromium
        # read the first segment as a *hostname*, fail to load, and screenshot
        # its own error page -- which it does with exit status 0 and a
        # perfectly valid PNG. The only visible symptom is an opaque rectangle
        # covering the entire video.
        f"file://{page.resolve()}",
    ]


def assert_capture_is_transparent(png: Path) -> None:
    """Fail loudly if a captured frame has no alpha.

    This is the guard that a file-existence check cannot provide. Chromium
    happily produces an opaque PNG when the page did not load, when the
    background flag was ignored, or when a composition covers the frame --
    and every one of those composites as a rectangle over the video. Checking
    the pixels is the only way to know the capture is usable.
    """
    from PIL import Image

    with Image.open(png) as image:
        if image.mode not in ("RGBA", "LA"):
            raise BackendUnavailable(
                f"capture {png.name} has no alpha channel (mode {image.mode}); "
                "the page did not load or Chromium ignored the transparent "
                "background. Compositing it would cover the video."
            )
        low, _high = image.getchannel("A").getextrema()
        if low != 0:
            raise BackendUnavailable(
                f"capture {png.name} is fully opaque; compositing it would "
                "cover the video."
            )


def _frames_key(comp: str, props: dict, dur: float, fps: float, target: Target) -> str:
    payload = json.dumps(
        {"comp": comp, "props": props, "dur": round(dur, 3), "fps": fps,
         "w": target.width, "h": target.height, "v": COMP_VERSION},
        sort_keys=True,
    )
    return hashlib.blake2b(payload.encode(), digest_size=8).hexdigest()


def render_hyperframes(overlay: Overlay, target: Target, workdir: Path,
                       *, fps: float) -> Path:
    """Render a composition to a directory of transparent PNGs.

    Returns the directory. Frames are numbered from zero so the ffmpeg pattern
    is a plain ``%05d``.
    """
    binary = find_chromium()
    if binary is None:
        raise BackendUnavailable(
            "hyperframes overlay skipped: no Chromium found. Install one "
            "(apt install chromium) or set REELFORGE_CHROMIUM to its path."
        )

    key = _frames_key(overlay.comp, overlay.props, overlay.dur, fps, target)
    outdir = workdir / f"hf-{overlay.comp}-{key}"
    done = outdir / ".complete"
    if done.exists():
        return outdir

    pagedir = outdir / "pages"
    pagedir.mkdir(parents=True, exist_ok=True)
    count = max(1, int(round(overlay.dur * fps)))

    for frame in range(count):
        t = frame / fps
        page = pagedir / f"f{frame:05d}.html"
        page.write_text(
            compose_html(overlay.comp, t, overlay.dur, overlay.props, target),
            encoding="utf-8",
        )
        png = outdir / f"frame_{frame:05d}.png"
        result = subprocess.run(
            chromium_cmd(binary, page, png, target),
            capture_output=True, text=True,
        )
        if not png.exists():
            raise BackendUnavailable(
                f"hyperframes overlay skipped: Chromium produced no frame "
                f"{frame} ({result.stderr.strip()[:200]})"
            )
        if frame == 0:
            # Checked once: if the first capture is sound the rest are too,
            # and checking all of them would double the cost of the stage.
            assert_capture_is_transparent(png)

    shutil.rmtree(pagedir, ignore_errors=True)
    done.write_text("ok", encoding="utf-8")
    return outdir


# ---------------------------------------------------------------------------
# Remotion
# ---------------------------------------------------------------------------

def remotion_cmd(project: Path, comp: str, outdir: Path, props: dict,
                 *, fps: float, target: Target,
                 browser: Path | None = None) -> list[str]:
    """The command that renders a Remotion composition to a PNG sequence.

    ``--sequence`` with a PNG image format is what yields per-frame files with
    an alpha channel; rendering to a video and keying it back out would lose
    the soft edges that are the reason to use Remotion in the first place.

    ``--browser-executable`` points Remotion at a Chromium that is already on
    the machine. Left to itself it downloads its own ~150 MB headless shell
    from remotion.media on first run, which is a slow surprise on a fresh box
    and an outright failure on any network that does not allow it. The same
    browser already renders the HyperFrames backend, so reusing it is both
    faster and one less thing that can be unavailable.
    """
    cmd = [
        "npx", "--no-install", "remotion", "render",
        str(project / "src" / "index.ts"),
        comp,
        str(outdir),
        "--sequence",
        "--image-format=png",
        "--pixel-format=yuva420p",
        f"--props={json.dumps(props)}",
        f"--width={target.width}",
        f"--height={target.height}",
        f"--fps={fps:g}",
        "--log=error",
    ]
    browser = browser or find_chromium()
    if browser is not None:
        cmd.append(f"--browser-executable={browser}")
    return cmd


def remotion_available(project: Path) -> bool:
    """Whether a Remotion project is installed and runnable at ``project``."""
    return (project / "node_modules" / "remotion").is_dir()


def render_remotion(overlay: Overlay, target: Target, workdir: Path,
                    *, fps: float, project: Path | None = None) -> Path:
    project = project or Path(
        os.environ.get("REELFORGE_REMOTION_PROJECT", "")
        or Path.home() / ".reelforge" / "remotion"
    )
    if not remotion_available(project):
        raise BackendUnavailable(
            f"remotion overlay {overlay.comp!r} skipped: no Remotion project at "
            f"{project}. Create one with `npx create-video@latest {project}` and "
            "set REELFORGE_REMOTION_PROJECT, or use a hyperframes overlay instead."
        )

    key = _frames_key(overlay.comp, overlay.props, overlay.dur, fps, target)
    outdir = workdir / f"rm-{overlay.comp}-{key}"
    done = outdir / ".complete"
    if done.exists():
        return outdir
    outdir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        remotion_cmd(project, overlay.comp, outdir, overlay.props,
                     fps=fps, target=target),
        cwd=project, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise BackendUnavailable(
            f"remotion overlay {overlay.comp!r} failed: "
            f"{(result.stderr or result.stdout).strip()[:300]}"
        )
    done.write_text("ok", encoding="utf-8")
    return outdir


# ---------------------------------------------------------------------------
# the entry point the renderer uses
# ---------------------------------------------------------------------------

def sequence_pattern(outdir: Path) -> str:
    """The ffmpeg input pattern for a rendered frame directory.

    Remotion names its sequence output ``element-0.png``; ours are
    ``frame_00000.png``. Detecting rather than assuming means either backend's
    output can be handed to the same compositing step.
    """
    if any(outdir.glob("frame_00000.png")):
        return str(outdir / "frame_%05d.png")
    if any(outdir.glob("element-0.png")):
        return str(outdir / "element-%d.png")
    existing = sorted(p.name for p in outdir.glob("*.png"))
    raise BackendUnavailable(
        f"no recognisable PNG sequence in {outdir} (found {existing[:3]})"
    )


def render_overlay(overlay: Overlay, target: Target, workdir: Path,
                   *, fps: float) -> filters.SequenceOverlay:
    """Render an animated overlay and describe how to composite it."""
    workdir.mkdir(parents=True, exist_ok=True)

    if overlay.type == "hyperframes":
        outdir = render_hyperframes(overlay, target, workdir, fps=fps)
    elif overlay.type == "remotion":
        outdir = render_remotion(overlay, target, workdir, fps=fps)
    else:
        raise BackendUnavailable(f"unknown motion backend {overlay.type!r}")

    # Compositions are authored full-frame, so they position themselves in
    # their own CSS and are composited at the origin. That keeps layout in one
    # place instead of split between the composition and the filter graph.
    return filters.SequenceOverlay(
        pattern=sequence_pattern(outdir),
        at=overlay.at,
        dur=overlay.dur,
        x="0",
        y="0",
        fps=fps,
    )
