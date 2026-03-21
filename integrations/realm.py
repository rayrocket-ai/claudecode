"""TRREB REALM SSO login via Keycloak.

Handles the login flow:
1. Navigate to torontomls.net
2. Redirect to sso.ampre.ca (Keycloak)
3. Fill member ID + password
4. Handle SMS 2FA if required
5. Save session cookies for reuse
"""

from __future__ import annotations

import json
import logging
import asyncio
from pathlib import Path
from typing import Awaitable, Callable

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from config import get_settings, STORAGE_DIR

logger = logging.getLogger(__name__)

SESSION_FILE = STORAGE_DIR / "realm_session.json"


class RealmClient:
    """Handles TRREB REALM SSO authentication."""

    def __init__(self, two_factor_callback: Callable[[], Awaitable[str]] | None = None):
        self.settings = get_settings()
        self.two_factor_callback = two_factor_callback
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def login(self) -> dict:
        """Perform full TRREB SSO login. Returns session cookies dict."""
        pw = await async_playwright().start()
        self._browser = await pw.chromium.launch(
            headless=self.settings.browser_headless,
            slow_mo=self.settings.browser_slowmo,
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1400, "height": 900},
        )
        page = await self._context.new_page()

        try:
            # Navigate to TRREB portal
            await page.goto(self.settings.realm_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # Click Login if there's a login button
            try:
                login_btn = page.locator('a:has-text("Login"), a:has-text("Sign In"), button:has-text("Login")')
                if await login_btn.count() > 0:
                    await login_btn.first.click()
                    await asyncio.sleep(3)
            except Exception:
                pass

            # Should now be on Keycloak SSO
            if "sso.ampre.ca" not in page.url:
                # Try direct SSO URL
                await page.goto(self.settings.realm_sso_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

            # Fill credentials
            await page.wait_for_selector("#username", timeout=10000)
            await page.fill("#username", self.settings.realm_username)
            await page.fill("#password", self.settings.realm_password)
            await page.click("#kc-login")
            await asyncio.sleep(3)

            # Handle 2FA
            await self._handle_otp(page)

            # Check success
            await asyncio.sleep(3)
            if "sso.ampre.ca" not in page.url:
                # Login successful — save cookies
                cookies = await self._context.cookies()
                SESSION_FILE.write_text(json.dumps(cookies, indent=2))
                logger.info("REALM login successful. Landed on: %s", page.url)
                return {"success": True, "url": page.url, "cookies_count": len(cookies)}
            else:
                return {"success": False, "error": "Still on SSO page after login"}

        except Exception as e:
            logger.exception("REALM login failed: %s", e)
            return {"success": False, "error": str(e)}

        finally:
            if self._browser:
                await self._browser.close()

    async def _handle_otp(self, page: Page) -> None:
        """Handle OTP/2FA if the page asks for it."""
        otp_selectors = [
            '#otp', 'input[name="otp"]',
            'input[autocomplete="one-time-code"]',
            'input[name="code"]',
        ]

        for sel in otp_selectors:
            try:
                el = await page.wait_for_selector(sel, timeout=5000, state="visible")
                if el:
                    code = await self._get_code()
                    if code:
                        # Re-query to avoid stale handle
                        await page.wait_for_selector(sel, timeout=5000, state="visible")
                        await page.fill(sel, code)

                        # Submit
                        for btn in ['#kc-login', 'input[type="submit"]', 'button[type="submit"]']:
                            try:
                                b = await page.wait_for_selector(btn, timeout=3000)
                                if b:
                                    await b.click()
                                    break
                            except Exception:
                                continue
                        await asyncio.sleep(5)
                    break
            except Exception:
                continue

    async def _get_code(self) -> str | None:
        """Get the 2FA code from callback or file-based fallback."""
        if self.two_factor_callback:
            try:
                return await self.two_factor_callback()
            except Exception as e:
                logger.error("2FA callback failed: %s", e)

        # File-based fallback
        otp_file = Path("/tmp/realm_otp.txt")
        otp_file.write_text("")
        logger.info("Waiting for 2FA code in /tmp/realm_otp.txt")

        for _ in range(180):
            await asyncio.sleep(1)
            try:
                code = otp_file.read_text().strip()
                if code and len(code) >= 4:
                    otp_file.write_text("")
                    return code
            except Exception:
                pass

        return None

    @staticmethod
    def has_saved_session() -> bool:
        """Check if a saved session exists."""
        return SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 10
