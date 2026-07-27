"""Resolve links into local files in the inbox.

The inbox is the single source of truth, and this module is one of the three
doors into it (the others being Syncthing and a direct drop). A link is a link:
you should be able to paste a YouTube URL, a Drive share, a presigned S3 URL or
a Zoom recording reference into the same place and have it land as a file.

Backends are chosen by inspecting the URL, and each is optional -- a missing
``rclone`` disables Drive without affecting YouTube. Anything unrecognised
falls through to a plain HTTPS download, which covers CDN links and direct
``.mp4`` URLs.

Link files live in ``inbox/_links/*.txt``: one URL per line, ``#`` comments
allowed. Because that directory is itself synced, links dropped from a phone
are fetched by the server without any dashboard or API in between.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import urllib.parse
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Backend(str, Enum):
    YTDLP = "yt-dlp"
    RCLONE = "rclone"
    DIRECT = "direct"
    ZOOM = "zoom"


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Link:
    url: str
    backend: Backend
    note: str = ""


# Hosts yt-dlp handles far better than a raw download: it resolves the actual
# media URL, picks a sane format, and merges streams. Not exhaustive -- yt-dlp
# supports ~1800 sites -- but these are the ones worth routing deliberately.
_YTDLP_HOSTS = re.compile(
    r"(^|\.)(youtube\.com|youtu\.be|vimeo\.com|twitch\.tv|tiktok\.com|"
    r"instagram\.com|x\.com|twitter\.com|facebook\.com|dailymotion\.com|"
    r"rumble\.com|streamable\.com)$",
    re.I,
)
_RCLONE_HOSTS = re.compile(
    r"(^|\.)(drive\.google\.com|docs\.google\.com|dropbox\.com|onedrive\.live\.com|"
    r"1drv\.ms|sharepoint\.com)$",
    re.I,
)
_ZOOM_HOSTS = re.compile(r"(^|\.)zoom\.us$", re.I)

_DIRECT_MEDIA = re.compile(r"\.(mp4|mov|mkv|webm|m4v|avi|mts|m2ts)(\?|$)", re.I)

# `remote:path` -- an rclone remote name, which is alphanumeric with dashes and
# underscores. Deliberately strict so a stray `C:\...` or a typo'd scheme is
# rejected rather than silently treated as a Drive fetch.
_RCLONE_REMOTE = re.compile(r"^[A-Za-z0-9_-]+:[^:]*$")


def classify(url: str) -> Link:
    """Pick a backend for a URL."""
    url = url.strip()
    if not url:
        raise FetchError("empty URL")

    # rclone remotes are written `remote:path/file.mp4`. urlparse happily reads
    # `gdrive` as a scheme, so the distinguishing feature is the absent `//`.
    if "://" not in url and _RCLONE_REMOTE.match(url):
        return Link(url, Backend.RCLONE, "rclone remote path")

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise FetchError(f"unsupported scheme {parsed.scheme!r}: {url}")

    host = parsed.netloc.split("@")[-1].split(":")[0].lower()

    # A direct media URL is checked first: an .mp4 sitting on a Drive-hosted
    # CDN path should just be downloaded, not routed through rclone auth.
    if _ZOOM_HOSTS.search(host):
        return Link(url, Backend.ZOOM, "Zoom recording")
    if _RCLONE_HOSTS.search(host) and not _DIRECT_MEDIA.search(parsed.path):
        return Link(url, Backend.RCLONE, "cloud drive")
    if _YTDLP_HOSTS.search(host):
        return Link(url, Backend.YTDLP, "media site")
    if _DIRECT_MEDIA.search(parsed.path):
        return Link(url, Backend.DIRECT, "direct media URL")
    # Unknown host with no media extension: yt-dlp recognises far more sites
    # than we can enumerate, so give it the first attempt.
    return Link(url, Backend.YTDLP, "unknown host, trying yt-dlp")


def parse_link_file(text: str) -> list[str]:
    """One URL per line; blank lines and ``#`` comments ignored."""
    urls = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Links pasted from a phone arrive wrapped in markdown, in angle
        # brackets, or with a sentence's trailing punctuation attached.
        markdown = re.search(r"\]\(\s*(\S+?)\s*\)", line)
        if markdown:
            line = markdown.group(1)
        else:
            line = line.strip("<>").split()[0]
        urls.append(line.rstrip(".,;)"))
    return urls


# --------------------------------------------------------------------------
# command builders -- pure, tested without the tools installed
# --------------------------------------------------------------------------

def ytdlp_cmd(url: str, dest_dir: Path, *, cookies: Path | None = None) -> list[str]:
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--no-progress",
        # Prefer an already-muxed MP4 when one exists, so we skip a remux.
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
        "--merge-output-format", "mp4",
        # Embedded chapters and subtitles are free editorial signal -- chapter
        # marks are often exactly the topic boundaries the brain is looking for.
        "--embed-chapters",
        "--write-auto-subs", "--sub-langs", "en.*", "--write-subs",
        "--restrict-filenames",
        "-o", str(dest_dir / "%(title).80s [%(id)s].%(ext)s"),
        "--print", "after_move:filepath",
    ]
    if cookies:
        cmd += ["--cookies", str(cookies)]
    return cmd + ["--", url]


def rclone_cmd(url: str, dest_dir: Path) -> list[str]:
    """Copy from a configured rclone remote.

    Share URLs are not directly usable -- rclone works on ``remote:path``, so a
    pasted Drive link needs the remote configured once via ``rclone config``.
    :func:`rclone_target` converts what it can and raises a message that says
    what to do when it cannot.
    """
    return [
        "rclone", "copy", rclone_target(url), str(dest_dir),
        "--progress=false", "--transfers", "4", "--retries", "3",
    ]


def rclone_target(url: str) -> str:
    if "://" not in url:
        return url  # already remote:path
    file_id = re.search(r"/d/([A-Za-z0-9_-]{10,})", url) or \
        re.search(r"[?&]id=([A-Za-z0-9_-]{10,})", url)
    if file_id:
        raise FetchError(
            f"Google Drive share link detected ({file_id.group(1)}).\n"
            "rclone needs a configured remote rather than a share URL. Run "
            "`rclone config` once on the server, then drop links as "
            "`gdrive:path/to/file.mp4`, or share the file to a synced folder."
        )
    raise FetchError(f"cannot map {url} to an rclone remote")


def direct_cmd(url: str, dest: Path) -> list[str]:
    return [
        "curl", "--fail", "--location", "--silent", "--show-error",
        # Resume a partial file rather than restarting a multi-GB download.
        "--continue-at", "-",
        "--retry", "3", "--retry-delay", "2",
        "--output", str(dest), url,
    ]


def suggest_filename(url: str) -> str:
    """Derive a safe destination filename from a URL.

    Taking only the basename is what keeps a crafted path like
    ``/../../etc/passwd`` from escaping the destination directory.
    """
    path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    if path.endswith("/"):
        return "download.mp4"  # directory-style URL carries no filename
    name = re.sub(r"[^\w.\-]+", "_", Path(path).name).strip("._")
    return name or "download.mp4"


# --------------------------------------------------------------------------
# availability
# --------------------------------------------------------------------------

def backend_available(backend: Backend) -> bool:
    return shutil.which({
        Backend.YTDLP: "yt-dlp",
        Backend.RCLONE: "rclone",
        Backend.DIRECT: "curl",
        Backend.ZOOM: "rclone",  # placeholder; Zoom goes through the connector
    }[backend]) is not None


def missing_backend_hint(backend: Backend) -> str:
    return {
        Backend.YTDLP: "yt-dlp not installed: pip install yt-dlp (or apt install yt-dlp)",
        Backend.RCLONE: "rclone not installed: curl https://rclone.org/install.sh | sudo bash",
        Backend.DIRECT: "curl not installed: apt install curl",
        Backend.ZOOM: "Zoom recordings are fetched through the Zoom connector in "
                      "Claude Code, not by the watcher. Use /reel-fetch for these.",
    }[backend]


# --------------------------------------------------------------------------
# execution
# --------------------------------------------------------------------------

def fetch(url: str, dest_dir: Path, *, cookies: Path | None = None,
          timeout: float = 3600) -> Path:
    """Fetch one URL into ``dest_dir``, returning the downloaded path."""
    link = classify(url)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not backend_available(link.backend):
        raise FetchError(missing_backend_hint(link.backend))

    if link.backend is Backend.ZOOM:
        raise FetchError(missing_backend_hint(Backend.ZOOM))

    before = set(dest_dir.iterdir())

    if link.backend is Backend.YTDLP:
        cmd = ytdlp_cmd(url, dest_dir, cookies=cookies)
    elif link.backend is Backend.RCLONE:
        cmd = rclone_cmd(url, dest_dir)
    else:
        cmd = direct_cmd(url, dest_dir / suggest_filename(url))

    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout, check=False)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).strip().splitlines()[-6:])
        raise FetchError(f"{link.backend.value} failed for {url}:\n{tail}")

    # yt-dlp prints the final path; everyone else we discover by diffing.
    if link.backend is Backend.YTDLP:
        for line in reversed(proc.stdout.strip().splitlines()):
            candidate = Path(line.strip())
            if candidate.is_file():
                return candidate

    new = [p for p in dest_dir.iterdir() if p not in before and p.is_file()]
    if not new:
        raise FetchError(f"{link.backend.value} reported success but wrote no file for {url}")
    return max(new, key=lambda p: p.stat().st_size)
