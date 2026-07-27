"""Content-hash keyed cache for derived data.

Transcribing an hour of video is expensive; doing it twice is inexcusable. Every
derived artifact -- probe output, extracted audio, transcript, analysis signals,
filmstrips -- is keyed by a hash of the *source content*, not its path.

That distinction matters more than it looks. Files get renamed, moved between
inbox and an archive folder, and re-synced by Syncthing with fresh mtimes. A
path- or mtime-keyed cache misses on all of those and silently re-transcribes.
A content-keyed one does not.

Hashing a 4 GB file in full would itself be slow, so we sample: size plus three
fixed windows. Two distinct videos colliding on all four would require deliberate
effort, and the failure mode of a collision is a wrong transcript rather than
data loss.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_SAMPLE_BYTES = 1 << 20  # 1 MiB per window


def content_key(path: Path) -> str:
    """Stable 16-hex-char key for a media file's contents."""
    size = path.stat().st_size
    h = hashlib.blake2b(digest_size=8)
    h.update(str(size).encode())

    with path.open("rb") as fh:
        # Head catches container/codec differences, middle catches genuinely
        # different content at the same size, tail catches truncated downloads --
        # which is the realistic failure mode when a fetch is interrupted.
        for offset in (0, max(0, size // 2 - _SAMPLE_BYTES // 2), max(0, size - _SAMPLE_BYTES)):
            fh.seek(offset)
            h.update(fh.read(_SAMPLE_BYTES))
    return h.hexdigest()


class Cache:
    """A directory of per-source artifact folders."""

    def __init__(self, root: Path):
        self.root = Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)

    def dir_for(self, key: str) -> Path:
        d = self.root / key
        d.mkdir(parents=True, exist_ok=True)
        return d

    def path(self, key: str, name: str) -> Path:
        return self.dir_for(key) / name

    def has(self, key: str, name: str) -> bool:
        p = self.path(key, name)
        return p.exists() and p.stat().st_size > 0

    def touch(self, key: str) -> None:
        """Mark an entry as recently used, so LRU retention spares it.

        Reading a cached artifact updates its atime naturally, but planning
        sessions often only read *some* files in an entry. Touching the
        directory keeps the whole entry alive as one unit.
        """
        try:
            os.utime(self.root / key, None)
        except OSError:
            pass

    def read_json(self, key: str, name: str) -> Any | None:
        p = self.path(key, name)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            # A half-written artifact from an interrupted run is worse than
            # none: it would be trusted. Treat unreadable as absent.
            return None
        self.touch(key)
        return data

    def write_json(self, key: str, name: str, payload: Any) -> Path:
        p = self.path(key, name)
        self._atomic_write(p, json.dumps(payload, indent=2).encode())
        return p

    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
        """Write via a temp file and rename.

        The watcher can be killed mid-transcription by a reboot or an OOM. A
        partial JSON file that parses is the nightmare case -- rename is atomic
        on the same filesystem, so a reader sees either the old file or the
        complete new one.
        """
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
