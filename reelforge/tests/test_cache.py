"""Tests for the content-hash cache."""

import json
import os

import pytest

from reelforge.core.cache import Cache, content_key


def _video(path, payload: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def test_key_follows_content_not_path(tmp_path):
    """Syncthing moves and renames files constantly; the cache must not care."""
    data = os.urandom(4096)
    a = _video(tmp_path / "talk.mp4", data)
    b = _video(tmp_path / "archive" / "renamed.mp4", data)
    assert content_key(a) == content_key(b)


def test_key_changes_with_content(tmp_path):
    a = _video(tmp_path / "a.mp4", b"x" * 4096)
    b = _video(tmp_path / "b.mp4", b"y" * 4096)
    assert content_key(a) != content_key(b)


def test_truncated_download_gets_a_different_key(tmp_path):
    """A partial fetch must not reuse the complete file's transcript."""
    full = _video(tmp_path / "full.mp4", os.urandom(1 << 21))
    partial = _video(tmp_path / "partial.mp4", full.read_bytes()[: (1 << 20)])
    assert content_key(full) != content_key(partial)


def test_key_handles_file_smaller_than_sample_window(tmp_path):
    tiny = _video(tmp_path / "tiny.mp4", b"abc")
    assert len(content_key(tiny)) == 16


def test_roundtrip_json(tmp_path):
    cache = Cache(tmp_path / "cache")
    cache.write_json("k1", "probe.json", {"duration": 12.5})
    assert cache.read_json("k1", "probe.json") == {"duration": 12.5}
    assert cache.has("k1", "probe.json")


def test_missing_entry_reads_as_none(tmp_path):
    assert Cache(tmp_path).read_json("nope", "probe.json") is None


def test_corrupt_artifact_reads_as_absent(tmp_path):
    """A half-written file from an OOM kill must not be trusted as valid."""
    cache = Cache(tmp_path)
    cache.path("k1", "words.json").write_text('{"words": [{"start": 1.0')
    assert cache.read_json("k1", "words.json") is None


def test_writes_are_atomic(tmp_path):
    """No .tmp residue, and the reader never sees a partial file."""
    cache = Cache(tmp_path)
    cache.write_json("k1", "big.json", {"words": list(range(5000))})
    entries = list(cache.dir_for("k1").iterdir())
    assert [p.name for p in entries] == ["big.json"]
    assert len(json.loads(entries[0].read_text())["words"]) == 5000
