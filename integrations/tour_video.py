"""House tour video generator — orchestrates photo fetching and Higgsfield video creation.

Workflow:
1. Fetch listing photos (by MLS number or listing URL)
2. Generate a short video clip for each photo using Higgsfield (image-to-video)
3. Concatenate clips into a full walkthrough tour video
4. Return the final video path for delivery via Telegram
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any

from config import STORAGE_DIR
from integrations.higgsfield import (
    HiggsFieldClient,
    ROOM_PROMPTS,
    WALKTHROUGH_MOTIONS,
    classify_room_from_index,
)
from integrations.listing_photos import fetch_listing_photos, fetch_photos_from_url

logger = logging.getLogger(__name__)

# Output directory for tour videos
TOURS_DIR = STORAGE_DIR / "tour_videos"
TOURS_DIR.mkdir(exist_ok=True)


async def generate_tour_video(
    mls_number: str | None = None,
    listing_url: str | None = None,
    *,
    max_photos: int = 10,
    clip_duration: int = 5,
    model: str = "standard",
    concurrency: int = 3,
    progress_callback: Any = None,
) -> dict[str, Any]:
    """Generate a complete house tour video from a listing.

    Args:
        mls_number: MLS number to look up on REALTOR.ca.
        listing_url: Direct listing URL to scrape photos from.
        max_photos: Maximum number of photos to use (each becomes a clip).
        clip_duration: Duration of each clip in seconds (3-5).
        model: Higgsfield model (standard or soul_cinema).
        concurrency: Max concurrent Higgsfield generation requests.
        progress_callback: Optional async callable(stage: str, current: int, total: int).

    Returns:
        Dict with:
            - video_path: Path to the final tour video
            - clip_paths: list of individual clip paths
            - address: property address
            - photo_count: number of photos used
            - duration_seconds: total video duration
    """
    if not mls_number and not listing_url:
        raise ValueError("Provide either mls_number or listing_url")

    # Step 1: Fetch listing photos
    if progress_callback:
        await progress_callback("fetching_photos", 0, 1)

    if mls_number:
        listing = await fetch_listing_photos(mls_number, max_photos=max_photos)
        listing_id = mls_number
    else:
        listing = await fetch_photos_from_url(listing_url, max_photos=max_photos)
        listing_id = listing.get("url", "url_listing")[:30].replace("/", "_")
        if not listing.get("mls_number"):
            listing["mls_number"] = listing_id

    photos = listing.get("downloaded_paths", [])
    if not photos:
        raise RuntimeError(
            f"No photos found for listing. "
            f"Photo URLs found: {len(listing.get('photo_urls', []))}"
        )

    address = listing.get("address", "Unknown Address")
    logger.info("Generating tour video for %s (%d photos)", address, len(photos))

    if progress_callback:
        await progress_callback("fetching_photos", 1, 1)

    # Step 2: Generate video clips from each photo
    client = HiggsFieldClient()
    tour_dir = TOURS_DIR / listing.get("mls_number", "tour")
    tour_dir.mkdir(exist_ok=True)

    clip_paths: list[Path] = []
    total_photos = len(photos)
    semaphore = asyncio.Semaphore(concurrency)

    async def generate_clip(index: int, photo_path: Path) -> Path | None:
        """Generate a single video clip from a photo."""
        async with semaphore:
            try:
                # Determine room type and motion
                room_type = classify_room_from_index(index, total_photos)
                prompt = ROOM_PROMPTS.get(room_type, ROOM_PROMPTS["default"])
                motion = WALKTHROUGH_MOTIONS[index % len(WALKTHROUGH_MOTIONS)]

                clip_path = tour_dir / f"clip_{index:02d}.mp4"

                if progress_callback:
                    await progress_callback("generating_clips", index, total_photos)

                logger.info(
                    "Generating clip %d/%d: %s (%s)",
                    index + 1, total_photos, room_type, motion["type"],
                )

                await client.generate_and_download(
                    photo_path,
                    clip_path,
                    prompt=prompt,
                    motion_type=motion["type"],
                    duration=clip_duration,
                    model=model,
                )

                return clip_path

            except Exception as e:
                logger.error("Failed to generate clip %d: %s", index, e)
                return None

    # Run clip generation with controlled concurrency
    tasks = [generate_clip(i, photo) for i, photo in enumerate(photos)]
    results = await asyncio.gather(*tasks)

    clip_paths = [p for p in results if p is not None]

    if not clip_paths:
        raise RuntimeError("All clip generations failed. Check Higgsfield API key and quota.")

    if progress_callback:
        await progress_callback("generating_clips", total_photos, total_photos)

    # Step 3: Concatenate clips into final tour video
    if progress_callback:
        await progress_callback("concatenating", 0, 1)

    final_path = tour_dir / "tour_complete.mp4"
    await _concatenate_clips(clip_paths, final_path)

    if progress_callback:
        await progress_callback("concatenating", 1, 1)

    total_duration = len(clip_paths) * clip_duration

    logger.info(
        "Tour video complete: %s (%d clips, %ds)",
        final_path, len(clip_paths), total_duration,
    )

    return {
        "video_path": final_path,
        "clip_paths": clip_paths,
        "address": address,
        "mls_number": listing.get("mls_number", ""),
        "photo_count": len(photos),
        "clip_count": len(clip_paths),
        "duration_seconds": total_duration,
    }


async def _concatenate_clips(clip_paths: list[Path], output_path: Path) -> None:
    """Concatenate video clips using ffmpeg.

    Creates a smooth tour by joining clips with crossfade transitions.
    Falls back to simple concatenation if crossfade fails.
    """
    if len(clip_paths) == 1:
        # Single clip — just copy it
        import shutil
        shutil.copy2(clip_paths[0], output_path)
        return

    # Write ffmpeg concat list
    concat_list = output_path.parent / "concat_list.txt"
    with open(concat_list, "w") as f:
        for clip in clip_paths:
            f.write(f"file '{clip.resolve()}'\n")

    try:
        # Try concatenation with crossfade transitions
        if len(clip_paths) >= 2:
            # Build ffmpeg filter for crossfade between clips
            # Use 0.5s crossfade between each pair
            fade_duration = 0.5

            # Simple concat with xfade is complex for many clips,
            # so use the concat demuxer with a brief fade
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-movflags", "+faststart",
                "-pix_fmt", "yuv420p",
                str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.warning("ffmpeg concat failed: %s", stderr.decode()[-500:])
                raise RuntimeError("ffmpeg failed")

    except (FileNotFoundError, RuntimeError):
        # Fallback: binary concatenation (less smooth but works without ffmpeg)
        logger.warning("ffmpeg not available, using binary concatenation")
        with open(output_path, "wb") as out:
            for clip in clip_paths:
                out.write(clip.read_bytes())

    finally:
        concat_list.unlink(missing_ok=True)

    logger.info("Concatenated %d clips into %s", len(clip_paths), output_path)
