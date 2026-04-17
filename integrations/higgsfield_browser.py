"""Higgsfield Playwright automation — drive the web UI for paid plan users.

Uses Playwright to log in (via saved OAuth cookies) and automate the
image-to-video creation flow at https://higgsfield.ai/create/video.

Workflow:
1. Launch browser with persistent context (saves login across sessions)
2. First run: user logs in manually (Google/Microsoft/Apple SSO) — cookies saved
3. Subsequent runs: reuse saved session cookies, no login needed
4. Upload reference image, enter prompt, submit generation
5. Poll the UI for completion and download the finished video

This is an alternative to the official API client (integrations/higgsfield.py)
for users who have a paid Higgsfield web plan but no Cloud API key.
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PWTimeoutError,
)

from config import STORAGE_DIR, get_settings

logger = logging.getLogger(__name__)

# Persistent browser data directory (keeps you logged in between runs)
HIGGSFIELD_PROFILE = STORAGE_DIR / "higgsfield_profile"
HIGGSFIELD_PROFILE.mkdir(exist_ok=True)

# Output directory for downloaded videos
HIGGSFIELD_DOWNLOADS = STORAGE_DIR / "higgsfield_downloads"
HIGGSFIELD_DOWNLOADS.mkdir(exist_ok=True)

LOGIN_URL = "https://higgsfield.ai/auth/sign-in"
CREATE_VIDEO_URL = "https://higgsfield.ai/create/video"


class HiggsFieldBrowser:
    """Playwright-based Higgsfield client for paid web plan users."""

    def __init__(self, *, headless: bool | None = None):
        settings = get_settings()
        self.headless = (
            headless if headless is not None else settings.browser_headless
        )
        self._playwright = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> "HiggsFieldBrowser":
        await self.start()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def start(self) -> None:
        """Launch a persistent browser context so login state is retained."""
        self._playwright = await async_playwright().start()
        # Persistent context keeps cookies/localStorage across runs
        self._context = await self._playwright.chromium.launch_persistent_context(
            str(HIGGSFIELD_PROFILE),
            headless=self.headless,
            viewport={"width": 1400, "height": 900},
            accept_downloads=True,
        )

    async def close(self) -> None:
        """Close browser and Playwright."""
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()

    async def is_logged_in(self) -> bool:
        """Check whether the persistent session is already authenticated."""
        page = await self._context.new_page()
        try:
            await page.goto("https://higgsfield.ai/", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            # Look for signed-in indicators (user avatar, credits balance, etc.)
            indicators = [
                '[data-testid="user-avatar"]',
                '[class*="avatar"]',
                'button:has-text("Create")',
                '[class*="credits"]',
            ]
            for sel in indicators:
                if await page.locator(sel).count() > 0:
                    return True
            # If we see a sign-in button, we're NOT logged in
            signin = page.locator('a:has-text("Sign in"), a:has-text("Log in"), button:has-text("Sign in")')
            return await signin.count() == 0
        finally:
            await page.close()

    async def interactive_login(self, timeout: float = 300.0) -> bool:
        """Open the browser visible so the user can log in manually via SSO.

        Must be called with headless=False. Waits until login is detected or
        the timeout elapses. Session is persisted in HIGGSFIELD_PROFILE.
        """
        if self.headless:
            logger.warning("interactive_login requires headless=False")

        page = await self._context.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)

        logger.info("Please complete login in the opened browser window...")

        # Poll for login completion
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            await asyncio.sleep(3)
            current_url = page.url
            if "higgsfield.ai" in current_url and "/auth" not in current_url:
                # Likely logged in — verify
                if await self.is_logged_in():
                    logger.info("Login detected. Session saved.")
                    await page.close()
                    return True

        await page.close()
        return False

    async def generate_video_from_image(
        self,
        image_path: Path | str,
        *,
        prompt: str,
        duration: int = 5,
        model: str = "standard",
        motion: str | None = None,
        timeout: float = 420.0,
    ) -> Path:
        """Automate the create-video UI to produce a video from an image.

        Args:
            image_path: Local path to the reference image.
            prompt: Text description of the desired camera motion/scene.
            duration: Target clip length in seconds.
            model: Model name (varies by Higgsfield UI — e.g. "standard", "soul_cinema").
            motion: Optional motion preset name as it appears in the UI.
            timeout: Max seconds to wait for generation completion.

        Returns:
            Local path to the downloaded video file.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        page = await self._context.new_page()

        try:
            await page.goto(CREATE_VIDEO_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # If not logged in, bail
            if page.url.startswith("https://higgsfield.ai/auth"):
                raise RuntimeError(
                    "Not logged in to Higgsfield. Run interactive_login() first."
                )

            # Upload reference image
            await self._upload_image(page, image_path)

            # Enter prompt
            await self._enter_prompt(page, prompt)

            # Configure motion/duration/model if UI supports it
            if motion:
                await self._select_motion(page, motion)
            await self._select_duration(page, duration)
            await self._select_model(page, model)

            # Submit generation
            await self._submit_generation(page)

            # Wait for completion and download
            video_path = await self._wait_and_download(page, timeout=timeout)
            return video_path

        finally:
            await page.close()

    # ── UI interaction helpers ─────────────────────────────────────

    async def _upload_image(self, page: Page, image_path: Path) -> None:
        """Upload the reference image via the file input."""
        # Look for a file input (often hidden behind an Upload button)
        try:
            # Try clicking an upload button first (to reveal the input)
            upload_btn = page.locator(
                'button:has-text("Upload"), button:has-text("Add image"), '
                '[aria-label*="upload" i], [class*="upload"]'
            )
            if await upload_btn.count() > 0:
                async with page.expect_file_chooser() as fc_info:
                    await upload_btn.first.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(str(image_path))
            else:
                # Fallback: set files directly on any file input
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(str(image_path))
        except Exception as e:
            # Last resort — find any file input even if hidden
            logger.warning("Primary upload method failed (%s), trying fallback", e)
            file_input = page.locator('input[type="file"]').first
            await file_input.set_input_files(str(image_path))

        await asyncio.sleep(3)
        logger.info("Uploaded %s", image_path.name)

    async def _enter_prompt(self, page: Page, prompt: str) -> None:
        """Type the prompt into the prompt textarea."""
        selectors = [
            'textarea[placeholder*="prompt" i]',
            'textarea[placeholder*="describe" i]',
            'textarea[name="prompt"]',
            'textarea',
            '[contenteditable="true"]',
        ]
        for sel in selectors:
            loc = page.locator(sel).first
            if await loc.count() > 0:
                await loc.click()
                await loc.fill(prompt)
                await asyncio.sleep(1)
                return
        raise RuntimeError("Could not find prompt input on Higgsfield UI")

    async def _select_motion(self, page: Page, motion: str) -> None:
        """Select a motion preset (best-effort — UI varies)."""
        try:
            btn = page.locator(f'button:has-text("{motion}"), [data-motion="{motion}"]').first
            if await btn.count() > 0:
                await btn.click()
                await asyncio.sleep(1)
        except Exception as e:
            logger.debug("Motion selection skipped: %s", e)

    async def _select_duration(self, page: Page, duration: int) -> None:
        """Select duration if a selector is available."""
        try:
            dur_btn = page.locator(f'button:has-text("{duration}s"), button:has-text("{duration} sec")').first
            if await dur_btn.count() > 0:
                await dur_btn.click()
                await asyncio.sleep(1)
        except Exception as e:
            logger.debug("Duration selection skipped: %s", e)

    async def _select_model(self, page: Page, model: str) -> None:
        """Select model (best-effort — UI varies)."""
        try:
            name_map = {
                "standard": ["Standard", "Kling", "Veo"],
                "soul_cinema": ["Soul Cinema", "Cinema"],
                "sora": ["Sora"],
            }
            candidates = name_map.get(model, [model])
            for name in candidates:
                btn = page.locator(f'button:has-text("{name}")').first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(1)
                    return
        except Exception as e:
            logger.debug("Model selection skipped: %s", e)

    async def _submit_generation(self, page: Page) -> None:
        """Click the generate/submit button."""
        selectors = [
            'button:has-text("Generate")',
            'button:has-text("Create")',
            'button[type="submit"]',
            '[aria-label*="generate" i]',
        ]
        for sel in selectors:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_enabled():
                await btn.click()
                logger.info("Submitted video generation")
                await asyncio.sleep(3)
                return
        raise RuntimeError("Could not find generate button")

    async def _wait_and_download(self, page: Page, timeout: float) -> Path:
        """Poll for the finished video and download it."""
        start = asyncio.get_event_loop().time()
        video_selector = 'video source, video[src]'

        while asyncio.get_event_loop().time() - start < timeout:
            await asyncio.sleep(5)

            # Check if a video element with src is present (= completed)
            videos = await page.locator(video_selector).all()
            for v in videos:
                src = await v.get_attribute("src")
                if src and (".mp4" in src or "video" in src.lower()):
                    # Download via URL or download button
                    video_url = src
                    if video_url.startswith("blob:"):
                        # Need to use download button instead
                        return await self._download_via_button(page)
                    return await self._download_url(page, video_url)

            # Also look for a download button
            dl_btn = page.locator(
                'button:has-text("Download"), a:has-text("Download"), '
                '[aria-label*="download" i]'
            ).first
            if await dl_btn.count() > 0 and await dl_btn.is_enabled():
                return await self._download_via_button(page, dl_btn)

        raise TimeoutError(f"Higgsfield video generation timed out after {timeout}s")

    async def _download_url(self, page: Page, url: str) -> Path:
        """Download the video from a direct URL using the browser context."""
        import httpx
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            safe_name = re.sub(r"[^\w.-]", "_", url.split("/")[-1])[:80] or "higgsfield_video.mp4"
            if not safe_name.endswith(".mp4"):
                safe_name += ".mp4"
            out = HIGGSFIELD_DOWNLOADS / safe_name
            out.write_bytes(resp.content)
            logger.info("Downloaded video (%d bytes) to %s", len(resp.content), out)
            return out

    async def _download_via_button(self, page: Page, dl_btn=None) -> Path:
        """Trigger a click on the download button and capture the downloaded file."""
        if dl_btn is None:
            dl_btn = page.locator(
                'button:has-text("Download"), a:has-text("Download")'
            ).first

        async with page.expect_download(timeout=60000) as download_info:
            await dl_btn.click()
        download = await download_info.value
        suggested = download.suggested_filename or "higgsfield_video.mp4"
        out = HIGGSFIELD_DOWNLOADS / suggested
        await download.save_as(str(out))
        logger.info("Downloaded video to %s", out)
        return out


async def interactive_login_flow() -> bool:
    """Convenience: open a visible browser so the user can log in once."""
    async with HiggsFieldBrowser(headless=False) as hf:
        return await hf.interactive_login()
