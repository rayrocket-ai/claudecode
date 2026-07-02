"""Google Maps geocoding + Distance Matrix client.

Lightweight async HTTP wrapper around the Google Maps APIs used for
tour planning:
  - Geocoding: address → (lat, lng)
  - Distance Matrix: pairwise drive times between stops

Usage:
    gc = Geocoder()
    point = await gc.geocode("123 Maple Ave, Toronto")
    matrix = await gc.distance_matrix([p1, p2, p3])
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

# Distance Matrix max 25 origins × 25 destinations per request
_MATRIX_BATCH = 10


class GeocoderError(Exception):
    """Raised when a Google Maps request fails."""


@dataclass
class GeoPoint:
    """A geocoded location."""
    address: str
    formatted_address: str
    lat: float
    lng: float

    @property
    def latlng(self) -> str:
        """Comma-separated string for API calls."""
        return f"{self.lat},{self.lng}"


class Geocoder:
    """Google Maps geocoding + Distance Matrix client."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.google_maps_api_key
        if not self.api_key:
            raise GeocoderError("GOOGLE_MAPS_API_KEY not configured")

    async def geocode(self, address: str) -> GeoPoint:
        """Geocode a single address.

        Raises GeocoderError if the address can't be resolved.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                GEOCODE_URL,
                params={"address": address, "key": self.api_key},
            )
            resp.raise_for_status()
            data = resp.json()

        status = data.get("status")
        if status != "OK":
            raise GeocoderError(
                f"Geocoding failed for '{address}': {status} "
                f"({data.get('error_message', '')})"
            )

        result = data["results"][0]
        loc = result["geometry"]["location"]
        return GeoPoint(
            address=address,
            formatted_address=result.get("formatted_address", address),
            lat=loc["lat"],
            lng=loc["lng"],
        )

    async def geocode_many(self, addresses: list[str]) -> list[GeoPoint]:
        """Geocode multiple addresses sequentially.

        Sequential (not parallel) to stay within Google Maps rate limits
        and match the spec's task-queue pattern.
        """
        results: list[GeoPoint] = []
        for addr in addresses:
            try:
                point = await self.geocode(addr)
                results.append(point)
            except GeocoderError as e:
                logger.warning("geocoder.skip", address=addr, error=str(e))
                # Append a placeholder so caller can track which ones failed
                results.append(
                    GeoPoint(address=addr, formatted_address=addr, lat=0.0, lng=0.0)
                )
        return results

    async def distance_matrix(
        self,
        points: list[GeoPoint],
        mode: str = "driving",
    ) -> list[list[int]]:
        """Compute pairwise drive times in minutes between all points.

        Returns a square matrix where matrix[i][j] = drive time from
        points[i] to points[j] in minutes (int, rounded).

        Handles Google's 25×25 per-request limit by batching.
        """
        n = len(points)
        matrix: list[list[int]] = [[0] * n for _ in range(n)]

        if n < 2:
            return matrix

        valid_points = [p for p in points if p.lat != 0.0 or p.lng != 0.0]
        if len(valid_points) < 2:
            return matrix

        origins_str = "|".join(p.latlng for p in points)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Batch destinations to stay under per-element limits
            for start in range(0, n, _MATRIX_BATCH):
                end = min(start + _MATRIX_BATCH, n)
                dests_str = "|".join(p.latlng for p in points[start:end])

                resp = await client.get(
                    DISTANCE_MATRIX_URL,
                    params={
                        "origins": origins_str,
                        "destinations": dests_str,
                        "mode": mode,
                        "key": self.api_key,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("status") != "OK":
                    raise GeocoderError(
                        f"Distance Matrix failed: {data.get('status')} "
                        f"({data.get('error_message', '')})"
                    )

                rows: list[dict[str, Any]] = data.get("rows", [])
                for i, row in enumerate(rows):
                    elements = row.get("elements", [])
                    for j_offset, el in enumerate(elements):
                        j = start + j_offset
                        if el.get("status") == "OK":
                            duration_sec = el["duration"]["value"]
                            matrix[i][j] = round(duration_sec / 60)
                        else:
                            matrix[i][j] = 9999  # large penalty

        return matrix
