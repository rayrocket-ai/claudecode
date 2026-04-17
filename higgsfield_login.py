"""Standalone script to log in to Higgsfield once and save the browser session.

Run this on a machine with a display before deploying the bot:

    python higgsfield_login.py

A browser window opens — sign in with Google/Microsoft/Apple. Once complete,
the session is saved to storage/higgsfield_profile/ and reused by the bot.
"""

from __future__ import annotations

import asyncio
import sys


async def main() -> int:
    from integrations.higgsfield_browser import interactive_login_flow

    print("Opening Higgsfield login... complete SSO in the browser window.")
    success = await interactive_login_flow()
    if success:
        print("✅ Login saved. You can now run the bot.")
        return 0
    print("❌ Login not completed before timeout.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
