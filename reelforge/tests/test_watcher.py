"""Tests for watcher behaviour that does not need ffmpeg."""

import time

import pytest

from reelforge.server.watcher import Watcher


@pytest.fixture
def watcher(tmp_path):
    w = Watcher(tmp_path, settle=0.2, poll=1)
    w.inbox.mkdir(parents=True, exist_ok=True)
    w.links.mkdir(parents=True, exist_ok=True)
    return w


# --------------------------------------------------------------------------
# settling -- the guard against processing a half-synced file
# --------------------------------------------------------------------------

def test_growing_file_is_not_processed(watcher):
    """Syncthing writes in chunks; ffprobe on a partial file lies plausibly."""
    video = watcher.inbox / "a.mp4"
    video.write_bytes(b"x" * 100)
    assert watcher.settled(video) is False

    video.write_bytes(b"x" * 200)          # still growing
    assert watcher.settled(video) is False


def test_stable_file_settles_after_the_window(watcher):
    video = watcher.inbox / "a.mp4"
    video.write_bytes(b"x" * 100)
    watcher.settled(video)                  # first observation
    time.sleep(0.25)
    assert watcher.settled(video) is True


def test_vanished_file_does_not_raise(watcher):
    """Syncthing can move a file out from under us mid-scan."""
    assert watcher.settled(watcher.inbox / "gone.mp4") is False


# --------------------------------------------------------------------------
# link resolution
# --------------------------------------------------------------------------

def test_failed_links_stay_visible_with_their_reason(watcher, monkeypatch):
    """Silent failure means finding out three days later. Rewrite in place."""
    link_file = watcher.links / "batch.txt"
    link_file.write_text("https://youtu.be/aaa\n")

    def boom(*_a, **_k):
        raise RuntimeError("yt-dlp not installed")

    monkeypatch.setattr("reelforge.server.watcher.fetch.fetch", boom)
    watcher.resolve_links(link_file)

    assert link_file.exists(), "failed link file must not be retired"
    body = link_file.read_text()
    assert "https://youtu.be/aaa" in body
    assert "yt-dlp not installed" in body


def test_rewritten_failure_file_still_parses_as_links(watcher, monkeypatch):
    """The error annotations must be comments, or the retry re-reads garbage."""
    from reelforge.core import fetch as fetch_mod

    link_file = watcher.links / "batch.txt"
    link_file.write_text("https://youtu.be/aaa\n")
    monkeypatch.setattr("reelforge.server.watcher.fetch.fetch",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("nope")))
    watcher.resolve_links(link_file)

    assert fetch_mod.parse_link_file(link_file.read_text()) == ["https://youtu.be/aaa"]


def test_fully_fetched_link_file_is_retired(watcher, monkeypatch):
    link_file = watcher.links / "batch.txt"
    link_file.write_text("https://youtu.be/aaa\n")

    fetched = watcher.inbox / "aaa.mp4"
    fetched.write_bytes(b"x")
    monkeypatch.setattr("reelforge.server.watcher.fetch.fetch", lambda *a, **k: fetched)

    watcher.resolve_links(link_file)
    assert not link_file.exists()
    assert (watcher.links / "batch.txt.done").exists()


def test_empty_link_file_is_left_alone(watcher):
    link_file = watcher.links / "notes.txt"
    link_file.write_text("# nothing here yet\n")
    watcher.resolve_links(link_file)
    assert link_file.exists()


# --------------------------------------------------------------------------
# scanning
# --------------------------------------------------------------------------

def test_non_video_files_are_ignored(watcher, monkeypatch):
    (watcher.inbox / "notes.md").write_text("hello")
    (watcher.inbox / "thumb.jpg").write_bytes(b"x")

    seen = []
    monkeypatch.setattr(Watcher, "prewarm", lambda self, p: seen.append(p))
    monkeypatch.setattr(Watcher, "settled", lambda self, p: True)
    watcher.tick()
    assert seen == []


def test_links_directory_is_not_treated_as_a_video(watcher, monkeypatch):
    monkeypatch.setattr(Watcher, "settled", lambda self, p: True)
    seen = []
    monkeypatch.setattr(Watcher, "prewarm", lambda self, p: seen.append(p))
    watcher.tick()
    assert seen == []
