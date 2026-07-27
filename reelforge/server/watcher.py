"""Inbox watcher: pre-warm everything slow before you sit down.

This is what makes a server worth more than a laptop. The moment footage lands
in ``inbox/`` -- synced from a phone, dropped by rsync, or fetched from a link
file -- this runs the expensive deterministic half unattended: probe, extract
audio, transcribe, analyse. By the time you attach to the session, planning is
instant.

It deliberately makes **no editorial decisions**. Cutting is a conversation; the
watcher only ever prepares the ingredients.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from reelforge.core import analyze, fetch, hardware, media  # noqa: E402
from reelforge.core.cache import Cache, content_key  # noqa: E402
from reelforge.core.transcribe import transcribe  # noqa: E402

log = logging.getLogger("reelforge.watch")

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
LINKS_DIR = "_links"


class Watcher:
    def __init__(self, root: Path, *, settle: float = 30.0, poll: float = 15.0):
        self.root = root
        self.inbox = root / "inbox"
        self.links = self.inbox / LINKS_DIR
        self.cache = Cache(root / ".cache")
        self.settle = settle
        self.poll = poll
        self.profile = hardware.profile(root)
        self._stop = False
        self._sizes: dict[Path, tuple[int, float]] = {}

    # -- lifecycle ---------------------------------------------------------

    def stop(self, *_args) -> None:
        log.info("stop requested; finishing current file")
        self._stop = True

    def run(self) -> int:
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.links.mkdir(parents=True, exist_ok=True)

        if not media.available():
            log.error("ffmpeg/ffprobe not found -- run scripts/install.sh")
            return 1

        log.info(
            "watching %s | %s on %s (%d workers), %d render lanes",
            self.inbox, self.profile.whisper_model, self.profile.whisper_device,
            self.profile.transcribe_workers, self.profile.render_parallelism,
        )

        while not self._stop:
            try:
                self.tick()
            except Exception:
                # A single unreadable file must never take the service down --
                # systemd would restart it into the same file forever.
                log.exception("tick failed; continuing")
            for _ in range(int(self.poll)):
                if self._stop:
                    break
                time.sleep(1)
        return 0

    def tick(self) -> None:
        for link_file in sorted(self.links.glob("*.txt")):
            self.resolve_links(link_file)
        for video in sorted(self.inbox.iterdir()):
            if self._stop:
                return
            if video.is_file() and video.suffix.lower() in VIDEO_EXT:
                if self.settled(video):
                    self.prewarm(video)

    # -- helpers -----------------------------------------------------------

    def settled(self, path: Path) -> bool:
        """True once a file has stopped growing.

        Syncthing writes large files in chunks over minutes, and ffprobe on a
        half-synced file reports a plausible but wrong duration -- which would
        be cached and believed. Waiting for a stable size is cheaper than
        detecting the corruption later.
        """
        try:
            size = path.stat().st_size
        except OSError:
            return False
        now = time.time()
        previous = self._sizes.get(path)
        if previous is None or previous[0] != size:
            self._sizes[path] = (size, now)
            return False
        return now - previous[1] >= self.settle

    def resolve_links(self, link_file: Path) -> None:
        """Download every URL in a dropped link file, then retire the file."""
        urls = fetch.parse_link_file(link_file.read_text())
        if not urls:
            return
        log.info("%s: %d link(s)", link_file.name, len(urls))

        done, failed = [], []
        for url in urls:
            try:
                path = fetch.fetch(url, self.inbox)
                log.info("fetched %s -> %s", url, path.name)
                done.append(url)
            except Exception as exc:
                log.error("fetch failed for %s: %s", url, exc)
                reason = "\n".join(f"#   {line}" for line in str(exc).splitlines())
                failed.append(f"{url}\n{reason}")

        # Rewrite rather than delete: a failed link stays visible with its
        # reason attached, so you can fix it from your phone instead of
        # discovering the silence three days later.
        if failed:
            link_file.write_text(
                "# ReelForge could not fetch these. Fix or delete this file.\n"
                + "\n".join(failed) + "\n"
            )
        else:
            link_file.rename(link_file.with_suffix(".txt.done"))

    def prewarm(self, video: Path) -> None:
        key = content_key(video)
        if self.cache.has(key, "signals.json") and self.cache.has(key, "words.json"):
            self.cache.touch(key)
            return

        log.info("pre-warming %s", video.name)
        started = time.time()

        try:
            info = media.probe(video)
        except Exception as exc:
            log.error("%s: unreadable (%s)", video.name, exc)
            return
        self.cache.write_json(key, "probe.json", info.as_dict())

        if not self.cache.has(key, "words.json"):
            if not info.has_audio:
                # Screen recordings and b-roll legitimately have no audio.
                log.info("%s: no audio track, skipping transcription", video.name)
                self.cache.write_json(key, "words.json", {
                    "language": "", "duration": info.duration,
                    "model": "none", "words": [],
                })
            else:
                self.transcribe_to_cache(video, key, info)

        if not self.cache.has(key, "signals.json"):
            analyze.analyze(video, self.cache, key)

        log.info(
            "%s ready in %.0fs (%.1fx realtime)",
            video.name, time.time() - started,
            info.duration / max(1e-6, time.time() - started),
        )

    def transcribe_to_cache(self, video: Path, key: str, info) -> None:
        audio = self.cache.path(key, "audio.wav")
        if not audio.exists():
            media.run(media.extract_audio_cmd(video, audio))

        result = transcribe(
            audio,
            model=self.profile.whisper_model,
            device=self.profile.whisper_device,
            compute_type=self.profile.whisper_compute,
            workers=self.profile.transcribe_workers,
        )
        self.cache.write_json(key, "words.json", result.as_dict())

        # The WAV is ~2 MB/minute and is only needed again if we re-transcribe
        # with a different model. Keeping it would dominate the cache.
        audio.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ReelForge inbox watcher")
    ap.add_argument("--root", type=Path,
                    default=Path(os.environ.get("REELFORGE_ROOT", "~/reelforge")).expanduser())
    ap.add_argument("--config", type=Path, help="config.toml (reserved)")
    ap.add_argument("--settle", type=float, default=30.0,
                    help="seconds a file must stop growing before processing")
    ap.add_argument("--poll", type=float, default=15.0)
    ap.add_argument("--once", action="store_true", help="one pass, then exit")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    watcher = Watcher(args.root, settle=args.settle, poll=args.poll)
    signal.signal(signal.SIGTERM, watcher.stop)
    signal.signal(signal.SIGINT, watcher.stop)

    if args.once:
        watcher.tick()
        return 0
    return watcher.run()


if __name__ == "__main__":
    raise SystemExit(main())
