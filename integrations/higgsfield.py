"""Higgsfield AI API client for image-to-video generation.

Uses the Higgsfield Cloud API to generate walkthrough-style tour videos
from listing photos. Each photo is animated into a short video clip
with camera motion, then clips are concatenated into a full tour.

API reference: https://cloud.higgsfield.ai/
SDK: https://github.com/higgsfield-ai/higgsfield-client
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

HIGGSFIELD_API_BASE = "https://cloud.higgsfield.ai/api/v1"

# Camera motion presets for realistic walkthrough feel
WALKTHROUGH_MOTIONS = [
    {"type": "push_in", "description": "Slow push-in toward the subject"},
    {"type": "pan_right", "description": "Gentle pan right to reveal the space"},
    {"type": "pan_left", "description": "Gentle pan left to reveal the space"},
    {"type": "tilt_up", "description": "Tilt up to show ceiling/height"},
    {"type": "dolly_forward", "description": "Dolly forward into the room"},
    {"type": "orbit_right", "description": "Subtle orbit around the subject"},
    {"type": "zoom_out", "description": "Slow zoom out to reveal full space"},
    {"type": "crane_up", "description": "Crane up for elevated perspective"},
]

# Room-type prompts for better video generation
ROOM_PROMPTS = {
    "exterior": "Cinematic establishing shot of a residential property exterior, smooth camera movement, golden hour lighting, real estate showcase",
    "living": "Smooth walkthrough of a spacious living room, warm natural lighting, cinematic camera movement, real estate video tour",
    "kitchen": "Cinematic pan across a modern kitchen, revealing countertops and appliances, warm lighting, real estate showcase",
    "bedroom": "Gentle dolly into a bright bedroom, soft natural light through windows, smooth camera motion, real estate tour",
    "bathroom": "Elegant reveal of a clean bathroom, smooth camera pan, bright lighting, real estate showcase",
    "dining": "Cinematic sweep of a dining area, warm ambient lighting, smooth camera movement, real estate video",
    "backyard": "Sweeping view of the backyard and outdoor space, natural lighting, cinematic drone-style movement",
    "default": "Smooth cinematic walkthrough of a room interior, natural lighting, professional real estate video tour, steady camera movement",
}


class HiggsFieldClient:
    """Client for Higgsfield Cloud API image-to-video generation."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.higgsfield_api_key
        if not self.api_key:
            raise ValueError(
                "Higgsfield API key not configured. "
                "Set HIGGSFIELD_API_KEY in .env"
            )
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_video_from_image(
        self,
        image_path: Path | str,
        *,
        prompt: str = "",
        motion_type: str = "push_in",
        duration: int = 5,
        model: str = "standard",
    ) -> dict[str, Any]:
        """Submit an image-to-video generation request.

        Args:
            image_path: Path to the source image file.
            prompt: Text prompt describing desired camera motion/style.
            motion_type: Camera motion preset (push_in, pan_right, etc.).
            duration: Video duration in seconds (3-5).
            model: Model to use (standard, soul_cinema).

        Returns:
            Dict with request_id and status info.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Read and encode image
        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        content_type = "image/jpeg"
        if image_path.suffix == ".png":
            content_type = "image/png"
        elif image_path.suffix == ".webp":
            content_type = "image/webp"

        image_url = f"data:{content_type};base64,{image_data}"

        if not prompt:
            prompt = ROOM_PROMPTS["default"]

        payload = {
            "prompt": prompt,
            "image_url": image_url,
            "motion_type": motion_type,
            "duration": duration,
            "model": model,
            "camera_fixed": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{HIGGSFIELD_API_BASE}/generations",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()

        request_id = data.get("id") or data.get("request_id")
        logger.info("Higgsfield generation submitted: %s", request_id)
        return {"request_id": request_id, "status": data.get("status", "queued"), "raw": data}

    async def check_status(self, request_id: str) -> dict[str, Any]:
        """Check the status of a generation request."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{HIGGSFIELD_API_BASE}/generations/{request_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def wait_for_completion(
        self,
        request_id: str,
        *,
        poll_interval: float = 5.0,
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Poll until generation is complete or times out."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            status = await self.check_status(request_id)
            state = status.get("status", "").lower()

            if state in ("completed", "done", "succeeded"):
                logger.info("Generation %s completed", request_id)
                return status
            elif state in ("failed", "error", "cancelled"):
                raise RuntimeError(
                    f"Generation {request_id} failed: {status.get('error', state)}"
                )

            logger.debug("Generation %s status: %s", request_id, state)
            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Generation {request_id} timed out after {timeout}s")

    async def download_video(
        self,
        generation_result: dict[str, Any],
        output_path: Path | str,
    ) -> Path:
        """Download the generated video to a local file."""
        output_path = Path(output_path)
        video_url = (
            generation_result.get("video_url")
            or generation_result.get("output", {}).get("video_url")
            or generation_result.get("result", {}).get("url")
        )
        if not video_url:
            raise ValueError("No video URL in generation result")

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(video_url, follow_redirects=True)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)

        logger.info("Downloaded video to %s (%d bytes)", output_path, output_path.stat().st_size)
        return output_path

    async def generate_and_download(
        self,
        image_path: Path | str,
        output_path: Path | str,
        *,
        prompt: str = "",
        motion_type: str = "push_in",
        duration: int = 5,
        model: str = "standard",
    ) -> Path:
        """Generate a video from an image and download the result.

        Convenience method that submits, polls, and downloads.
        """
        result = await self.generate_video_from_image(
            image_path,
            prompt=prompt,
            motion_type=motion_type,
            duration=duration,
            model=model,
        )
        completed = await self.wait_for_completion(result["request_id"])
        return await self.download_video(completed, output_path)


def classify_room_from_index(index: int, total: int) -> str:
    """Heuristic to guess room type from photo order in a listing.

    Listings typically follow: exterior → living → kitchen → bedrooms → bathrooms → backyard.
    """
    if total <= 1:
        return "default"

    ratio = index / total

    if index == 0:
        return "exterior"
    elif ratio < 0.2:
        return "living"
    elif ratio < 0.35:
        return "kitchen"
    elif ratio < 0.55:
        return "bedroom"
    elif ratio < 0.7:
        return "bathroom"
    elif ratio < 0.85:
        return "dining"
    elif index == total - 1:
        return "backyard"
    else:
        return "default"
