"""TransactionDesk (TRREB WebForms®) browser automation.

This module automates:
1. Login via TRREB portal SSO → TransactionDesk
2. Creating new transactions
3. Adding OREA forms to transactions
4. Filling form fields with deal data
5. Saving completed forms
6. Creating Authentisign signing sessions

Entry point: https://ontariomlp.ca/trrebwebform/ (SSO handoff to pr.transactiondesk.com)
"""

from __future__ import annotations

import json
import logging
import re
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from config import get_settings, STORAGE_DIR
from forms.field_maps import FORM_100_FIELDS, FIELD_MAPS, FORM_NAME_MAP, TRANSACTION_TYPE_MAP

logger = logging.getLogger(__name__)

TD_BASE = "https://pr.transactiondesk.com"
PORTAL_ENTRY = "https://ontariomlp.ca/trrebwebform/"
SESSION_FILE = STORAGE_DIR / "transactiondesk_session.json"
REALM_SESSION_FILE = STORAGE_DIR / "realm_session.json"


class TransactionDeskClient:
    """Automates TransactionDesk via Playwright browser."""

    def __init__(self, two_factor_callback: Callable[[], Awaitable[str]] | None = None):
        self.settings = get_settings()
        self.two_factor_callback = two_factor_callback
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def _launch_browser(self) -> Page:
        """Launch browser, load saved session cookies, return page."""
        pw = await async_playwright().start()
        self._browser = await pw.chromium.launch(
            headless=self.settings.browser_headless,
            slow_mo=self.settings.browser_slowmo,
        )

        # Load REALM session cookies
        cookies = []
        for session_file in [REALM_SESSION_FILE, SESSION_FILE]:
            if session_file.exists():
                try:
                    saved = json.loads(session_file.read_text())
                    cookies.extend(saved)
                except Exception:
                    pass

        self._context = await self._browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        if cookies:
            # Filter valid cookies (Playwright requires name, value, domain)
            valid_cookies = [c for c in cookies if c.get("name") and c.get("domain")]
            if valid_cookies:
                await self._context.add_cookies(valid_cookies)

        self._page = await self._context.new_page()
        return self._page

    async def _save_session(self) -> None:
        """Save current browser cookies for reuse."""
        if self._context:
            cookies = await self._context.cookies()
            SESSION_FILE.write_text(json.dumps(cookies, indent=2))

    async def _close(self) -> None:
        """Clean up browser resources."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass

    async def _ensure_logged_in(self, page: Page) -> bool:
        """Navigate to TransactionDesk via the portal SSO entry point.
        Returns True if we land on TD successfully."""

        # First try going directly to TD (if session cookies are valid)
        await page.goto(f"{TD_BASE}/transactions", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        if "transactiondesk.com" in page.url and "login" not in page.url.lower():
            logger.info("TransactionDesk session is still valid")
            return True

        # Session expired — go through portal SSO
        logger.info("TD session expired, re-authenticating via portal SSO")
        await page.goto(PORTAL_ENTRY, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Check if we need to log into TRREB first
        if "sso.ampre.ca" in page.url or "login" in page.url.lower():
            logger.info("Need TRREB SSO login first")
            success = await self._do_trreb_login(page)
            if not success:
                return False

            # After TRREB login, navigate to WebForms again
            await page.goto(PORTAL_ENTRY, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)

        # Should now be on TransactionDesk
        if "transactiondesk.com" in page.url:
            await self._save_session()
            return True

        # Check if we're on ontariomlp.ca — the webforms link may need clicking
        if "ontariomlp.ca" in page.url:
            try:
                wf_link = page.locator('a:has-text("WebForms")')
                if await wf_link.count() > 0:
                    # Open in same tab by removing target
                    await wf_link.evaluate('el => el.removeAttribute("target")')
                    await wf_link.click()
                    await asyncio.sleep(5)
            except Exception:
                pass

        if "transactiondesk.com" in page.url:
            await self._save_session()
            return True

        logger.error("Failed to reach TransactionDesk. Current URL: %s", page.url)
        return False

    async def _do_trreb_login(self, page: Page) -> bool:
        """Handle the TRREB Keycloak SSO login flow."""
        try:
            # Wait for the login form
            await page.wait_for_selector("#username", timeout=10000)

            # Fill credentials
            await page.fill("#username", self.settings.realm_username)
            await page.fill("#password", self.settings.realm_password)
            await page.click("#kc-login")
            await asyncio.sleep(3)

            # Check for 2FA / OTP screen
            otp_selectors = [
                '#otp', 'input[name="otp"]',
                'input[autocomplete="one-time-code"]',
                'input[name="code"]',
            ]

            for sel in otp_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=5000, state="visible")
                    if el:
                        logger.info("2FA required — requesting code from user")
                        code = await self._get_2fa_code()
                        if code:
                            await page.fill(sel, code)
                            # Find and click the submit button
                            submit_btns = ['#kc-login', 'input[type="submit"]', 'button[type="submit"]']
                            for btn_sel in submit_btns:
                                try:
                                    btn = await page.wait_for_selector(btn_sel, timeout=3000)
                                    if btn:
                                        await btn.click()
                                        break
                                except Exception:
                                    continue
                            await asyncio.sleep(5)
                        else:
                            logger.error("No 2FA code received")
                            return False
                        break
                except Exception:
                    continue

            # Check if login succeeded
            await asyncio.sleep(3)
            return "sso.ampre.ca" not in page.url

        except Exception as e:
            logger.exception("TRREB login failed: %s", e)
            return False

    async def _get_2fa_code(self) -> str | None:
        """Get 2FA code from the callback or from a file-based fallback."""
        if self.two_factor_callback:
            try:
                return await self.two_factor_callback()
            except Exception as e:
                logger.error("2FA callback failed: %s", e)

        # File-based fallback: poll /tmp/realm_otp.txt
        otp_file = Path("/tmp/realm_otp.txt")
        otp_file.write_text("")  # Clear
        logger.info("Waiting for 2FA code in /tmp/realm_otp.txt ...")

        for _ in range(180):  # 3 minutes
            await asyncio.sleep(1)
            try:
                code = otp_file.read_text().strip()
                if code and len(code) >= 4:
                    otp_file.write_text("")  # Clear after reading
                    return code
            except Exception:
                pass

        return None

    # ── Transaction Management ────────────────────────────────

    async def create_transaction(self, name: str, doc_type: str = "aps") -> str | None:
        """Create a new transaction in TransactionDesk. Returns transaction UUID."""
        page = self._page
        assert page is not None

        await page.goto(f"{TD_BASE}/transactions", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Click "Create Transaction" button
        try:
            create_btn = page.locator('button:has-text("Create"), a:has-text("Create Transaction")')
            await create_btn.first.click(timeout=10000)
            await asyncio.sleep(2)
        except Exception:
            logger.error("Could not find Create Transaction button")
            return None

        # Fill the create transaction modal
        try:
            # Transaction name
            name_input = page.locator('input[name="name"], #transactionName, input[placeholder*="name" i]')
            if await name_input.count() > 0:
                await name_input.first.fill(name)

            # Transaction type
            tx_type = TRANSACTION_TYPE_MAP.get(doc_type, "Residential Sale")
            type_select = page.locator('select[name="txtype"], #transactionType')
            if await type_select.count() > 0:
                await type_select.first.select_option(label=tx_type)

            await asyncio.sleep(1)

            # Submit
            submit_btn = page.locator('button:has-text("Create"), button:has-text("Save"), input[type="submit"]')
            await submit_btn.first.click(timeout=10000)
            await asyncio.sleep(3)

        except Exception as e:
            logger.error("Error filling create transaction modal: %s", e)
            return None

        # Extract transaction UUID from URL
        current_url = page.url
        uuid_match = re.search(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', current_url)
        if uuid_match:
            return uuid_match.group(0)

        # Try from the page content / redirect
        await asyncio.sleep(2)
        current_url = page.url
        uuid_match = re.search(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', current_url)
        if uuid_match:
            return uuid_match.group(0)

        logger.warning("Could not extract transaction UUID from URL: %s", current_url)
        return None

    async def add_form_to_transaction(self, tx_uuid: str, form_name: str) -> str | None:
        """Add a form to an existing transaction. Returns form UUID."""
        page = self._page
        assert page is not None

        # Navigate to transaction forms
        await page.goto(
            f"{TD_BASE}/transaction/detail/{tx_uuid}/forms",
            wait_until="domcontentloaded",
        )
        await asyncio.sleep(2)

        # Click "Add Form" button
        try:
            add_btn = page.locator('button:has-text("Add"), a:has-text("Add Form")')
            await add_btn.first.click(timeout=10000)
            await asyncio.sleep(2)
        except Exception:
            logger.error("Could not find Add Form button")
            return None

        # Search for the form
        try:
            search_input = page.locator('input[type="search"], input[placeholder*="search" i], input[name="search"]')
            if await search_input.count() > 0:
                await search_input.first.fill(form_name[:30])  # partial name
                await asyncio.sleep(2)

            # Click the form in results
            form_link = page.locator(f'text="{form_name}"').first
            if await form_link.count() == 0:
                # Try partial match
                short_name = form_name.split(" - ")[-1] if " - " in form_name else form_name
                form_link = page.locator(f'text="{short_name}"').first

            await form_link.click(timeout=10000)
            await asyncio.sleep(1)

            # Confirm / Add
            confirm_btn = page.locator('button:has-text("Add"), button:has-text("Confirm"), button:has-text("OK")')
            if await confirm_btn.count() > 0:
                await confirm_btn.first.click()
                await asyncio.sleep(3)

        except Exception as e:
            logger.error("Error adding form: %s", e)
            return None

        # Extract form UUID
        current_url = page.url
        uuid_match = re.search(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', current_url)
        if uuid_match and uuid_match.group(0) != tx_uuid:
            return uuid_match.group(0)

        # Try to find form UUID from the forms list
        await page.goto(
            f"{TD_BASE}/transaction/detail/{tx_uuid}/forms",
            wait_until="domcontentloaded",
        )
        await asyncio.sleep(2)

        form_links = await page.query_selector_all('a[href*="/form/"]')
        for link in form_links:
            href = await link.get_attribute("href") or ""
            fm = re.search(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', href)
            if fm and fm.group(0) != tx_uuid:
                return fm.group(0)

        logger.warning("Could not extract form UUID")
        return None

    async def fill_form(self, form_uuid: str, deal_data: dict, doc_type: str = "aps") -> bool:
        """Fill a form's fields with deal data."""
        page = self._page
        assert page is not None

        # Navigate to the form editor
        await page.goto(
            f"{TD_BASE}/form/{form_uuid}/false",
            wait_until="domcontentloaded",
        )
        # Wait for form to render (TransactionDesk loads forms dynamically)
        await asyncio.sleep(5)

        # Wait for form iframe or direct fields
        # TD sometimes uses an iframe for the form editor
        frame = page.main_frame
        frames = page.frames
        for f in frames:
            if "form" in f.url.lower():
                frame = f
                break

        # Get the field map
        field_map = FIELD_MAPS.get(doc_type, FORM_100_FIELDS)
        flat_data = _flatten_deal_data(deal_data)

        filled_count = 0
        for html_name, data_key in field_map.items():
            value = flat_data.get(data_key, "")
            if not value:
                continue

            try:
                # Try to find and fill the field
                field = await frame.query_selector(f'input[name="{html_name}"], textarea[name="{html_name}"]')
                if field:
                    await field.click(click_count=3)  # Select all
                    await field.type(str(value))
                    filled_count += 1
                    logger.debug("Filled %s = %s", html_name, value)
            except Exception as e:
                logger.debug("Could not fill %s: %s", html_name, e)

        logger.info("Filled %d / %d fields in form %s", filled_count, len(field_map), form_uuid)
        return filled_count > 0

    async def save_form(self, form_uuid: str) -> bool:
        """Save the current form."""
        page = self._page
        assert page is not None

        try:
            save_btn = page.locator('button:has-text("Save"), a:has-text("Save")')
            if await save_btn.count() > 0:
                await save_btn.first.click()
                await asyncio.sleep(3)
                return True
        except Exception as e:
            logger.error("Error saving form: %s", e)

        return False

    # ── Signing (Authentisign) ────────────────────────────────

    async def create_signing_session(
        self,
        tx_uuid: str,
        signers: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Create an Authentisign signing session.

        signers: list of {"name": "...", "email": "...", "role": "buyer|seller"}
        """
        page = self._page
        assert page is not None

        try:
            # Navigate to signings
            await page.goto(f"{TD_BASE}/signings", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # Click Create Signing
            create_btn = page.locator('button:has-text("Create"), a:has-text("Create")')
            await create_btn.first.click(timeout=10000)
            await asyncio.sleep(2)

            # Select transaction
            tx_select = page.locator(f'text="{tx_uuid}"')
            if await tx_select.count() > 0:
                await tx_select.first.click()
                await asyncio.sleep(1)

            # Add signers
            for signer in signers:
                try:
                    add_signer = page.locator('button:has-text("Add Signer"), a:has-text("Add")')
                    if await add_signer.count() > 0:
                        await add_signer.first.click()
                        await asyncio.sleep(1)

                    name_input = page.locator('input[name*="name" i]').last
                    email_input = page.locator('input[name*="email" i]').last

                    if await name_input.count() > 0:
                        await name_input.fill(signer["name"])
                    if await email_input.count() > 0:
                        await email_input.fill(signer["email"])
                except Exception as e:
                    logger.warning("Error adding signer %s: %s", signer.get("name"), e)

            # Send for signing
            send_btn = page.locator('button:has-text("Send"), button:has-text("Start")')
            if await send_btn.count() > 0:
                await send_btn.first.click()
                await asyncio.sleep(3)

            return {"success": True, "url": page.url}

        except Exception as e:
            logger.exception("Error creating signing session: %s", e)
            return {"success": False, "error": str(e)}

    # ── High-Level Workflows ──────────────────────────────────

    async def run_full_workflow(
        self,
        deal_data: dict,
        doc_type: str = "aps",
    ) -> dict[str, Any]:
        """Complete workflow: login → create transaction → add form → fill → save."""
        try:
            page = await self._launch_browser()

            # Step 1: Login
            logged_in = await self._ensure_logged_in(page)
            if not logged_in:
                return {"success": False, "error": "Failed to log into TransactionDesk"}

            # Step 2: Create transaction
            addr = deal_data.get("property_street_number", "")
            street = deal_data.get("property_street_name", "")
            city = deal_data.get("property_city", "")
            tx_name = f"{addr} {street}, {city}".strip().strip(",")
            if not tx_name:
                tx_name = f"Transaction {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            tx_uuid = await self.create_transaction(tx_name, doc_type)
            if not tx_uuid:
                return {"success": False, "error": "Failed to create transaction"}

            # Step 3: Add form
            form_name = FORM_NAME_MAP.get(doc_type, FORM_NAME_MAP["aps"])
            form_uuid = await self.add_form_to_transaction(tx_uuid, form_name)
            if not form_uuid:
                return {
                    "success": False,
                    "error": f"Failed to add form '{form_name}' to transaction",
                    "transaction_uuid": tx_uuid,
                    "transaction_url": f"{TD_BASE}/transaction/detail/{tx_uuid}/overview",
                }

            # Step 4: Fill form
            filled = await self.fill_form(form_uuid, deal_data, doc_type)
            if not filled:
                logger.warning("No fields were filled — form selectors may need calibration")

            # Step 5: Save form
            await self.save_form(form_uuid)

            # Take screenshot
            screenshot_path = str(STORAGE_DIR / f"td_form_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path)

            return {
                "success": True,
                "transaction_uuid": tx_uuid,
                "form_uuid": form_uuid,
                "transaction_url": f"{TD_BASE}/transaction/detail/{tx_uuid}/overview",
                "form_url": f"{TD_BASE}/form/{form_uuid}/false",
                "screenshot_path": screenshot_path,
            }

        except Exception as e:
            logger.exception("TransactionDesk workflow error: %s", e)
            return {"success": False, "error": str(e)}

        finally:
            await self._close()

    async def test_connection(self) -> dict[str, Any]:
        """Test the connection to TransactionDesk. Returns status dict."""
        try:
            page = await self._launch_browser()
            logged_in = await self._ensure_logged_in(page)

            if logged_in:
                screenshot_path = str(STORAGE_DIR / "td_test_connection.png")
                await page.screenshot(path=screenshot_path)
                await self._save_session()
                return {
                    "success": True,
                    "url": page.url,
                    "screenshot_path": screenshot_path,
                }
            else:
                return {"success": False, "error": "Could not log into TransactionDesk"}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await self._close()


# ── Helper Functions ──────────────────────────────────────────────


def _flatten_deal_data(deal_data: dict) -> dict[str, str]:
    """Convert collected deal data into flat field values matching TransactionDesk."""
    flat: dict[str, str] = {}

    # Direct copies
    for key in [
        "buyer_1", "buyer_2", "seller_1", "seller_2",
        "property_street_number", "property_street_name", "property_unit",
        "property_city", "property_postal_code", "legal_description",
        "deposit_holder", "listing_brokerage", "listing_agent",
        "co_op_brokerage", "attached_schedules",
    ]:
        if deal_data.get(key):
            flat[key] = str(deal_data[key])

    # Province default
    flat["property_province"] = deal_data.get("property_province", "Ontario")

    # Purchase price
    price = deal_data.get("purchase_price")
    if price:
        price_num = _normalize_number(price)
        flat["purchase_price_formatted"] = f"{price_num:,.2f}"
        flat["purchase_price_words"] = _num_to_words(int(price_num))

    # Deposit
    deposit = deal_data.get("deposit")
    if deposit:
        dep_num = _normalize_number(deposit)
        flat["deposit_formatted"] = f"{dep_num:,.2f}"
        flat["deposit_words"] = _num_to_words(int(dep_num))

    # Offer date
    offer_date = deal_data.get("offer_date")
    if offer_date:
        d, m, y = _parse_date(offer_date)
        flat["offer_date_d"] = d
        flat["offer_date_mmmm"] = m
        flat["offer_date_yy"] = y

    # Irrevocability
    irrev_date = deal_data.get("irrevocability_date")
    if irrev_date:
        d, m, y = _parse_date(irrev_date)
        flat["irrev_expire_d"] = d
        flat["irrev_expire_mmmm"] = m
        flat["irrev_expire_yy"] = y

    irrev_time = deal_data.get("irrevocability_time")
    if irrev_time:
        flat["irrevocability_hours"] = str(irrev_time)

    # Closing date
    closing_date = deal_data.get("closing_date")
    if closing_date:
        d, m, y = _parse_date(closing_date)
        flat["closing_date_d"] = d
        flat["closing_date_mmmm"] = m
        flat["closing_date_yy"] = y

    return flat


def _normalize_number(value) -> float:
    """Convert a price/number to float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[,$\s]", "", value)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def _num_to_words(n: int) -> str:
    """Convert integer to English words."""
    if n == 0:
        return "Zero"

    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
            "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety"]

    def _chunk(num: int) -> str:
        if num == 0:
            return ""
        elif num < 20:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + (" " + ones[num % 10] if num % 10 else "")
        else:
            return ones[num // 100] + " Hundred" + (" " + _chunk(num % 100) if num % 100 else "")

    parts = []
    scales = [(1_000_000_000, "Billion"), (1_000_000, "Million"), (1_000, "Thousand")]

    for scale, name in scales:
        if n >= scale:
            parts.append(_chunk(n // scale) + " " + name)
            n %= scale

    if n > 0:
        parts.append(_chunk(n))

    return " ".join(parts)


def _parse_date(date_str: str) -> tuple[str, str, str]:
    """Parse a date string into (day, month_name, year) tuple."""
    if not date_str:
        return ("", "", "")

    # Try common formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return (str(dt.day), dt.strftime("%B"), str(dt.year))
        except ValueError:
            continue

    # Try dateutil as last resort
    try:
        from dateutil.parser import parse
        dt = parse(date_str)
        return (str(dt.day), dt.strftime("%B"), str(dt.year))
    except Exception:
        pass

    return (date_str, "", "")
