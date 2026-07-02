"""BrokerBay Playwright-based client.

BrokerBay is a React SPA with no public API — all interactions are done
via browser automation. Login goes through Honeywell PingFederate SSO.

Flow:
  1. Navigate to Honeywell SSO URL
  2. Fill credentials (once per session)
  3. Session redirects to edge.brokerbay.com
  4. Save browser storageState to disk
  5. On subsequent runs, load storageState and skip login

This client does the heavy lifting: searching listings, reading details,
fetching time slots, and booking showings.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PWTimeoutError,
    async_playwright,
)

from config import get_settings, STORAGE_DIR

logger = logging.getLogger(__name__)

# URLs from the spec
HONEYWELL_SSO_URL = (
    "https://authn.honeywell.com/as/mHuzv5EdfY/resume/as/authorization.ping"
)
BROKERBAY_APP_URL = "https://edge.brokerbay.com"
BROKERBAY_LOGIN_URL = f"{BROKERBAY_APP_URL}/login"


class BrokerBayBrowserError(Exception):
    """Raised when a BrokerBay browser action fails."""


class BrokerBayBrowser:
    """Playwright-based BrokerBay automation client.

    Usage:
        async with BrokerBayBrowser() as bb:
            listing = await bb.search_listing("123 Maple Ave")
            slots = await bb.get_available_time_slots(listing["id"], "2025-03-25")
            conf = await bb.book_showing(...)
    """

    def __init__(
        self,
        two_factor_callback: Callable[[], Awaitable[str]] | None = None,
    ):
        self.settings = get_settings()
        self.two_factor_callback = two_factor_callback

        # Session file location (per spec: SESSION_PATH)
        sp = self.settings.session_path
        if sp.startswith("./"):
            self.session_file = STORAGE_DIR / sp.lstrip("./")
        else:
            self.session_file = Path(sp)
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> "BrokerBayBrowser":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    # ── Lifecycle ────────────────────────────────────────────────────

    async def start(self) -> None:
        """Launch browser and restore session if available."""
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=self.settings.browser_headless,
            slow_mo=self.settings.browser_slowmo,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context_kwargs: dict[str, Any] = {
            "viewport": {"width": 1400, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

        # Restore saved storage state if present
        if self.session_file.exists() and self.session_file.stat().st_size > 10:
            try:
                context_kwargs["storage_state"] = str(self.session_file)
                logger.info(
                    "brokerbay.session_restored", file=str(self.session_file)
                )
            except Exception as e:
                logger.warning("brokerbay.session_restore_error", error=str(e))

        self._context = await self._browser.new_context(**context_kwargs)
        self._page = await self._context.new_page()

    async def close(self) -> None:
        """Close browser cleanly."""
        try:
            if self._browser:
                await self._browser.close()
        finally:
            if self._pw:
                await self._pw.stop()
            self._browser = None
            self._context = None
            self._page = None
            self._pw = None

    # ── Auth ─────────────────────────────────────────────────────────

    async def ensure_logged_in(self) -> None:
        """Ensure the browser is authenticated. Login if needed."""
        if await self.is_session_valid():
            logger.info("brokerbay.session_valid")
            return

        logger.info("brokerbay.login_required")
        await self.login()

    async def is_session_valid(self) -> bool:
        """Check if the current session is still authenticated."""
        if not self._page:
            return False
        try:
            await self._page.goto(
                BROKERBAY_APP_URL, wait_until="domcontentloaded", timeout=15000
            )
            await self._random_wait(1.0, 2.0)

            # If URL still contains login/SSO redirects, not logged in
            url = self._page.url
            if any(
                marker in url.lower()
                for marker in ("login", "authn.honeywell.com", "signin", "auth")
            ):
                return False

            # Look for app-shell elements that only exist when logged in
            try:
                await self._page.wait_for_selector(
                    '[data-testid="user-menu"], '
                    '[class*="UserMenu"], '
                    'nav [class*="avatar"], '
                    'text=/dashboard/i, '
                    'text=/my listings/i',
                    timeout=5000,
                )
                return True
            except PWTimeoutError:
                return False
        except Exception as e:
            logger.warning("brokerbay.session_check_error", error=str(e))
            return False

    async def login(self) -> None:
        """Perform full BrokerBay login via Honeywell SSO."""
        if not self.settings.brokerbay_email or not self.settings.brokerbay_password:
            raise BrokerBayBrowserError(
                "BROKERBAY_EMAIL / BROKERBAY_PASSWORD not configured"
            )

        assert self._page is not None
        page = self._page

        # Navigate to Honeywell SSO (per spec)
        try:
            await page.goto(
                HONEYWELL_SSO_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )
        except PWTimeoutError:
            # Fallback: try the app URL, which will redirect to SSO
            await page.goto(
                BROKERBAY_LOGIN_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )

        await self._random_wait(1.5, 3.0)

        # Look for the email/username field (Honeywell Ping uses various names)
        email_selectors = [
            'input[name="pf.username"]',
            'input[name="username"]',
            'input[name="email"]',
            'input[type="email"]',
            '#username',
            '#email',
        ]
        email_field = await self._first_visible(page, email_selectors, timeout=15000)
        if not email_field:
            raise BrokerBayBrowserError(
                "Could not locate email/username field on Honeywell SSO page"
            )

        await email_field.fill(self.settings.brokerbay_email)
        await self._random_wait(0.3, 0.6)

        # Some flows require clicking "Next" before password appears
        next_btn_selectors = [
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'input[type="submit"][value="Next"]',
            'input[type="submit"][value="Continue"]',
        ]
        clicked_next = False
        for sel in next_btn_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    clicked_next = True
                    await self._random_wait(1.5, 2.5)
                    break
            except Exception:
                continue

        # Fill password
        pw_selectors = [
            'input[name="pf.pass"]',
            'input[name="password"]',
            'input[type="password"]',
            '#password',
        ]
        pw_field = await self._first_visible(page, pw_selectors, timeout=15000)
        if not pw_field:
            raise BrokerBayBrowserError(
                "Could not locate password field on Honeywell SSO page"
            )
        await pw_field.fill(self.settings.brokerbay_password)
        await self._random_wait(0.3, 0.6)

        # Submit
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Continue")',
        ]
        submit_btn = await self._first_visible(page, submit_selectors, timeout=5000)
        if submit_btn:
            await submit_btn.click()

        # Wait for redirect back to BrokerBay
        try:
            await page.wait_for_url(
                lambda url: "brokerbay.com" in url and "login" not in url.lower(),
                timeout=30000,
            )
        except PWTimeoutError:
            # Check for 2FA prompt
            await self._handle_2fa(page)
            try:
                await page.wait_for_url(
                    lambda url: "brokerbay.com" in url and "login" not in url.lower(),
                    timeout=30000,
                )
            except PWTimeoutError as e:
                raise BrokerBayBrowserError(
                    f"Login did not complete — still on {page.url}"
                ) from e

        await page.wait_for_load_state("networkidle", timeout=15000)
        await self._save_session()
        logger.info("brokerbay.login_success", landed_on=page.url)

    async def _handle_2fa(self, page: Page) -> None:
        """Handle 2FA prompt if present."""
        otp_selectors = [
            'input[name="otp"]',
            'input[name="code"]',
            'input[autocomplete="one-time-code"]',
            'input[placeholder*="code" i]',
            '#otp',
        ]
        field = await self._first_visible(page, otp_selectors, timeout=5000)
        if not field:
            return

        logger.info("brokerbay.2fa_required")
        if not self.two_factor_callback:
            raise BrokerBayBrowserError(
                "2FA required but no callback configured"
            )

        code = await self.two_factor_callback()
        if not code:
            raise BrokerBayBrowserError("No 2FA code provided")

        await field.fill(code)
        await self._random_wait(0.3, 0.6)

        for sel in [
            'button[type="submit"]',
            'button:has-text("Verify")',
            'button:has-text("Submit")',
            'button:has-text("Continue")',
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    break
            except Exception:
                continue

        await page.wait_for_load_state("networkidle", timeout=30000)

    async def _save_session(self) -> None:
        """Persist browser storageState to disk."""
        if not self._context:
            return
        state = await self._context.storage_state()
        self.session_file.write_text(json.dumps(state))
        logger.info("brokerbay.session_saved", file=str(self.session_file))

    # ── Page Object Methods ──────────────────────────────────────────

    async def search_listing(self, address_or_mls: str) -> dict[str, Any] | None:
        """Search BrokerBay for a listing.

        Args:
            address_or_mls: Street address or MLS number.

        Returns:
            Listing dict with id, address, mlsNumber — or None if not found.
        """
        await self.ensure_logged_in()
        assert self._page is not None
        page = self._page

        # Navigate to app home / search
        try:
            await page.goto(
                f"{BROKERBAY_APP_URL}/search?q={address_or_mls}",
                wait_until="domcontentloaded",
                timeout=20000,
            )
        except PWTimeoutError:
            await page.goto(BROKERBAY_APP_URL, wait_until="domcontentloaded")

        await self._random_wait(1.5, 2.5)

        # Find and use search input as fallback
        search_selectors = [
            'input[type="search"]',
            'input[placeholder*="search" i]',
            'input[placeholder*="address" i]',
            'input[placeholder*="mls" i]',
            '[data-testid="search-input"]',
        ]
        search_box = await self._first_visible(page, search_selectors, timeout=5000)
        if search_box:
            await search_box.fill(address_or_mls)
            await page.keyboard.press("Enter")
            await self._random_wait(2.0, 3.5)

        # Grab the first result
        result_selectors = [
            '[data-testid="listing-card"]',
            '[class*="ListingCard"]',
            '[class*="listing-result"]',
            'article[role="button"]',
            'a[href*="/listings/"]',
        ]
        for sel in result_selectors:
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0:
                    href = await loc.get_attribute("href") or ""
                    text = (await loc.inner_text()).strip()
                    listing_id = self._extract_id_from_href(href)

                    # Try to extract MLS from text
                    mls = ""
                    mls_match = re.search(r"\b[A-Z]\d{7,8}\b", text)
                    if mls_match:
                        mls = mls_match.group(0)

                    return {
                        "id": listing_id or address_or_mls,
                        "address": text.split("\n")[0].strip(),
                        "mlsNumber": mls,
                        "url": href,
                        "raw_text": text,
                    }
            except Exception:
                continue

        logger.warning("brokerbay.listing_not_found", query=address_or_mls)
        return None

    async def get_listing_details(self, listing_id: str) -> dict[str, Any]:
        """Load a listing's detail page and extract metadata."""
        await self.ensure_logged_in()
        assert self._page is not None
        page = self._page

        await page.goto(
            f"{BROKERBAY_APP_URL}/listings/{listing_id}",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        await self._random_wait(1.5, 2.5)

        text = await page.inner_text("body")

        return {
            "id": listing_id,
            "address": self._extract_address(text),
            "price": self._extract_price(text),
            "sqft": self._extract_number(text, r"(\d[\d,]+)\s*(?:sqft|sq\s*ft)"),
            "yearBuilt": self._extract_number(text, r"built\s*(?:in\s*)?(\d{4})"),
            "agentName": self._extract_agent_name(text),
            "agentPhone": self._extract_phone(text),
            "showingInstructions": self._extract_showing_instructions(text),
        }

    async def get_available_time_slots(
        self, listing_id: str, date: str
    ) -> list[dict[str, str]]:
        """Get available showing time windows for a listing on a date.

        Args:
            listing_id: BrokerBay listing ID.
            date: YYYY-MM-DD.

        Returns:
            List of {start, end} dicts (times in HH:MM).
        """
        await self.ensure_logged_in()
        assert self._page is not None
        page = self._page

        await page.goto(
            f"{BROKERBAY_APP_URL}/listings/{listing_id}/book?date={date}",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        await self._random_wait(1.5, 2.5)

        # Extract time slots from the booking widget
        slots: list[dict[str, str]] = []
        slot_selectors = [
            '[data-testid="time-slot"]',
            '[class*="TimeSlot"]:not([class*="disabled"])',
            'button[data-time]:not([disabled])',
        ]
        for sel in slot_selectors:
            try:
                els = page.locator(sel)
                count = await els.count()
                if count > 0:
                    for i in range(count):
                        el = els.nth(i)
                        t = (await el.inner_text()).strip()
                        # Parse "10:00 AM - 11:00 AM" or similar
                        m = re.match(
                            r"(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*[-–]\s*"
                            r"(\d{1,2}:\d{2}\s*(?:AM|PM)?)",
                            t,
                            re.IGNORECASE,
                        )
                        if m:
                            slots.append({"start": m.group(1), "end": m.group(2)})
                    break
            except Exception:
                continue

        return slots

    async def book_showing(
        self,
        listing_id: str,
        date_time: datetime,
        client_name: str,
        duration_minutes: int = 25,
    ) -> dict[str, Any]:
        """Book a showing on BrokerBay.

        Returns a confirmation dict with fields from the booking response.
        """
        await self.ensure_logged_in()
        assert self._page is not None
        page = self._page

        date_str = date_time.strftime("%Y-%m-%d")
        time_str = date_time.strftime("%I:%M %p").lstrip("0")

        # Navigate to booking page
        await page.goto(
            f"{BROKERBAY_APP_URL}/listings/{listing_id}/book?date={date_str}",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        await self._random_wait(1.5, 2.5)

        # Click the matching time slot
        time_clicked = False
        for pattern in [time_str, time_str.replace(" ", ""), time_str.lower()]:
            try:
                loc = page.locator(f'button:has-text("{pattern}")').first
                if await loc.count() > 0:
                    await loc.click()
                    time_clicked = True
                    await self._random_wait(0.5, 1.0)
                    break
            except Exception:
                continue

        if not time_clicked:
            raise BrokerBayBrowserError(
                f"Time slot {time_str} not available for {listing_id}"
            )

        # Fill client name
        name_selectors = [
            'input[name="clientName"]',
            'input[name="client_name"]',
            'input[placeholder*="client" i]',
            '[data-testid="client-name-input"]',
        ]
        name_field = await self._first_visible(page, name_selectors, timeout=5000)
        if name_field:
            await name_field.fill(client_name)

        # Set duration if the form supports it
        duration_selectors = [
            'input[name="duration"]',
            'select[name="duration"]',
        ]
        for sel in duration_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    tag = await el.evaluate("(e) => e.tagName")
                    if tag == "SELECT":
                        await el.select_option(str(duration_minutes))
                    else:
                        await el.fill(str(duration_minutes))
                    break
            except Exception:
                continue

        # Submit
        submit_selectors = [
            'button:has-text("Book")',
            'button:has-text("Request Showing")',
            'button:has-text("Confirm")',
            'button[type="submit"]',
        ]
        submit_btn = await self._first_visible(page, submit_selectors, timeout=5000)
        if not submit_btn:
            raise BrokerBayBrowserError("Could not find booking submit button")

        await submit_btn.click()

        # Wait for confirmation
        try:
            await page.wait_for_selector(
                'text=/confirmed|booked|success/i', timeout=15000
            )
        except PWTimeoutError:
            pass

        await self._random_wait(1.5, 2.5)

        # Extract confirmation details
        body_text = await page.inner_text("body")
        conf_id_match = re.search(
            r"(?:confirmation|booking|reference)[\s#:]*([A-Z0-9-]{6,})",
            body_text,
            re.IGNORECASE,
        )

        return {
            "confirmationId": conf_id_match.group(1) if conf_id_match else "",
            "listingId": listing_id,
            "bookedTime": date_time.isoformat(),
            "clientName": client_name,
            "durationMinutes": duration_minutes,
        }

    async def get_my_listings(self) -> list[dict[str, Any]]:
        """Fetch all active listings for the logged-in user's brokerage."""
        await self.ensure_logged_in()
        assert self._page is not None
        page = self._page

        await page.goto(
            f"{BROKERBAY_APP_URL}/my-listings",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        await self._random_wait(1.5, 2.5)

        listings: list[dict[str, Any]] = []
        selectors = [
            '[data-testid="listing-row"]',
            '[class*="ListingRow"]',
            '[class*="listing-item"]',
            'a[href*="/listings/"]',
        ]
        for sel in selectors:
            try:
                els = page.locator(sel)
                count = await els.count()
                if count > 0:
                    for i in range(count):
                        el = els.nth(i)
                        href = await el.get_attribute("href") or ""
                        text = (await el.inner_text()).strip()
                        listing_id = self._extract_id_from_href(href)
                        listings.append({
                            "id": listing_id,
                            "address": text.split("\n")[0].strip(),
                            "url": href,
                            "raw_text": text,
                        })
                    break
            except Exception:
                continue

        return listings

    async def get_pending_requests(self) -> list[dict[str, Any]]:
        """Fetch pending showing requests for our listings."""
        await self.ensure_logged_in()
        assert self._page is not None
        page = self._page

        await page.goto(
            f"{BROKERBAY_APP_URL}/showings?status=pending",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        await self._random_wait(1.5, 2.5)

        requests: list[dict[str, Any]] = []
        selectors = [
            '[data-testid="showing-request"]',
            '[class*="ShowingRequest"]',
            '[class*="pending-showing"]',
        ]
        for sel in selectors:
            try:
                els = page.locator(sel)
                count = await els.count()
                if count > 0:
                    for i in range(count):
                        el = els.nth(i)
                        text = (await el.inner_text()).strip()
                        requests.append({
                            "requestId": await el.get_attribute("data-id") or str(i),
                            "raw_text": text,
                        })
                    break
            except Exception:
                continue

        return requests

    async def approve_showing_request(self, request_id: str) -> bool:
        """Approve a pending showing request."""
        await self.ensure_logged_in()
        assert self._page is not None
        page = self._page

        await page.goto(
            f"{BROKERBAY_APP_URL}/showings/{request_id}",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        await self._random_wait(1.0, 2.0)

        for sel in [
            'button:has-text("Approve")',
            'button:has-text("Confirm")',
            '[data-testid="approve-button"]',
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0:
                    await btn.click()
                    await self._random_wait(1.0, 2.0)
                    return True
            except Exception:
                continue

        return False

    async def decline_showing_request(
        self, request_id: str, reason: str = ""
    ) -> bool:
        """Decline a pending showing request."""
        await self.ensure_logged_in()
        assert self._page is not None
        page = self._page

        await page.goto(
            f"{BROKERBAY_APP_URL}/showings/{request_id}",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        await self._random_wait(1.0, 2.0)

        for sel in [
            'button:has-text("Decline")',
            'button:has-text("Reject")',
            '[data-testid="decline-button"]',
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0:
                    await btn.click()
                    await self._random_wait(0.5, 1.0)

                    if reason:
                        reason_sel = 'textarea[name="reason"], input[name="reason"]'
                        reason_field = page.locator(reason_sel).first
                        if await reason_field.count() > 0:
                            await reason_field.fill(reason)

                    confirm_btn = page.locator(
                        'button:has-text("Confirm"), button[type="submit"]'
                    ).first
                    if await confirm_btn.count() > 0:
                        await confirm_btn.click()

                    await self._random_wait(1.0, 2.0)
                    return True
            except Exception:
                continue

        return False

    # ── Helpers ──────────────────────────────────────────────────────

    async def _first_visible(
        self, page: Page, selectors: list[str], timeout: int = 10000
    ):
        """Return the first visible element matching any of the given selectors."""
        per_selector = max(500, timeout // len(selectors))
        for sel in selectors:
            try:
                el = await page.wait_for_selector(
                    sel, state="visible", timeout=per_selector
                )
                if el:
                    return el
            except PWTimeoutError:
                continue
            except Exception:
                continue
        return None

    async def _random_wait(self, low: float = 0.15, high: float = 0.3) -> None:
        """Sleep a random short time to look human."""
        await asyncio.sleep(random.uniform(low, high))

    @staticmethod
    def _extract_id_from_href(href: str) -> str:
        """Pull the listing/showing ID out of a URL path."""
        m = re.search(r"/(?:listings|showings)/([A-Za-z0-9_-]+)", href)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_price(text: str) -> int | None:
        m = re.search(r"\$\s*([\d,]+)(?:\.\d{2})?", text)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_number(text: str, pattern: str) -> int | None:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_address(text: str) -> str:
        # Grab the first line that looks like a street address
        for line in text.splitlines():
            line = line.strip()
            if re.match(r"^\d{1,6}\s+\w", line) and len(line) < 200:
                return line
        return ""

    @staticmethod
    def _extract_agent_name(text: str) -> str:
        m = re.search(
            r"(?:Listing\s+Agent|Agent):\s*([A-Z][A-Za-z'\-]+\s+[A-Z][A-Za-z'\-]+)",
            text,
        )
        return m.group(1) if m else ""

    @staticmethod
    def _extract_phone(text: str) -> str:
        m = re.search(r"(\d{3}[-.\s]\d{3}[-.\s]\d{4})", text)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_showing_instructions(text: str) -> str:
        m = re.search(
            r"(?:Showing\s+Instructions|Access|Lockbox)[:\s]+(.{10,300})",
            text,
            re.DOTALL,
        )
        return m.group(1).strip().split("\n")[0] if m else ""
