"""Disk retention for ReelForge.

Video fills disks. A Hetzner box that runs out of space mid-render fails in
confusing ways, so retention is a first-class scheduled job rather than
something you remember to do.

Three rules, in priority order:

1. **Sources are never deleted.** Not by age, not under pressure. If you are out
   of space, that is a decision for you to make, not a script.
2. **``memory/`` is never deleted.** It is kilobytes and it is the only thing
   here that cannot be regenerated.
3. Everything else -- renders and the analysis cache -- is derived, and expires.

Renders expire by age. The cache expires by least-recently-used above a ceiling,
because a cache entry for a video you are actively working on is worth far more
than one from six weeks ago regardless of size.

    python3 server/retention.py --dry-run     # report only, change nothing
    python3 server/retention.py               # apply the policy
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

DEFAULTS = {
    "renders_days": 30,
    "cache_max_gb": 100.0,
    "min_free_gb": 20.0,
}


@dataclass
class Candidate:
    path: Path
    size_bytes: int
    age_days: float
    reason: str

    @property
    def size_gb(self) -> float:
        return self.size_bytes / 1024**3


def _dir_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path, onerror=lambda _e: None):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                continue
    return total


def _atime_days(path: Path) -> float:
    """Age in days since last access, falling back to mtime.

    Access time is the better signal for a cache -- an entry you re-planned
    yesterday should survive even if it was created months ago. Many filesystems
    mount with ``relatime``, which is coarse but adequate at day granularity.
    """
    try:
        st = path.stat()
    except OSError:
        return 0.0
    stamp = max(st.st_atime, st.st_mtime)
    return (time.time() - stamp) / 86400


def plan_renders(outbox: Path, max_age_days: int) -> list[Candidate]:
    """Rendered outputs older than the cutoff. Regenerable from their EDL."""
    if not outbox.is_dir():
        return []
    out: list[Candidate] = []
    for item in outbox.iterdir():
        # EDLs are the recipe and cost nothing to keep -- never expire them.
        if item.suffix in {".json", ".md"}:
            continue
        age = _atime_days(item)
        if age <= max_age_days:
            continue
        size = _dir_size(item) if item.is_dir() else item.stat().st_size
        out.append(Candidate(item, size, age, f"render older than {max_age_days}d"))
    return sorted(out, key=lambda c: c.age_days, reverse=True)


def plan_cache(cache: Path, max_gb: float) -> list[Candidate]:
    """Least-recently-used cache entries above the size ceiling."""
    if not cache.is_dir():
        return []
    entries = [
        Candidate(p, _dir_size(p), _atime_days(p), "cache LRU eviction")
        for p in cache.iterdir()
        if p.is_dir()
    ]
    total_gb = sum(e.size_gb for e in entries)
    if total_gb <= max_gb:
        return []

    # Evict oldest-accessed first, stopping the moment we are under the ceiling.
    entries.sort(key=lambda c: c.age_days, reverse=True)
    doomed: list[Candidate] = []
    for entry in entries:
        if total_gb <= max_gb:
            break
        doomed.append(entry)
        total_gb -= entry.size_gb
    return doomed


def free_gb(path: Path) -> float:
    try:
        return shutil.disk_usage(path).free / 1024**3
    except OSError:
        return 0.0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Apply ReelForge disk retention.")
    ap.add_argument("--root", type=Path,
                    default=Path(os.environ.get("REELFORGE_ROOT", "~/reelforge")).expanduser())
    ap.add_argument("--renders-days", type=int, default=DEFAULTS["renders_days"])
    ap.add_argument("--cache-max-gb", type=float, default=DEFAULTS["cache_max_gb"])
    ap.add_argument("--min-free-gb", type=float, default=DEFAULTS["min_free_gb"])
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be removed, change nothing")
    args = ap.parse_args(argv)

    root: Path = args.root
    if not root.is_dir():
        print(f"error: {root} does not exist", file=sys.stderr)
        return 2

    before = free_gb(root)
    doomed = plan_renders(root / "outbox", args.renders_days)
    doomed += plan_cache(root / ".cache", args.cache_max_gb)

    if not doomed:
        print(f"nothing to reclaim. {before:.1f} GB free at {root}")
    else:
        reclaim = sum(c.size_gb for c in doomed)
        verb = "would reclaim" if args.dry_run else "reclaiming"
        print(f"{verb} {reclaim:.1f} GB across {len(doomed)} items:")
        for c in doomed:
            print(f"  {c.size_gb:7.2f} GB  {c.age_days:5.0f}d  {c.reason:28}  {c.path.name}")

        if not args.dry_run:
            for c in doomed:
                try:
                    shutil.rmtree(c.path) if c.path.is_dir() else c.path.unlink()
                except OSError as exc:
                    print(f"  ! failed to remove {c.path}: {exc}", file=sys.stderr)

    after = free_gb(root)
    if not args.dry_run and doomed:
        print(f"free: {before:.1f} GB -> {after:.1f} GB")

    if after < args.min_free_gb:
        # Deliberately not deleting sources to solve this. Say so plainly.
        print(
            f"\nWARNING: {after:.1f} GB free, below the {args.min_free_gb:.0f} GB "
            "floor. Retention will not delete source footage -- move or archive "
            f"files from {root}/inbox yourself, or lower cache_max_gb.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
