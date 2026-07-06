"""Standalone script to test TRREB REALM login.

Run this with a visible browser to verify the SSO login flow:
    python scripts/test_realm_login.py

When TRREB sends an SMS 2FA code, write it to /tmp/realm_otp.txt:
    echo "123456" > /tmp/realm_otp.txt
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings, STORAGE_DIR


async def main():
    from playwright.async_api import async_playwright

    settings = get_settings()
    print(f"→ REALM username: {settings.realm_username}")
    print(f"→ REALM URL: {settings.realm_url}")
    print(f"→ SSO URL: {settings.realm_sso_url}")
    print()

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False, slow_mo=500)
    context = await browser.new_context(viewport={"width": 1400, "height": 900})
    page = await context.new_page()

    try:
        # Step 1: Navigate to portal
        print("→ Step 1: Navigating to torontomls.net...")
        await page.goto(settings.realm_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        await page.screenshot(path=str(STORAGE_DIR / "step1_portal.png"))
        print(f"  URL: {page.url}")

        # Click Login if available
        try:
            login_btn = page.locator('a:has-text("Login"), a:has-text("Sign In")')
            if await login_btn.count() > 0:
                await login_btn.first.click()
                await asyncio.sleep(3)
        except Exception:
            pass

        # If not on SSO, go directly
        if "sso.ampre.ca" not in page.url:
            await page.goto(settings.realm_sso_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)

        await page.screenshot(path=str(STORAGE_DIR / "step2_sso.png"))
        print(f"  SSO URL: {page.url}")

        # Step 2: Fill credentials
        print("→ Step 2: Filling credentials...")
        await page.wait_for_selector("#username", timeout=10000)
        await page.fill("#username", settings.realm_username)
        await page.fill("#password", settings.realm_password)
        await page.screenshot(path=str(STORAGE_DIR / "step3_filled.png"))
        await page.click("#kc-login")
        await asyncio.sleep(3)
        await page.screenshot(path=str(STORAGE_DIR / "step4_after_login.png"))
        print(f"  URL after login: {page.url}")

        # Step 3: Handle 2FA
        otp_selectors = [
            '#otp', 'input[name="otp"]',
            'input[autocomplete="one-time-code"]',
            'input[name="code"]',
        ]

        for sel in otp_selectors:
            try:
                await page.wait_for_selector(sel, timeout=5000, state="visible")
                print("→ Step 3: 2FA required! Write the SMS code to /tmp/realm_otp.txt")
                print("  Example: echo '123456' > /tmp/realm_otp.txt")

                otp_file = Path("/tmp/realm_otp.txt")
                otp_file.write_text("")

                code = ""
                for i in range(180):
                    await asyncio.sleep(1)
                    try:
                        code = otp_file.read_text().strip()
                        if code and len(code) >= 4:
                            otp_file.write_text("")
                            break
                    except Exception:
                        pass
                    if i % 30 == 0 and i > 0:
                        print(f"  Still waiting... ({i}s)")

                if code:
                    print(f"  Got code: {code}")
                    await page.wait_for_selector(sel, timeout=5000, state="visible")
                    await page.fill(sel, code)

                    for btn in ['#kc-login', 'input[type="submit"]', 'button[type="submit"]']:
                        try:
                            b = await page.wait_for_selector(btn, timeout=3000)
                            if b:
                                await b.click()
                                break
                        except Exception:
                            continue
                    await asyncio.sleep(5)
                else:
                    print("  ❌ No code received within 3 minutes")
                break
            except Exception:
                continue

        await page.screenshot(path=str(STORAGE_DIR / "step5_final.png"))
        print(f"→ Final URL: {page.url}")

        # Save session
        if "sso.ampre.ca" not in page.url:
            cookies = await context.cookies()
            session_path = STORAGE_DIR / "realm_session.json"
            session_path.write_text(json.dumps(cookies, indent=2))
            print(f"✅ Login successful! {len(cookies)} cookies saved to {session_path}")
        else:
            print("❌ Still on SSO page — login may have failed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
