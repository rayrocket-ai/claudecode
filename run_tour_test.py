"""Live end-to-end test for house tour video generation.

Run this on a machine with outbound network access to:
  - platform.higgsfield.ai (Higgsfield API)
  - api2.realtor.ca (MLS listing lookup)

Usage:
  python run_tour_test.py --mls C5840000
  python run_tour_test.py --url https://www.realtor.ca/real-estate/...
  python run_tour_test.py --image /path/to/photo.jpg  # single-image smoke test

Requires HIGGSFIELD_API_KEY and HIGGSFIELD_API_SECRET in .env.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


async def test_connection() -> bool:
    """Probe the Higgsfield API to confirm credentials work."""
    from integrations.higgsfield import test_connection as probe
    print("\n[1/3] Testing Higgsfield API credentials...")
    result = await probe()
    if result.get("ok"):
        print(f"  ✅ {result.get('note', 'Credentials accepted')}")
        return True
    print(f"  ❌ {result.get('error')}")
    return False


async def test_single_image(image_path: Path) -> bool:
    """Generate a single 5s video clip from a local image — fastest smoke test."""
    from integrations.higgsfield import HiggsFieldClient, ROOM_PROMPTS
    print(f"\n[2/3] Generating single-image video from {image_path}...")

    client = HiggsFieldClient()
    output = Path("storage/test_single_clip.mp4")
    output.parent.mkdir(exist_ok=True)

    try:
        await client.generate_and_download(
            image_path,
            output,
            prompt=ROOM_PROMPTS["living"],
            motion_type="push_in",
            duration=5,
        )
        print(f"  ✅ Video saved to {output} ({output.stat().st_size:,} bytes)")
        return True
    except Exception as e:
        print(f"  ❌ Generation failed: {type(e).__name__}: {e}")
        return False


async def test_full_tour(mls: str | None, url: str | None) -> bool:
    """Full end-to-end: fetch photos, generate clips, concatenate."""
    from integrations.tour_video import generate_tour_video

    print(f"\n[3/3] Full tour video for {mls or url}...")

    async def progress(stage, current, total):
        print(f"  [{stage}] {current}/{total}")

    try:
        result = await generate_tour_video(
            mls_number=mls,
            listing_url=url,
            max_photos=5,  # start small
            clip_duration=5,
            progress_callback=progress,
        )
        print(f"\n  ✅ Tour video: {result['video_path']}")
        print(f"     Address: {result['address']}")
        print(f"     Clips: {result['clip_count']}, Duration: {result['duration_seconds']}s")
        return True
    except Exception as e:
        print(f"  ❌ Full tour failed: {type(e).__name__}: {e}")
        return False


async def main() -> int:
    parser = argparse.ArgumentParser(description="Test house tour video generation")
    parser.add_argument("--mls", help="MLS number to fetch from REALTOR.ca")
    parser.add_argument("--url", help="REALTOR.ca listing URL")
    parser.add_argument("--image", help="Local image for single-clip smoke test")
    parser.add_argument("--skip-auth", action="store_true", help="Skip auth probe")
    args = parser.parse_args()

    if not args.skip_auth:
        if not await test_connection():
            print("\nAborting — credentials not accepted. Check .env and try again.")
            return 1

    if args.image:
        image = Path(args.image)
        if not image.exists():
            print(f"Image not found: {image}")
            return 1
        ok = await test_single_image(image)
        return 0 if ok else 1

    if args.mls or args.url:
        ok = await test_full_tour(args.mls, args.url)
        return 0 if ok else 1

    print("\nNo test target given. Pass --mls, --url, or --image.")
    print("Example: python run_tour_test.py --image sample.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
