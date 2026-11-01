"""The account's look: colours, handle, fonts -- shared by posts and carousels.

Lives at ``~/reelforge/memory/brand.json`` so it sits beside the playbook and
style profile, and every surface (a reel's end card, a carousel's slides)
reads the same values. Nothing here invents an identity: the handle stays
empty until the user sets it, and an empty handle is simply not drawn.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

BRAND_FILE = "brand.json"


@dataclass
class Brand:
    name: str = ""
    handle: str = ""                 # "@you" -- drawn on end cards and slides when set
    primary: str = "#0A2540"         # deep navy: slide backgrounds
    accent: str = "#FF6B2C"          # orange: keywords, highlights, CTAs
    text: str = "#FFFFFF"
    muted: str = "#C9D3E0"
    font: str = 'Inter, "DejaVu Sans", "Noto Sans", system-ui, sans-serif'

    def to_dict(self) -> dict:
        return asdict(self)


def load(memory: Path | None) -> Brand:
    """The saved brand, or the defaults. Unknown keys are ignored, not fatal."""
    if memory is None:
        return Brand()
    path = Path(memory) / BRAND_FILE
    if not path.exists():
        return Brand()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Brand()
    known = {f.name for f in fields(Brand)}
    return Brand(**{k: str(v) for k, v in data.items() if k in known and v is not None})


def save(brand: Brand, memory: Path) -> Path:
    memory.mkdir(parents=True, exist_ok=True)
    path = memory / BRAND_FILE
    path.write_text(json.dumps(brand.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path
