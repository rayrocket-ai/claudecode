"""Redbricks pre-construction real estate data API client."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
MAX_REQUESTS_PER_MINUTE = 60


class RedbricksClient:
    """Async client for the Redbricks pre-construction data API."""

    def __init__(self, api_key: str, base_url: str = "https://api.redbricks.dev"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._lock = asyncio.Lock()
        self._request_timestamps: list[float] = []

    async def _ensure_rate_limit(self) -> None:
        """Enforce 60 requests per minute sliding window."""
        async with self._lock:
            now = time.monotonic()
            self._request_timestamps = [
                t for t in self._request_timestamps if now - t < 60.0
            ]
            if len(self._request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
                wait = 60.0 - (now - self._request_timestamps[0])
                if wait > 0:
                    logger.info("Rate limit reached, waiting %.1fs", wait)
                    await asyncio.sleep(wait)
            self._request_timestamps.append(time.monotonic())

    async def _get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Make an authenticated GET request to the Redbricks API."""
        await self._ensure_rate_limit()
        url = f"{self._base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        # Remove None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", "60"))
                    logger.warning("Rate limited, retrying after %.0fs", retry_after)
                    await asyncio.sleep(retry_after)
                    response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 401:
                    logger.warning("Redbricks auth failed: check API key")
                elif response.status_code == 404:
                    logger.warning("Redbricks resource not found: %s", endpoint)
                else:
                    logger.warning(
                        "Redbricks request failed: %s %s", response.status_code, url
                    )

        except Exception as e:
            logger.warning("Redbricks API error for %s: %s", endpoint, e)

        return None

    async def search_projects(
        self,
        *,
        name: str | None = None,
        city: str | None = None,
        district: str | None = None,
        neighbourhood: str | None = None,
        sales_status: str | None = None,
        construction_status: str | None = None,
        type_: str | None = None,
        occupancy_date_min: str | None = None,
        occupancy_date_max: str | None = None,
        launch_date_min: str | None = None,
        launch_date_max: str | None = None,
        current_price_min: float | None = None,
        current_price_max: float | None = None,
        price_per_sqft_min: float | None = None,
        price_per_sqft_max: float | None = None,
        interior_size_min: float | None = None,
        interior_size_max: float | None = None,
        beds_min: int | None = None,
        beds_max: int | None = None,
        developer: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_direction: str | None = None,
        per_page: int = 20,
        page: int = 1,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Search projects with filters. GET /api/v1/projects"""
        params: dict[str, Any] = {
            "name": name,
            "city": city,
            "district": district,
            "neighbourhood": neighbourhood,
            "sales_status": sales_status,
            "construction_status": construction_status,
            "type": type_,
            "occupancy_date_min": occupancy_date_min,
            "occupancy_date_max": occupancy_date_max,
            "launch_date_min": launch_date_min,
            "launch_date_max": launch_date_max,
            "current_price_min": current_price_min,
            "current_price_max": current_price_max,
            "price_per_sqft_min": price_per_sqft_min,
            "price_per_sqft_max": price_per_sqft_max,
            "interior_size_min": interior_size_min,
            "interior_size_max": interior_size_max,
            "beds_min": beds_min,
            "beds_max": beds_max,
            "developer": developer,
            "search": search,
            "sort_by": sort_by,
            "sort_direction": sort_direction,
            "per_page": per_page,
            "page": page,
            **kwargs,
        }
        return await self._get("/api/v1/projects", params)

    async def get_project(self, project_id: int) -> dict[str, Any] | None:
        """Get a single project by ID. GET /api/v1/projects/{id}"""
        return await self._get(f"/api/v1/projects/{project_id}")

    async def get_floorplans(
        self, project_id: int, page: int = 1, per_page: int = 50
    ) -> dict[str, Any] | None:
        """Get floorplans for a project. GET /api/v1/projects/{id}/floorplans"""
        return await self._get(
            f"/api/v1/projects/{project_id}/floorplans",
            {"page": page, "per_page": per_page},
        )

    async def get_prices(
        self,
        project_ids: str | None = None,
        floorplan_ids: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any] | None:
        """Get prices. GET /api/v1/prices"""
        return await self._get(
            "/api/v1/prices",
            {
                "projects_id": project_ids,
                "floorplans_id": floorplan_ids,
                "page": page,
                "per_page": per_page,
            },
        )

    async def get_all_projects(
        self, type_: str | None = None, per_page: int = 200
    ) -> list[dict[str, Any]]:
        """Fetch all projects across all pages."""
        all_projects: list[dict[str, Any]] = []
        page = 1
        while True:
            result = await self.search_projects(type_=type_, per_page=per_page, page=page)
            if not result or "data" not in result:
                break
            all_projects.extend(result["data"])
            meta = result.get("meta", {})
            if page >= meta.get("last_page", 1):
                break
            page += 1
        return all_projects

    async def get_all_floorplans(self, project_id: int) -> list[dict[str, Any]]:
        """Fetch all floorplans for a project across all pages."""
        all_floorplans: list[dict[str, Any]] = []
        page = 1
        while True:
            result = await self.get_floorplans(project_id, page=page, per_page=50)
            if not result or "data" not in result:
                break
            all_floorplans.extend(result["data"])
            meta = result.get("meta", {})
            if page >= meta.get("last_page", 1):
                break
            page += 1
        return all_floorplans

    async def get_all_prices(
        self, project_ids: str | None = None
    ) -> list[dict[str, Any]]:
        """Fetch all prices across all pages."""
        all_prices: list[dict[str, Any]] = []
        page = 1
        while True:
            result = await self.get_prices(
                project_ids=project_ids, page=page, per_page=50
            )
            if not result or "data" not in result:
                break
            all_prices.extend(result["data"])
            meta = result.get("meta", {})
            if page >= meta.get("last_page", 1):
                break
            page += 1
        return all_prices


# ---------------------------------------------------------------------------
# Module-level singleton & convenience functions
# ---------------------------------------------------------------------------

_client: RedbricksClient | None = None


def get_redbricks_client() -> RedbricksClient | None:
    """Return a shared RedbricksClient, or None if not configured."""
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    if not settings.is_redbricks_configured:
        return None
    _client = RedbricksClient(settings.redbricks_api_key, settings.redbricks_api_url)
    return _client


async def search_condos(
    city: str | None = None,
    search: str | None = None,
    current_price_min: float | None = None,
    current_price_max: float | None = None,
    beds_min: int | None = None,
    beds_max: int | None = None,
    per_page: int = 20,
    **kwargs: Any,
) -> list[dict[str, Any]] | None:
    """Quick search for pre-construction condos (convenience wrapper)."""
    client = get_redbricks_client()
    if not client:
        logger.warning("Redbricks not configured — set REDBRICKS_API_KEY")
        return None
    result = await client.search_projects(
        type_="Condo",
        city=city,
        search=search,
        current_price_min=current_price_min,
        current_price_max=current_price_max,
        beds_min=beds_min,
        beds_max=beds_max,
        per_page=per_page,
        **kwargs,
    )
    if result and "data" in result:
        return result["data"]
    return None


async def lookup_project(project_id: int) -> dict[str, Any] | None:
    """Look up a single pre-construction project by ID."""
    client = get_redbricks_client()
    if not client:
        logger.warning("Redbricks not configured — set REDBRICKS_API_KEY")
        return None
    return await client.get_project(project_id)
