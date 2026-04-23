"""End-to-end pipeline: Google Sheet -> per-house voiceover-edited video.

For each pending row in the Higgsfield tracking sheet this module:

    1. Downloads the house video (`video_url` column).
    2. Detects scene cuts so we can align narration to each room.
    3. Looks up a property description by address.
    4. Asks Claude for a room-aligned voiceover script.
    5. Renders each script segment with ElevenLabs TTS.
    6. Muxes the voiceover onto the video, timed to the scenes.
    7. Optionally writes status + output path back to the sheet.

Designed to be callable from a CLI (`run_voiceover_automation.py`) or a
Telegram command.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

from integrations.google_sheets import HiggsfieldSheet, HouseVideoRow
from integrations.property_lookup import PropertyInfo, lookup_property
from integrations.video_voiceover import (
    build_voiceover_track,
    detect_scenes,
    download_video,
    mux_audio_over_video,
    probe_duration,
    working_dir_for_address,
)
from integrations.voiceover import (
    ElevenLabsTTS,
    ScriptSegment,
    generate_voiceover_script,
    synthesize_segments,
)

logger = logging.getLogger(__name__)

ProgressFn = Callable[[str, HouseVideoRow, dict[str, Any]], Awaitable[None]] | None


@dataclass
class VoiceoverResult:
    row: HouseVideoRow
    property_info: PropertyInfo
    scenes: list[tuple[float, float]] = field(default_factory=list)
    script: list[ScriptSegment] = field(default_factory=list)
    final_video_path: Path | None = None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.final_video_path is not None and not self.error


async def process_row(
    row: HouseVideoRow,
    *,
    tts: ElevenLabsTTS | None = None,
    progress: ProgressFn = None,
) -> VoiceoverResult:
    """Run the full per-house pipeline. Never raises — captures errors on the
    result object so the batch runner can continue."""
    result = VoiceoverResult(row=row, property_info=PropertyInfo(address=row.address))

    async def emit(stage: str, **extra: Any) -> None:
        if progress:
            await progress(stage, row, extra)

    try:
        workdir = working_dir_for_address(row.address)
        source_video = workdir / "source.mp4"
        voiceover_track = workdir / "voiceover.m4a"
        final_video = workdir / "final.mp4"
        tts_dir = workdir / "tts"

        await emit("download")
        await download_video(row.video_url, source_video)

        await emit("detect_scenes")
        scenes = await detect_scenes(source_video)
        result.scenes = [(s.start_seconds, s.duration_seconds) for s in scenes]

        await emit("lookup_property")
        result.property_info = await lookup_property(row.address)

        await emit("generate_script", scene_count=len(scenes))
        segments = await generate_voiceover_script(result.property_info, result.scenes)
        result.script = segments

        await emit("synthesize_tts", segment_count=len(segments))
        await synthesize_segments(segments, tts_dir, tts=tts)

        await emit("mix_voiceover")
        total_duration = await probe_duration(source_video)
        await build_voiceover_track(segments, total_duration, voiceover_track)

        await emit("mux_video")
        await mux_audio_over_video(source_video, voiceover_track, final_video)

        result.final_video_path = final_video
        await emit("done", final_path=str(final_video))
    except Exception as exc:
        logger.exception("Pipeline failed for row %d (%r)", row.row_number, row.address)
        result.error = f"{type(exc).__name__}: {exc}"
        await emit("error", error=result.error)

    return result


async def run_sheet_automation(
    *,
    only_pending: bool = True,
    limit: int | None = None,
    concurrency: int = 1,
    write_back: bool = True,
    progress: ProgressFn = None,
) -> list[VoiceoverResult]:
    """Process every pending row in the Higgsfield sheet."""
    sheet = HiggsfieldSheet()
    rows = await sheet.fetch_rows(only_pending=only_pending)
    if limit is not None:
        rows = rows[:limit]

    if not rows:
        logger.info("No pending rows in the Higgsfield sheet.")
        return []

    logger.info("Processing %d row(s) with concurrency=%d", len(rows), concurrency)

    # Single TTS client shared across rows (API key only loaded once)
    tts = ElevenLabsTTS()

    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def run_one(row: HouseVideoRow) -> VoiceoverResult:
        async with semaphore:
            if write_back:
                try:
                    await sheet.update_row(row, status="processing")
                except Exception as exc:
                    logger.warning("Could not mark row %d processing: %s", row.row_number, exc)
            result = await process_row(row, tts=tts, progress=progress)
            if write_back:
                try:
                    if result.ok and result.final_video_path is not None:
                        await sheet.update_row(
                            row,
                            status="done",
                            final_video_url=str(result.final_video_path),
                        )
                    else:
                        await sheet.update_row(row, status=f"error: {result.error}"[:200])
                except Exception as exc:
                    logger.warning("Could not update row %d: %s", row.row_number, exc)
            return result

    return await asyncio.gather(*(run_one(r) for r in rows))
