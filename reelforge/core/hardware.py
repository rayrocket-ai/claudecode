"""Hardware detection and derived encode/transcribe settings.

ReelForge is built to run on a CPU-only Hetzner box but must not have that
assumption welded into it -- moving to a GPU machine later should change speed,
not code. Every performance-sensitive choice in the pipeline reads its settings
from :func:`profile` rather than hardcoding a model size or an encoder.

Stdlib only, on purpose: this module is imported by ``/reel-doctor`` before any
dependencies are installed, so it has to work on a bare box.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Whisper model choices, cheapest first. distil-large-v3 is the sweet spot on
# CPU: near large-v3 accuracy at roughly 4x the speed, which is what makes
# unattended pre-warming of hour-long sources practical on a dedicated box.
_CPU_MODEL_BY_RAM_GB = [
    (3, "base.en"),
    (6, "small.en"),
    (10, "distil-large-v3"),
]
_CPU_MODEL_DEFAULT = "distil-large-v3"


@dataclass
class Profile:
    """Everything the pipeline needs to know about the machine it is on."""

    cores: int
    ram_gb: float
    disk_free_gb: float
    gpu: str | None
    ffmpeg: str | None
    ffprobe: bool
    node: str | None
    python: str

    # Derived settings -- read these, not the raw fields above.
    whisper_model: str = ""
    whisper_compute: str = ""
    whisper_device: str = ""
    transcribe_workers: int = 1
    render_parallelism: int = 1
    encoder: str = ""
    draft_args: list[str] = field(default_factory=list)
    final_args: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _run(cmd: list[str]) -> str | None:
    """Run a command, returning stdout or None if it is missing or fails."""
    if shutil.which(cmd[0]) is None:
        return None
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def _cores() -> int:
    """Physical-ish core count.

    ``os.cpu_count`` reports hyperthreads. For x264 and whisper alike, threads
    past the physical core count buy very little and cost memory bandwidth, so
    we prefer the cgroup/affinity-aware count and fall back conservatively.
    """
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:  # not Linux
        return max(1, os.cpu_count() or 1)


def _ram_gb() -> float:
    try:
        meminfo = Path("/proc/meminfo").read_text()
        kb = int(re.search(r"MemTotal:\s+(\d+) kB", meminfo).group(1))
        return round(kb / 1024 / 1024, 1)
    except (OSError, AttributeError, ValueError):
        pass
    try:
        return round(
            os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3, 1
        )
    except (ValueError, OSError, AttributeError):
        return 0.0


def _disk_free_gb(path: Path) -> float:
    try:
        return round(shutil.disk_usage(path).free / 1024**3, 1)
    except OSError:
        return 0.0


def _gpu() -> str | None:
    out = _run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
    if not out:
        return None
    name = out.strip().splitlines()[0].strip()
    return name or None


def _apple_silicon() -> bool:
    """Whether this is an Apple Silicon Mac.

    Worth detecting separately from ``_gpu``: there is no CUDA here, so the
    transcription path stays on CPU, but there *is* a dedicated media engine
    that encodes H.264 far faster than any software encoder. Treating a Mac as
    a plain CPU box leaves most of the machine unused.
    """
    import platform

    return platform.system() == "Darwin" and platform.machine() == "arm64"


def _ffmpeg_version() -> str | None:
    out = _run(["ffmpeg", "-version"])
    if not out:
        return None
    match = re.search(r"ffmpeg version (\S+)", out)
    return match.group(1) if match else "unknown"


def _has_encoder(name: str) -> bool:
    out = _run(["ffmpeg", "-hide_banner", "-encoders"])
    return bool(out and re.search(rf"\b{re.escape(name)}\b", out))


def profile(workdir: Path | None = None) -> Profile:
    """Detect the machine and derive pipeline settings from it."""
    import platform

    workdir = workdir or Path.cwd()
    cores = _cores()
    ram = _ram_gb()
    gpu = _gpu()
    apple = _apple_silicon()

    p = Profile(
        cores=cores,
        ram_gb=ram,
        disk_free_gb=_disk_free_gb(workdir),
        gpu=gpu,
        ffmpeg=_ffmpeg_version(),
        ffprobe=shutil.which("ffprobe") is not None,
        node=(_run(["node", "--version"]) or "").strip() or None,
        python=platform.python_version(),
    )

    # --- transcription -----------------------------------------------------
    if gpu:
        p.whisper_device = "cuda"
        p.whisper_compute = "float16"
        p.whisper_model = "large-v3"
        p.transcribe_workers = 1  # GPU is the bottleneck; parallelism hurts
    else:
        p.whisper_device = "cpu"
        p.whisper_compute = "int8"
        p.whisper_model = _CPU_MODEL_DEFAULT
        for ceiling, model in _CPU_MODEL_BY_RAM_GB:
            if ram and ram < ceiling:
                p.whisper_model = model
                break
        # Each worker holds its own model copy. Cap by RAM as well as cores so
        # a 4-core/8GB CX box does not OOM halfway through an hour of audio.
        by_ram = int(ram // 4) if ram else 1
        p.transcribe_workers = max(1, min(cores, by_ram or 1, 8))

        if apple:
            # CTranslate2 has no Metal backend, so transcription stays on the
            # CPU -- but an Apple Silicon core is several times a cloud vCPU,
            # and the memory is unified, so the RAM ladder above is too timid
            # here. One step up is comfortably real-time.
            p.whisper_model = _CPU_MODEL_DEFAULT if ram >= 16 else p.whisper_model

    # --- rendering ---------------------------------------------------------
    # Segments render in parallel then concat: the single biggest CPU win.
    # Leave a core free so the box stays responsive for everything else on it.
    p.render_parallelism = max(1, min(cores - 1, 12)) if cores > 2 else 1

    if gpu and _has_encoder("h264_nvenc"):
        p.encoder = "h264_nvenc"
        p.draft_args = ["-c:v", "h264_nvenc", "-preset", "p1", "-cq", "28"]
        p.final_args = ["-c:v", "h264_nvenc", "-preset", "p6", "-cq", "19"]
    elif apple and _has_encoder("h264_videotoolbox"):
        # The media engine is quality-limited rather than CRF-driven, so these
        # are bitrates. They are generous on purpose: VideoToolbox is fast
        # enough that spending bits is free, and a vertical 1080x1920 reel is
        # detail-dense in a way a 16:9 frame of the same height is not.
        p.encoder = "h264_videotoolbox"
        p.draft_args = ["-c:v", "h264_videotoolbox", "-b:v", "5M", "-realtime", "1"]
        p.final_args = ["-c:v", "h264_videotoolbox", "-b:v", "12M"]
        # Hardware encoding is a fixed-function block: running many segments
        # through it at once queues on the same silicon rather than going
        # faster, and it starves the machine of memory bandwidth.
        p.render_parallelism = max(1, min(p.render_parallelism, 4))
    else:
        p.encoder = "libx264"
        threads = str(max(1, cores // max(1, p.render_parallelism)))
        p.draft_args = [
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-threads", threads,
        ]
        p.final_args = [
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-threads", threads,
        ]

    return p


# Problems that make the pipeline fail outright, vs. ones that only degrade it.
def check(p: Profile, *, min_disk_gb: float = 20.0) -> tuple[list[str], list[str]]:
    """Return ``(blockers, warnings)`` for a detected profile."""
    blockers: list[str] = []
    warnings: list[str] = []

    if not p.ffmpeg:
        blockers.append("ffmpeg not found -- run scripts/install.sh")
    elif p.ffmpeg != "unknown":
        major = re.match(r"(\d+)", p.ffmpeg)
        if major and int(major.group(1)) < 6:
            warnings.append(
                f"ffmpeg {p.ffmpeg} is older than 6.x; xfade and zoompan "
                "behaviour differs. 6+ recommended."
            )
    if not p.ffprobe:
        blockers.append("ffprobe not found (usually ships with ffmpeg)")

    if p.disk_free_gb < min_disk_gb:
        blockers.append(
            f"only {p.disk_free_gb} GB free; video work needs headroom. "
            "Run retention.py --prune or free space."
        )
    elif p.disk_free_gb < min_disk_gb * 3:
        warnings.append(f"{p.disk_free_gb} GB free -- watch disk during long renders")

    if not p.node:
        warnings.append("node not found -- Remotion premium overlays unavailable")

    if p.cores < 4:
        warnings.append(
            f"{p.cores} cores: transcription and rendering will be slow. "
            "Expect roughly real-time rather than 5-15x."
        )
    if p.ram_gb and p.ram_gb < 4:
        warnings.append(
            f"{p.ram_gb} GB RAM -- falling back to {p.whisper_model}; "
            "word timings will be less precise."
        )

    return blockers, warnings


if __name__ == "__main__":  # `python3 core/hardware.py` prints the profile
    prof = profile()
    blockers, warnings = check(prof)
    print(json.dumps(
        {"profile": prof.as_dict(), "blockers": blockers, "warnings": warnings},
        indent=2,
    ))
