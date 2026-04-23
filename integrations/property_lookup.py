"""Look up a property by its street address and return a description.

Two complementary strategies are tried:

1. REALTOR.ca PropertySearch by street-address substring (primary for CA).
2. Google web search + page scrape fallback (works for US + any public listing).

Both paths normalise into a common `PropertyInfo` dataclass. Only descriptive
fields — beds / baths / sqft / public remarks — are used downstream; pricing
isn't required (though it's captured when available).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


REALTOR_CA_API = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"


@dataclass
class PropertyInfo:
    address: str
    description: str = ""
    bedrooms: str = ""
    bathrooms: str = ""
    square_footage: str = ""
    property_type: str = ""
    price: str = ""
    features: list[str] = field(default_factory=list)
    listing_url: str = ""
    source: str = ""

    def is_usable(self) -> bool:
        """True if we have enough signal to write a narration."""
        return bool(self.description) or bool(self.features) or bool(self.bedrooms)

    def summary(self) -> str:
        parts: list[str] = []
        if self.bedrooms:
            parts.append(f"{self.bedrooms} bed")
        if self.bathrooms:
            parts.append(f"{self.bathrooms} bath")
        if self.square_footage:
            parts.append(f"{self.square_footage} sqft")
        if self.property_type:
            parts.append(self.property_type)
        header = " · ".join(parts)
        desc = self.description or ""
        return f"{header}\n\n{desc}".strip()


async def lookup_property(address: str) -> PropertyInfo:
    """Find listing info for `address`. Never raises — returns a blank-ish
    PropertyInfo when nothing useful is found so the pipeline can fall back
    to a generic room-by-room voiceover script."""
    address = (address or "").strip()
    if not address:
        return PropertyInfo(address=address)

    logger.info("Looking up property: %s", address)

    # Strategy 1: REALTOR.ca (best for Canadian addresses)
    try:
        info = await _lookup_realtor_ca(address)
        if info and info.is_usable():
            logger.info("REALTOR.ca hit for %s", address)
            return info
    except Exception as exc:
        logger.warning("REALTOR.ca lookup failed for %r: %s", address, exc)

    # Strategy 2: Plain web search + scrape (best-effort)
    try:
        info = await _lookup_via_web_search(address)
        if info and info.is_usable():
            logger.info("Web-search hit (%s) for %s", info.source, address)
            return info
    except Exception as exc:
        logger.warning("Web-search lookup failed for %r: %s", address, exc)

    logger.info("No property data found for %r — will use a generic script", address)
    return PropertyInfo(address=address)


# ----------------------------------------------------------------------
# REALTOR.ca
# ----------------------------------------------------------------------
async def _lookup_realtor_ca(address: str) -> PropertyInfo | None:
    payload = {
        "ZoomLevel": "5",
        "LatitudeMax": "85",
        "LongitudeMax": "-50",
        "LatitudeMin": "40",
        "LongitudeMin": "-142",
        "Sort": "6-D",
        "PropertySearchTypeId": "1",
        "TransactionTypeId": "2",
        "keywords": address,
        "ApplicationId": "1",
        "CultureId": "1",
        "Version": "7.0",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            REALTOR_CA_API,
            data=payload,
            headers={
                "Origin": "https://www.realtor.ca",
                "Referer": "https://www.realtor.ca/",
            },
        )
    if resp.status_code != 200:
        return None

    data = resp.json()
    results = data.get("Results") or []
    if not results:
        return None

    listing = results[0]
    prop = listing.get("Property", {}) or {}
    addr = (prop.get("Address") or {}).get("AddressText", "")
    building = prop.get("Building") or {}

    features: list[str] = []
    for key in ("StyleName", "AmenitiesNearBy", "Features"):
        val = prop.get(key) or building.get(key)
        if isinstance(val, str) and val.strip():
            features.append(val.strip())

    return PropertyInfo(
        address=addr or address,
        description=(listing.get("PublicRemarks") or "").strip(),
        bedrooms=str(building.get("BedroomsTotal", "")).strip(),
        bathrooms=str(building.get("BathroomTotal", "")).strip(),
        square_footage=str(building.get("SizeInterior", "")).strip(),
        property_type=(prop.get("Type") or building.get("Type") or "").strip(),
        price=(prop.get("Price") or "").strip(),
        features=features,
        listing_url=(listing.get("RelativeDetailsURL") or "").strip(),
        source="realtor.ca",
    )


# ----------------------------------------------------------------------
# Web search fallback
# ----------------------------------------------------------------------
_LISTING_HOSTS = ("zillow.com", "redfin.com", "realtor.com", "trulia.com", "remax.", "realtor.ca")


async def _lookup_via_web_search(address: str) -> PropertyInfo | None:
    """Use a lightweight DuckDuckGo HTML search to find a listing page, then
    scrape meta description. Deliberately minimal — we just need a description.
    """
    query = f'"{address}" house for sale'
    async with httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RealEstateBot/1.0)"},
    ) as client:
        resp = await client.get("https://duckduckgo.com/html/", params={"q": query})
        if resp.status_code != 200:
            return None

        url = _first_listing_url(resp.text)
        if not url:
            return None

        page = await client.get(url)
        if page.status_code != 200:
            return None

    description = _extract_meta_description(page.text)
    if not description:
        return None

    beds = _first_number(page.text, r"(\d+(?:\.\d+)?)\s*(?:bd|bed|beds|bedroom)")
    baths = _first_number(page.text, r"(\d+(?:\.\d+)?)\s*(?:ba|bath|baths|bathroom)")
    sqft = _first_number(page.text, r"([\d,]+)\s*(?:sqft|sq\.?\s*ft)")

    return PropertyInfo(
        address=address,
        description=description.strip(),
        bedrooms=beds,
        bathrooms=baths,
        square_footage=sqft.replace(",", ""),
        listing_url=str(url),
        source="web",
    )


_DDG_RESULT_RE = re.compile(r'href="(?:https?://)?([^"/]+)(/[^"]*)"', re.IGNORECASE)


def _first_listing_url(html: str) -> str | None:
    for match in _DDG_RESULT_RE.finditer(html):
        host, path = match.group(1), match.group(2)
        if any(marker in host for marker in _LISTING_HOSTS):
            url = f"https://{host}{path}"
            # DuckDuckGo sometimes wraps redirects through uddg=
            if "duckduckgo.com" in url and "uddg=" in url:
                m = re.search(r"uddg=([^&]+)", url)
                if m:
                    from urllib.parse import unquote
                    return unquote(m.group(1))
            return url
    return None


_META_DESC_RE = re.compile(
    r'<meta\s+[^>]*?(?:name|property)=["\'](?:og:description|description)["\']'
    r'\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _extract_meta_description(html: str) -> str:
    m = _META_DESC_RE.search(html)
    return m.group(1) if m else ""


def _first_number(html: str, pattern: str) -> str:
    m = re.search(pattern, html, re.IGNORECASE)
    return m.group(1) if m else ""
