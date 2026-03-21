"""MLS property data lookup (REALTOR.ca / TRREB)."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

REALTOR_CA_API = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"


async def lookup_mls(mls_number: str) -> dict[str, Any] | None:
    """Look up property details by MLS number on REALTOR.ca.

    Returns a dict with property details if found, None otherwise.
    Note: REALTOR.ca may block automated requests. This is a best-effort lookup.
    """
    if not mls_number or not re.match(r"^[A-Z]?\d{5,10}$", mls_number.strip().upper()):
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # REALTOR.ca uses a POST endpoint with form data
            response = await client.post(
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
                    "ReferenceNumber": mls_number.strip().upper(),
                    "ApplicationId": "1",
                    "CultureId": "1",
                    "Version": "7.0",
                },
                headers={
                    "Origin": "https://www.realtor.ca",
                    "Referer": "https://www.realtor.ca/",
                },
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("Results", [])
                if results:
                    listing = results[0]
                    prop = listing.get("Property", {})
                    addr = prop.get("Address", {})
                    return {
                        "mls_number": listing.get("MlsNumber", mls_number),
                        "address": addr.get("AddressText", ""),
                        "price": prop.get("Price", ""),
                        "property_type": prop.get("Type", ""),
                        "bedrooms": prop.get("Bedrooms", ""),
                        "bathrooms": prop.get("Bathrooms", ""),
                        "description": listing.get("PublicRemarks", ""),
                    }

    except Exception as e:
        logger.warning("MLS lookup failed for %s: %s", mls_number, e)

    return None
