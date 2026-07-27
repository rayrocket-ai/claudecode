"""Tests for link classification and fetch command construction."""

import pytest

from reelforge.core import fetch
from reelforge.core.fetch import Backend, FetchError


@pytest.mark.parametrize("url,backend", [
    ("https://youtube.com/watch?v=abc123", Backend.YTDLP),
    ("https://youtu.be/abc123", Backend.YTDLP),
    ("https://www.vimeo.com/12345", Backend.YTDLP),
    ("https://twitch.tv/videos/999", Backend.YTDLP),
    ("https://drive.google.com/file/d/1AbCdEfGhIjK/view", Backend.RCLONE),
    ("https://www.dropbox.com/s/xyz/clip", Backend.RCLONE),
    ("https://cdn.example.com/raw/interview.mp4", Backend.DIRECT),
    ("https://example.com/a/b/take2.MOV?sig=xyz", Backend.DIRECT),
    ("https://acme.zoom.us/rec/share/abc", Backend.ZOOM),
    ("gdrive:footage/keynote.mp4", Backend.RCLONE),
])
def test_classify_routes_to_expected_backend(url, backend):
    assert fetch.classify(url).backend is backend


def test_unknown_host_falls_through_to_ytdlp():
    """yt-dlp supports ~1800 sites; guessing it beats refusing."""
    assert fetch.classify("https://obscure.tv/watch/17").backend is Backend.YTDLP


def test_direct_media_beats_drive_routing():
    """A plain .mp4 on a Google CDN path should download, not need OAuth."""
    url = "https://drive.google.com/uc/export/clip.mp4"
    assert fetch.classify(url).backend is Backend.DIRECT


def test_non_http_scheme_rejected():
    with pytest.raises(FetchError, match="unsupported scheme"):
        fetch.classify("ftp://example.com/a.mp4")


def test_empty_url_rejected():
    with pytest.raises(FetchError, match="empty URL"):
        fetch.classify("   ")


# --------------------------------------------------------------------------
# link files -- what you drop into inbox/_links/
# --------------------------------------------------------------------------

def test_parse_link_file_ignores_comments_and_blanks():
    text = """
    # monday batch
    https://youtu.be/aaa

    https://youtu.be/bbb
    """
    assert fetch.parse_link_file(text) == ["https://youtu.be/aaa", "https://youtu.be/bbb"]


def test_parse_link_file_tolerates_pasted_markdown_and_punctuation():
    """Links pasted from a phone arrive wrapped or with a trailing period."""
    text = "[keynote](https://youtu.be/ccc)\nhttps://youtu.be/ddd.\n"
    assert fetch.parse_link_file(text) == ["https://youtu.be/ccc", "https://youtu.be/ddd"]


# --------------------------------------------------------------------------
# command builders
# --------------------------------------------------------------------------

def test_ytdlp_requests_muxed_mp4_and_chapters(tmp_path):
    cmd = fetch.ytdlp_cmd("https://youtu.be/x", tmp_path)
    assert "--no-playlist" in cmd
    assert cmd[cmd.index("--merge-output-format") + 1] == "mp4"
    # Chapters often mark exactly the topic boundaries the brain looks for.
    assert "--embed-chapters" in cmd
    # `--` before the URL stops a leading-dash URL being read as a flag.
    assert cmd[-2] == "--"


def test_ytdlp_cookies_only_added_when_given(tmp_path):
    assert "--cookies" not in fetch.ytdlp_cmd("https://youtu.be/x", tmp_path)
    with_cookies = fetch.ytdlp_cmd("https://youtu.be/x", tmp_path, cookies=tmp_path / "c.txt")
    assert with_cookies[with_cookies.index("--cookies") + 1].endswith("c.txt")


def test_direct_download_resumes_rather_than_restarting(tmp_path):
    """Multi-GB downloads over hotel wifi must not restart from zero."""
    cmd = fetch.direct_cmd("https://cdn.example.com/a.mp4", tmp_path / "a.mp4")
    assert cmd[cmd.index("--continue-at") + 1] == "-"
    assert "--fail" in cmd and "--location" in cmd


def test_drive_share_link_explains_the_fix():
    """The error has to say what to do, not just that it failed."""
    with pytest.raises(FetchError, match="rclone config"):
        fetch.rclone_target("https://drive.google.com/file/d/1AbCdEfGhIjK/view")


def test_rclone_remote_path_passes_through():
    assert fetch.rclone_target("gdrive:clips/a.mp4") == "gdrive:clips/a.mp4"


@pytest.mark.parametrize("url,expected", [
    ("https://cdn.example.com/My%20Talk.mp4", "My_Talk.mp4"),
    ("https://cdn.example.com/a/b/", "download.mp4"),
    ("https://cdn.example.com/../../etc/passwd", "passwd"),
])
def test_suggest_filename_sanitises(url, expected):
    """A filename derived from a URL must not escape the destination."""
    name = fetch.suggest_filename(url)
    assert name == expected
    assert "/" not in name


def test_missing_backend_hints_are_actionable():
    for backend in Backend:
        assert len(fetch.missing_backend_hint(backend)) > 20
