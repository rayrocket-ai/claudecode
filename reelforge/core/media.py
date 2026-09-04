"""FFmpeg and FFprobe: command construction, separated from execution.

Every ffmpeg invocation in ReelForge is built by a pure function here that
returns an argument list, and executed by :func:`run`. Nothing builds a command
string inline.

That split is what makes the pipeline testable on a machine with no ffmpeg
installed -- CI asserts the *arguments*, which is where the bugs actually live.
A wrong filter graph is a bug; subprocess spawning is not.
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Audio for speech recognition. 16 kHz mono is what whisper resamples to
# internally, so doing it once here avoids doing it per-chunk later.
ASR_RATE = 16_000


class FFmpegError(RuntimeError):
    """An ffmpeg/ffprobe invocation failed, with its stderr attached."""

    def __init__(self, cmd: list[str], returncode: int, stderr: str):
        self.cmd, self.returncode, self.stderr = cmd, returncode, stderr
        # ffmpeg's real error is almost always the last line; the preceding
        # 30 lines are banner and stream metadata nobody needs in a traceback.
        tail = "\n".join(stderr.strip().splitlines()[-8:])
        super().__init__(f"{shlex.join(cmd[:3])} ... failed ({returncode}):\n{tail}")


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool
    video_codec: str
    audio_codec: str | None
    size_bytes: int

    @property
    def aspect(self) -> float:
        return self.width / self.height if self.height else 0.0

    @property
    def is_vertical(self) -> bool:
        return self.aspect < 1.0

    def as_dict(self) -> dict:
        d = self.__dict__.copy()
        d["path"] = str(self.path)
        d["aspect"] = round(self.aspect, 4)
        return d


# --------------------------------------------------------------------------
# execution
# --------------------------------------------------------------------------

def available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def run(cmd: list[str], *, timeout: float | None = None) -> str:
    """Execute a built command, raising :class:`FFmpegError` on failure."""
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise FFmpegError(cmd, proc.returncode, proc.stderr)
    return proc.stdout


# --------------------------------------------------------------------------
# command builders -- pure, and unit-tested without ffmpeg present
# --------------------------------------------------------------------------

def probe_cmd(src: Path) -> list[str]:
    return [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(src),
    ]


def extract_audio_cmd(src: Path, dst: Path) -> list[str]:
    """Mono 16 kHz PCM WAV for speech recognition."""
    return [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-i", str(src),
        "-vn",
        "-ac", "1",
        "-ar", str(ASR_RATE),
        "-c:a", "pcm_s16le",
        str(dst),
    ]


def silence_cmd(src: Path, *, noise_db: float = -32.0, min_dur: float = 0.35) -> list[str]:
    """Detect silence. Output is parsed from stderr by :func:`parse_silence`.

    -32 dB rather than ffmpeg's -60 dB default: room tone, breath and fan noise
    sit well above -60, so the default finds almost nothing in real footage.
    0.35 s is roughly the shortest gap a viewer reads as a pause rather than as
    a glitchy cut.
    """
    return [
        "ffmpeg", "-hide_banner", "-nostdin",
        "-i", str(src),
        "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}",
        "-f", "null", "-",
    ]


def scene_cmd(src: Path, *, threshold: float = 0.4) -> list[str]:
    """Detect visual cuts. Timestamps are parsed from stderr."""
    return [
        "ffmpeg", "-hide_banner", "-nostdin",
        "-i", str(src),
        "-filter:v", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-",
    ]


def loudness_curve_cmd(src: Path, *, window: float = 1.0) -> list[str]:
    """Per-window RMS, used as a proxy for emphasis, laughter and energy."""
    return [
        "ffmpeg", "-hide_banner", "-nostdin",
        "-i", str(src),
        "-af", f"astats=metadata=1:reset={window},"
               f"ametadata=print:key=lavfi.astats.Overall.RMS_level",
        "-f", "null", "-",
    ]


def loudness_cmd(src: Path) -> list[str]:
    """Integrated loudness and loudness range, EBU R128.

    Different from :func:`loudness_curve_cmd`, which gives a per-second RMS
    curve for finding *moments*. This gives one number for the whole file,
    which is what you compare against a platform target -- and what a
    reference video tells you about how hot its creator mixes.
    """
    return [
        "ffmpeg", "-hide_banner", "-nostdin",
        "-i", str(src),
        "-af", "ebur128=framelog=quiet",
        "-f", "null", "-",
    ]


def filmstrip_cmd(src: Path, dst_pattern: Path, *, every_seconds: float = 5.0,
                  width: int = 320) -> list[str]:
    """Sample frames as JPEGs.

    These are the brain's only visual input. Sampling at low resolution keeps
    both disk and, more importantly, vision tokens bounded -- dumping full
    frames from an hour of video would cost more than the rest of the pipeline
    combined and tell the model very little extra.
    """
    return [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-i", str(src),
        "-vf", f"fps=1/{every_seconds},scale={width}:-2",
        "-q:v", "6",
        str(dst_pattern),
    ]


# --------------------------------------------------------------------------
# output parsing
# --------------------------------------------------------------------------

def parse_probe(raw: str, src: Path) -> MediaInfo:
    data = json.loads(raw)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if video is None:
        raise ValueError(f"{src.name}: no video stream")

    fmt = data.get("format", {})
    # Duration can be absent on the stream but present on the container, and
    # vice versa for some MKVs. Try both before giving up.
    duration = float(video.get("duration") or fmt.get("duration") or 0.0)

    return MediaInfo(
        path=src,
        duration=duration,
        width=int(video.get("width", 0)),
        height=int(video.get("height", 0)),
        fps=_parse_fraction(video.get("avg_frame_rate") or video.get("r_frame_rate")),
        has_audio=audio is not None,
        video_codec=video.get("codec_name", "unknown"),
        audio_codec=audio.get("codec_name") if audio else None,
        size_bytes=int(fmt.get("size") or (src.stat().st_size if src.exists() else 0)),
    )


def _parse_fraction(value: str | None) -> float:
    """ffprobe reports frame rate as 'num/den'; 0/0 means unknown."""
    if not value or "/" not in value:
        try:
            return float(value) if value else 0.0
        except ValueError:
            return 0.0
    num, _, den = value.partition("/")
    try:
        d = float(den)
        return round(float(num) / d, 3) if d else 0.0
    except ValueError:
        return 0.0


def parse_silence(stderr: str) -> list[tuple[float, float]]:
    """Extract ``(start, end)`` silence spans from silencedetect output."""
    spans: list[tuple[float, float]] = []
    start: float | None = None
    for line in stderr.splitlines():
        if "silence_start:" in line:
            start = _tail_float(line, "silence_start:")
        elif "silence_end:" in line and start is not None:
            end = _tail_float(line, "silence_end:")
            if end is not None and end > start:
                spans.append((start, end))
            start = None
    return spans


def parse_scenes(stderr: str) -> list[float]:
    """Extract scene-change timestamps from showinfo output."""
    times: list[float] = []
    for line in stderr.splitlines():
        if "pts_time:" in line:
            t = _tail_float(line, "pts_time:")
            if t is not None:
                times.append(t)
    return sorted(set(times))


def parse_loudness(stderr: str) -> tuple[float | None, float | None]:
    """Extract ``(integrated LUFS, loudness range LU)`` from ebur128's summary.

    The summary block prints ``I:`` and ``LRA:`` lines once at the end; the
    per-frame ``M:`` readings that precede them are deliberately not matched.
    """
    integrated: float | None = None
    lra: float | None = None
    for line in stderr.splitlines():
        stripped = line.strip()
        if stripped.startswith("I:") and "LUFS" in stripped:
            integrated = _tail_float(stripped, "I:")
        elif stripped.startswith("LRA:") and "LU" in stripped:
            lra = _tail_float(stripped, "LRA:")
    return integrated, lra


def _tail_float(line: str, marker: str) -> float | None:
    try:
        return float(line.split(marker, 1)[1].split()[0])
    except (IndexError, ValueError):
        return None


# --------------------------------------------------------------------------
# convenience
# --------------------------------------------------------------------------

def probe(src: Path) -> MediaInfo:
    return parse_probe(run(probe_cmd(src)), src)


def run_capturing_stderr(cmd: list[str], *, timeout: float | None = None) -> str:
    """Run a command whose useful output goes to stderr (the detect filters).

    These filters exit non-zero in some ffmpeg builds despite succeeding, so
    the return code is deliberately ignored -- an empty parse is the real
    failure signal, and callers handle that.
    """
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    return proc.stderr
