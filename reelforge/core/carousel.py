"""Instagram carousels: written by Claude, drawn by Remotion, in the account's brand.

Two ways in, from the second reference reel (docs/REFERENCE-FORMATS.md):

* **three inputs** -- the audience's problem, the context (who you are, what
  you sell), and a carousel idea that already worked for a competitor or a
  creator you follow. The idea is a *structure* to borrow, never text to copy.
* **from a reel** -- a reel that already performed for you. Its transcript is
  the idea; the carousel re-tells it slide by slide, hook to call to action.

Either way the output is a folder per carousel: ``slide-01.png`` ...
``slide-NN.png`` at 1080x1350 (Instagram's tallest feed ratio, 4:5), plus
``caption.txt`` ready to paste and ``carousel.json`` -- the decision itself,
which can be edited and re-rendered with ``--decision`` without another call.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .brand import Brand

WIDTH, HEIGHT = 1080, 1350
MIN_SLIDES, MAX_SLIDES = 5, 10

CAROUSEL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["carousels"],
    "properties": {
        "carousels": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["angle", "slides", "caption"],
                "properties": {
                    "angle": {"type": "string",
                              "description": "The one idea this carousel argues, in a line"},
                    "slides": {
                        "type": "array",
                        "minItems": MIN_SLIDES,
                        "maxItems": MAX_SLIDES,
                        "items": {
                            "type": "object",
                            "required": ["role", "headline"],
                            "properties": {
                                "role": {"type": "string", "enum": ["hook", "body", "cta"]},
                                "headline": {"type": "string",
                                             "description": "Wrap the one word that matters "
                                                            "in *asterisks* for the accent colour"},
                                "body": {"type": "string",
                                         "description": "At most ~30 words; omit on the hook"},
                                "kicker": {"type": "string",
                                           "description": "2-3 word label above the headline"},
                            },
                        },
                    },
                    "caption": {"type": "string",
                                "description": "The post caption: first line is a second hook"},
                    "hashtags": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
                },
            },
        },
    },
}


class CarouselError(ValueError):
    """A carousel that cannot be rendered. Says what is wrong."""


@dataclass
class Slide:
    role: str
    headline: str
    body: str = ""
    kicker: str = ""

    def to_props(self) -> dict:
        out: dict[str, Any] = {"role": self.role, "headline": self.headline}
        if self.body:
            out["body"] = self.body
        if self.kicker:
            out["kicker"] = self.kicker
        return out


@dataclass
class CarouselPlan:
    angle: str
    slides: list[Slide]
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)


def parse(payload: dict) -> tuple[list[CarouselPlan], list[str]]:
    """Carousels from the brain's payload, repaired where repair is safe.

    The shape rules that make a carousel work are enforced here, not trusted
    to the prompt: the first slide is the hook and the last is the call to
    action, whatever roles the model wrote.
    """
    notes: list[str] = []
    plans: list[CarouselPlan] = []
    for n, raw in enumerate(payload.get("carousels") or [], 1):
        slides = [Slide(role=str(s.get("role", "body")), headline=str(s.get("headline", "")).strip(),
                        body=str(s.get("body", "") or "").strip(),
                        kicker=str(s.get("kicker", "") or "").strip())
                  for s in raw.get("slides") or []]
        slides = [s for s in slides if s.headline]
        if len(slides) < 3:
            notes.append(f"carousel {n} dropped: only {len(slides)} usable slides")
            continue
        if len(slides) > MAX_SLIDES:
            notes.append(f"carousel {n} trimmed from {len(slides)} to {MAX_SLIDES} slides")
            slides = slides[:MAX_SLIDES - 1] + [slides[-1]]
        for s in slides:
            s.role = "body"
        slides[0].role, slides[-1].role = "hook", "cta"
        tags = [t if t.startswith("#") else f"#{t}"
                for t in (str(x).strip().replace(" ", "") for x in raw.get("hashtags") or []) if t]
        plans.append(CarouselPlan(angle=str(raw.get("angle", "")).strip(), slides=slides,
                                  caption=str(raw.get("caption", "")).strip(), hashtags=tags[:8]))
    if not plans:
        raise CarouselError("no usable carousel in the decision "
                            f"(raw: {json.dumps(payload)[:300]})")
    return plans, notes


def brief_request(*, problem: str, context: str, idea: str, variants: int,
                  keyword: str | None, offer: str | None) -> str:
    return (
        f"Write {variants} carousel{'s' if variants != 1 else ''}.\n\n"
        f"## The audience's problem\n\n{problem.strip()}\n\n"
        f"## Context\n\n{context.strip()}\n\n"
        "## A carousel idea that already worked (borrow its structure, not its words)\n\n"
        f"{idea.strip()}\n\n" + _cta_lines(keyword, offer)
    )


def reel_request(*, transcript: str, context: str, variants: int,
                 keyword: str | None, offer: str | None) -> str:
    return (
        f"Turn this reel, which already performed, into {variants} "
        f"carousel{'s' if variants != 1 else ''}. Keep the idea that made it work; "
        "re-tell it for a reader swiping, not a viewer listening.\n\n"
        + (f"## Context\n\n{context.strip()}\n\n" if context.strip() else "")
        + f"## The reel's transcript\n\n{transcript.strip()}\n\n" + _cta_lines(keyword, offer)
    )


def _cta_lines(keyword: str | None, offer: str | None) -> str:
    lines = []
    if keyword:
        lines.append(f"The last slide asks people to comment {keyword.upper()}.")
    if offer:
        lines.append(f"Commenters get: {offer.strip()}")
    return ("## Call to action\n\n" + "\n".join(lines) + "\n") if lines else ""


def caption_text(plan: CarouselPlan) -> str:
    tail = ("\n\n" + " ".join(plan.hashtags)) if plan.hashtags else ""
    return plan.caption + tail + "\n"


def slug(text: str, fallback: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40].strip("-")
    return s or fallback


def props(plan: CarouselPlan, brand: Brand, keyword: str | None) -> dict:
    return {
        "slides": [s.to_props() for s in plan.slides],
        "brand": {k: getattr(brand, k) for k in ("primary", "accent", "text", "muted",
                                                 "font", "handle", "name")},
        "keyword": (keyword or "").upper(),
        "width": WIDTH,
        "height": HEIGHT,
    }


def render_cmd(project: Path, props_path: Path, out_dir: Path, browser: Path | None) -> list[str]:
    cmd = ["npx", "--no-install", "remotion", "render", "src/index.ts", "Carousel", str(out_dir),
           f"--props={props_path}", "--sequence", "--image-format=png",
           "--overwrite", "--log=error"]
    if browser is not None:
        cmd.append(f"--browser-executable={browser}")
    return cmd


def render(plan: CarouselPlan, out_dir: Path, brand: Brand, *, keyword: str | None = None) -> list[Path]:
    """Draw one carousel to ``out_dir/slide-NN.png``. Returns the slide paths."""
    from .render import remotion_renderer as rm

    ok, why = rm.available()
    if not ok:
        raise CarouselError(f"carousels are drawn with Remotion, which is not ready: {why}")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="reelforge-carousel-") as tmp:
        tmp_path = Path(tmp)
        props_path = tmp_path / "props.json"
        props_path.write_text(json.dumps(props(plan, brand, keyword)), encoding="utf-8")
        frames = tmp_path / "frames"
        result = subprocess.run(render_cmd(rm.project_dir(), props_path, frames, rm.find_browser()),
                                cwd=rm.project_dir(), capture_output=True, text=True)
        if result.returncode != 0:
            raise CarouselError("Remotion failed to draw the slides:\n"
                                + (result.stderr or result.stdout)[-1500:])
        # Remotion names a sequence by frame number with its own padding;
        # sort by that number and rename to slide-01.png..., the order the
        # slides are uploaded in.
        rendered = sorted(frames.glob("*.png"),
                          key=lambda p: int(re.findall(r"\d+", p.stem)[-1]) if re.findall(r"\d+", p.stem) else 0)
        if len(rendered) != len(plan.slides):
            raise CarouselError(f"expected {len(plan.slides)} slides, Remotion drew {len(rendered)}")
        for old in out_dir.glob("slide-*.png"):
            old.unlink()
        paths = []
        for i, src in enumerate(rendered, 1):
            dst = out_dir / f"slide-{i:02d}.png"
            shutil.move(str(src), dst)
            paths.append(dst)
    return paths


def save(plan: CarouselPlan, out_dir: Path, keyword: str | None) -> None:
    """The decision and the caption beside the slides."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "caption.txt").write_text(caption_text(plan), encoding="utf-8")
    (out_dir / "carousel.json").write_text(json.dumps({
        "keyword": keyword or "",
        "carousels": [{"angle": plan.angle, "caption": plan.caption, "hashtags": plan.hashtags,
                       "slides": [s.to_props() for s in plan.slides]}],
    }, indent=2) + "\n", encoding="utf-8")
