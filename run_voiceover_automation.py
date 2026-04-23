"""CLI: read the Higgsfield Google Sheet and produce voiceover-edited videos.

Usage:
    # Process every pending row
    python run_voiceover_automation.py

    # One-off: process a specific address + video URL (skips the sheet)
    python run_voiceover_automation.py --address "123 Main St" --video-url https://...

    # Cap the batch and skip the sheet write-back
    python run_voiceover_automation.py --limit 3 --no-write-back

Requires the following in .env:
    ANTHROPIC_API_KEY            (voiceover script)
    ELEVENLABS_API_KEY           (TTS)
    GOOGLE_SHEETS_CSV_URL        OR GOOGLE_SHEETS_CREDENTIALS_PATH + HIGGSFIELD_SHEET_ID

And `ffmpeg` / `ffprobe` must be on PATH.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from automation.voiceover_pipeline import (
    HouseVideoRow,
    process_row,
    run_sheet_automation,
)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
        stream=sys.stdout,
    )


async def _run_single(address: str, video_url: str) -> int:
    row = HouseVideoRow(row_number=0, address=address, video_url=video_url)

    async def on_stage(stage, row, extra):
        print(f"  [{stage}] {extra}" if extra else f"  [{stage}]")

    result = await process_row(row, progress=on_stage)
    if result.ok:
        print(f"\n✅ Final video: {result.final_video_path}")
        return 0
    print(f"\n❌ Failed: {result.error}")
    return 1


async def _run_sheet(limit: int | None, concurrency: int, write_back: bool, only_pending: bool) -> int:
    async def on_stage(stage, row, extra):
        tag = f"row {row.row_number} / {row.address[:40]!r}"
        print(f"  [{stage}] {tag}" + (f" {extra}" if extra else ""))

    results = await run_sheet_automation(
        only_pending=only_pending,
        limit=limit,
        concurrency=concurrency,
        write_back=write_back,
        progress=on_stage,
    )
    ok_count = sum(1 for r in results if r.ok)
    fail_count = len(results) - ok_count
    print(f"\nProcessed {len(results)} row(s): {ok_count} ok, {fail_count} failed")
    for r in results:
        status = "✅" if r.ok else "❌"
        detail = str(r.final_video_path) if r.ok else r.error
        print(f"  {status} row {r.row.row_number} {r.row.address[:40]!r} -> {detail}")
    return 0 if fail_count == 0 else 1


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--address", help="Process a single address (requires --video-url)")
    parser.add_argument("--video-url", help="Higgsfield video URL for --address")
    parser.add_argument("--limit", type=int, help="Max sheet rows to process")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--no-write-back", dest="write_back", action="store_false")
    parser.add_argument("--all-rows", dest="only_pending", action="store_false",
                        help="Process every row (not just pending ones)")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.set_defaults(write_back=True, only_pending=True)
    args = parser.parse_args()

    _setup_logging(args.verbose)

    if args.address:
        if not args.video_url:
            parser.error("--address requires --video-url")
        return await _run_single(args.address, args.video_url)

    return await _run_sheet(args.limit, args.concurrency, args.write_back, args.only_pending)


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
