"""Scene detection, voiceover muxing, and room-aligned video editing.

All video operations go through `ffmpeg` / `ffprobe` on the host.

Pipeline:
  1. `detect_scenes(video)`           -> list[(start, duration)]
  2. voiceover.generate_voiceover_script(info, scenes) -> ScriptSegments
  3. voiceover.synthesize_segments(...)                -> mp3 per segment
  4. `build_voiceover_track(segments, total_duration)` -> single voiceover.mp3
  5. `mux_audio_over_video(video, voiceover, output)`  -> final.mp4

Step 4 pads each TTS clip with leading silence so it starts exactly when
its scene begins. This is what keeps the voice line up with the room shown.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

import httpx

from config import STORAGE_DIR, get_settings
from integrations.voiceover import ScriptSegment

logger = logging.getLogger(__name__)


@dataclass
class Scene:
    start_seconds: float
    duration_seconds: float

    @property
    def end_seconds(self) -> float:
        return self.start_seconds + self.duration_seconds


# ----------------------------------------------------------------------
# Video download
# ----------------------------------------------------------------------
async def download_video(url: str, output_path: Path) -> Path:
    """Download a video URL to disk. Supports direct http(s) mp4 links."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with output_path.open("wb") as fh:
                async for chunk in resp.aiter_bytes(chunk_size=1 << 16):
                    fh.write(chunk)
    logger.info("Downloaded video %s -> %s (%d bytes)", url, output_path, output_path.stat().st_size)
    return output_path


# ----------------------------------------------------------------------
# ffprobe / ffmpeg helpers
# ----------------------------------------------------------------------
def _require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(
            f"{name} not found on PATH. Install ffmpeg (includes ffprobe) before running the voiceover pipeline."
        )


async def _run(*args: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode or 0, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")


async def probe_duration(video_path: Path) -> float:
    _require_tool("ffprobe")
    rc, out, err = await _run(
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    )
    if rc != 0:
        raise RuntimeError(f"ffprobe failed: {err[-300:]}")
    try:
        return float(out.strip())
    except ValueError as exc:
        raise RuntimeError(f"ffprobe returned non-numeric duration: {out!r}") from exc


# ----------------------------------------------------------------------
# Scene detection
# ----------------------------------------------------------------------
async def detect_scenes(
    video_path: Path,
    *,
    threshold: float | None = None,
    min_scene_seconds: float | None = None,
) -> list[Scene]:
    """Detect scene-change timestamps with ffmpeg's `scene` filter.

    Short scenes (below `min_scene_seconds`) are merged into the preceding
    scene so narration has enough room to breathe.
    """
    _require_tool("ffmpeg")

    settings = get_settings()
    thr = settings.voiceover_scene_threshold if threshold is None else threshold
    min_len = settings.voiceover_min_scene_seconds if min_scene_seconds is None else min_scene_seconds

    duration = await probe_duration(video_path)

    rc, _, err = await _run(
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(video_path),
        "-vf", f"select='gt(scene,{thr})',showinfo",
        "-f", "null", "-",
    )
    if rc != 0:
        raise RuntimeError(f"ffmpeg scene-detect failed: {err[-300:]}")

    timestamps: list[float] = [0.0]
    for line in err.splitlines():
        if "pts_time" not in line:
            continue
        key = "pts_time:"
        idx = line.find(key)
        if idx < 0:
            continue
        tail = line[idx + len(key):].split()[0]
        try:
            ts = float(tail)
        except ValueError:
            continue
        if ts > 0 and ts < duration:
            timestamps.append(ts)

    # De-dupe + sort
    timestamps = sorted({round(t, 3) for t in timestamps})

    # Build raw scene list
    scenes: list[Scene] = []
    for i, start in enumerate(timestamps):
        end = timestamps[i + 1] if i + 1 < len(timestamps) else duration
        scenes.append(Scene(start_seconds=start, duration_seconds=max(0.0, end - start)))

    # Merge tiny scenes into the previous one
    merged: list[Scene] = []
    for scene in scenes:
        if merged and scene.duration_seconds < min_len:
            prev = merged[-1]
            merged[-1] = Scene(prev.start_seconds, prev.duration_seconds + scene.duration_seconds)
        else:
            merged.append(scene)

    # Guarantee at least one segment spanning the whole clip
    if not merged:
        merged = [Scene(0.0, duration)]

    logger.info(
        "Detected %d scenes (threshold=%.2f, min=%0.2fs) in %.2fs clip",
        len(merged), thr, min_len, duration,
    )
    return merged


# ----------------------------------------------------------------------
# Voiceover track assembly + mux
# ----------------------------------------------------------------------
async def build_voiceover_track(
    segments: list[ScriptSegment],
    total_duration: float,
    output_path: Path,
) -> Path:
    """Compose a single audio file with each segment placed at its scene start.

    Uses ffmpeg's `adelay` to push each segment to its start timestamp, then
    `amix` to combine them. Segments without an audio_path are skipped.
    """
    _require_tool("ffmpeg")

    ready = [s for s in segments if s.audio_path and s.audio_path.exists()]
    if not ready:
        raise RuntimeError("No rendered TTS segments to mix")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = ["ffmpeg", "-y", "-hide_banner", "-nostats"]
    for seg in ready:
        cmd += ["-i", str(seg.audio_path)]

    filter_parts: list[str] = []
    labels: list[str] = []
    for i, seg in enumerate(ready):
        delay_ms = max(0, int(round(seg.start_seconds * 1000)))
        label = f"a{i}"
        # stereo delay so both channels align
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[{label}]")
        labels.append(f"[{label}]")

    mix_inputs = "".join(labels)
    filter_parts.append(
        f"{mix_inputs}amix=inputs={len(ready)}:dropout_transition=0:normalize=0,"
        f"apad=whole_dur={total_duration:.3f}[out]"
    )

    cmd += [
        "-filter_complex", ";".join(filter_parts),
        "-map", "[out]",
        "-t", f"{total_duration:.3f}",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path),
    ]

    rc, _, err = await _run(*cmd)
    if rc != 0:
        raise RuntimeError(f"ffmpeg voiceover mix failed: {err[-500:]}")
    logger.info("Built voiceover track -> %s", output_path)
    return output_path


async def mux_audio_over_video(
    video_path: Path,
    voiceover_path: Path,
    output_path: Path,
    *,
    original_audio_volume: float = 0.0,
    voiceover_volume: float = 1.0,
) -> Path:
    """Overlay the voiceover onto the video, optionally ducking original audio.

    Higgsfield clips usually have no usable audio, so the default fully mutes
    the original track and uses only the voiceover.
    """
    _require_tool("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if original_audio_volume <= 0:
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-nostats",
            "-i", str(video_path),
            "-i", str(voiceover_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        # Keep (ducked) original, mix voiceover on top
        filter_complex = (
            f"[0:a]volume={original_audio_volume}[orig];"
            f"[1:a]volume={voiceover_volume}[vo];"
            f"[orig][vo]amix=inputs=2:duration=longest:dropout_transition=0[aout]"
        )
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-nostats",
            "-i", str(video_path),
            "-i", str(voiceover_path),
            "-filter_complex", filter_complex,
            "-map", "0:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]

    rc, _, err = await _run(*cmd)
    if rc != 0:
        raise RuntimeError(f"ffmpeg mux failed: {err[-500:]}")
    logger.info("Muxed voiceover onto video -> %s", output_path)
    return output_path


# ----------------------------------------------------------------------
# Output location
# ----------------------------------------------------------------------
VOICEOVER_DIR = STORAGE_DIR / "voiceover_tours"
VOICEOVER_DIR.mkdir(exist_ok=True)


def working_dir_for_address(address: str) -> Path:
    """Return a stable per-house work directory inside storage/."""
    safe = "".join(c if c.isalnum() else "_" for c in address.strip())[:80] or "tour"
    path = VOICEOVER_DIR / safe
    path.mkdir(parents=True, exist_ok=True)
    return path
