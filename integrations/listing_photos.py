"""Scrape listing photos from REALTOR.ca for tour video generation."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import httpx

from config import STORAGE_DIR

logger = logging.getLogger(__name__)

REALTOR_CA_API = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"
REALTOR_CA_DETAIL = "https://api2.realtor.ca/Listing.svc/PropertyDetails"

# Photo storage
PHOTOS_DIR = STORAGE_DIR / "listing_photos"
PHOTOS_DIR.mkdir(exist_ok=True)


async def fetch_listing_photos(
    mls_number: str,
    *,
    max_photos: int = 20,
) -> dict[str, Any]:
    """Fetch listing photos and property info from REALTOR.ca by MLS number.

    Returns dict with keys:
        - mls_number: str
        - address: str
        - photo_urls: list[str]  (full-resolution URLs)
        - downloaded_paths: list[Path]  (local file paths)
        - property_type: str
        - description: str
    """
    if not mls_number or not re.match(r"^[A-Z]?\d{5,10}$", mls_number.strip().upper()):
        raise ValueError(f"Invalid MLS number: {mls_number}")

    mls_number = mls_number.strip().upper()
    result: dict[str, Any] = {
        "mls_number": mls_number,
        "address": "",
        "photo_urls": [],
        "downloaded_paths": [],
        "property_type": "",
        "description": "",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Search for the listing
        search_resp = await client.post(
            REALTOR_CA_API,
            data={
                "ZoomLevel": "11",
                "LatitudeMax": "44.5",
                "LongitudeMax": "-79.0",
                "LatitudeMin": "43.5",
                "LongitudeMin": "-80.0",
                "Sort": "6-D",
                "PropertySearchTypeId": "1",
                "TransactionTypeId": "2",
                "ReferenceNumber": mls_number,
                "ApplicationId": "1",
                "CultureId": "1",
                "Version": "7.0",
            },
            headers={
                "Origin": "https://www.realtor.ca",
                "Referer": "https://www.realtor.ca/",
            },
        )

        if search_resp.status_code != 200:
            raise RuntimeError(f"REALTOR.ca search failed: HTTP {search_resp.status_code}")

        data = search_resp.json()
        results = data.get("Results", [])
        if not results:
            raise ValueError(f"No listing found for MLS# {mls_number}")

        listing = results[0]
        prop = listing.get("Property", {})
        addr = prop.get("Address", {})

        result["address"] = addr.get("AddressText", "")
        result["property_type"] = prop.get("Type", "")
        result["description"] = listing.get("PublicRemarks", "")

        # Extract photo URLs from the listing
        photos = prop.get("Photo", [])
        photo_urls = []
        for photo in photos[:max_photos]:
            # REALTOR.ca provides multiple sizes; prefer HighResPath
            url = (
                photo.get("HighResPath")
                or photo.get("MedResPath")
                or photo.get("LowResPath")
                or ""
            )
            if url:
                # Ensure full URL
                if url.startswith("//"):
                    url = "https:" + url
                elif url.startswith("/"):
                    url = "https://cdn.realtor.ca" + url
                photo_urls.append(url)

        # Also check for additional photo data in different format
        if not photo_urls:
            # Some listings use a different photo structure
            photo_list = listing.get("AlternateURL", {}).get("PhotoChangeDateUTC")
            individual_photos = listing.get("Individual", [])
            for indiv in individual_photos:
                photo_url = indiv.get("Photo", "")
                if photo_url and photo_url not in photo_urls:
                    if photo_url.startswith("//"):
                        photo_url = "https:" + photo_url
                    photo_urls.append(photo_url)

        result["photo_urls"] = photo_urls

        if not photo_urls:
            logger.warning("No photos found for MLS# %s", mls_number)
            return result

        # Download photos locally
        listing_dir = PHOTOS_DIR / mls_number
        listing_dir.mkdir(exist_ok=True)

        downloaded = []
        for i, url in enumerate(photo_urls):
            try:
                img_resp = await client.get(
                    url,
                    headers={"Referer": "https://www.realtor.ca/"},
                    follow_redirects=True,
                )
                if img_resp.status_code == 200:
                    # Determine extension from content type
                    ct = img_resp.headers.get("content-type", "image/jpeg")
                    ext = ".jpg"
                    if "png" in ct:
                        ext = ".png"
                    elif "webp" in ct:
                        ext = ".webp"

                    path = listing_dir / f"photo_{i:02d}{ext}"
                    path.write_bytes(img_resp.content)
                    downloaded.append(path)
                    logger.info("Downloaded photo %d/%d for MLS# %s", i + 1, len(photo_urls), mls_number)
            except Exception as e:
                logger.warning("Failed to download photo %d for MLS# %s: %s", i, mls_number, e)

        result["downloaded_paths"] = downloaded

    logger.info(
        "Fetched %d photos for MLS# %s (%s)",
        len(downloaded),
        mls_number,
        result["address"],
    )
    return result


async def fetch_photos_from_url(
    listing_url: str,
    *,
    max_photos: int = 20,
) -> dict[str, Any]:
    """Scrape listing photos from a REALTOR.ca listing URL using Playwright.

    Supports URLs like:
        https://www.realtor.ca/real-estate/12345678/...
    """
    # Try to extract MLS number from URL
    mls_match = re.search(r"/(\d{7,10})/", listing_url)
    if mls_match:
        # Try the API approach first with the listing ID
        pass

    # Use Playwright for full page scraping
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError("Playwright is required for URL-based photo scraping")

    result: dict[str, Any] = {
        "url": listing_url,
        "address": "",
        "photo_urls": [],
        "downloaded_paths": [],
        "property_type": "",
        "description": "",
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(listing_url, wait_until="networkidle", timeout=30000)

            # Extract address
            addr_el = await page.query_selector("h1.address, [class*='address']")
            if addr_el:
                result["address"] = (await addr_el.inner_text()).strip()

            # Extract all listing photos
            photo_urls = set()

            # Method 1: Look for photo gallery images
            img_elements = await page.query_selector_all(
                "img[src*='photo'], img[src*='listing'], "
                "img[src*='cdn.realtor.ca'], img[data-src*='cdn.realtor.ca']"
            )
            for img in img_elements:
                src = await img.get_attribute("src") or await img.get_attribute("data-src") or ""
                if src and ("cdn.realtor.ca" in src or "listing" in src.lower()):
                    if src.startswith("//"):
                        src = "https:" + src
                    # Try to get high-res version
                    src = re.sub(r"/\d+x\d+/", "/1024x768/", src)
                    photo_urls.add(src)

            # Method 2: Check for photo data in page scripts
            scripts = await page.evaluate("""
                () => {
                    const urls = [];
                    // Check for embedded photo data
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    scripts.forEach(s => {
                        try {
                            const data = JSON.parse(s.textContent);
                            if (data.photo) {
                                data.photo.forEach(p => {
                                    if (p.contentUrl) urls.push(p.contentUrl);
                                });
                            }
                            if (data.image) {
                                const imgs = Array.isArray(data.image) ? data.image : [data.image];
                                imgs.forEach(img => {
                                    if (typeof img === 'string') urls.push(img);
                                    else if (img.url) urls.push(img.url);
                                });
                            }
                        } catch(e) {}
                    });
                    return urls;
                }
            """)
            for url in scripts:
                if url.startswith("//"):
                    url = "https:" + url
                photo_urls.add(url)

            photo_urls = list(photo_urls)[:max_photos]
            result["photo_urls"] = photo_urls

            # Download photos
            if photo_urls:
                listing_id = re.sub(r"[^\w]", "_", listing_url.split("/")[-1] or "url_listing")[:50]
                listing_dir = PHOTOS_DIR / listing_id
                listing_dir.mkdir(exist_ok=True)

                async with httpx.AsyncClient(timeout=15.0) as client:
                    downloaded = []
                    for i, url in enumerate(photo_urls):
                        try:
                            resp = await client.get(url, follow_redirects=True)
                            if resp.status_code == 200:
                                ct = resp.headers.get("content-type", "image/jpeg")
                                ext = ".jpg"
                                if "png" in ct:
                                    ext = ".png"
                                elif "webp" in ct:
                                    ext = ".webp"
                                path = listing_dir / f"photo_{i:02d}{ext}"
                                path.write_bytes(resp.content)
                                downloaded.append(path)
                        except Exception as e:
                            logger.warning("Failed to download photo %d: %s", i, e)

                    result["downloaded_paths"] = downloaded

        finally:
            await browser.close()

    return result
