"""Livabl.com pre-construction condo scraper (Playwright-based)."""

from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import datetime, timezone
from typing import Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from config import get_settings

logger = logging.getLogger(__name__)

LIVABL_BASE_URL = "https://www.livabl.com"

DEFAULT_ONTARIO_CITIES = [
    "toronto", "mississauga", "brampton", "markham", "vaughan",
    "richmond-hill", "oakville", "burlington", "hamilton", "ottawa",
    "pickering", "oshawa", "whitby", "ajax", "milton",
    "kitchener", "waterloo", "london", "guelph", "barrie",
    "newmarket", "aurora", "scarborough", "etobicoke", "north-york",
]

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _city_from_slug(slug: str) -> str:
    """Convert URL slug to display name: 'richmond-hill' -> 'Richmond Hill'."""
    return slug.replace("-", " ").title()


def _parse_price(text: str) -> float | None:
    """Extract numeric price from text like '$1,299,000' or 'From $499K'."""
    if not text:
        return None
    text = text.replace(",", "").replace("$", "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)\s*[kK]", text)
    if m:
        return float(m.group(1)) * 1000
    m = re.search(r"(\d+(?:\.\d+)?)\s*[mM]", text)
    if m:
        return float(m.group(1)) * 1_000_000
    m = re.search(r"(\d+)", text)
    if m:
        return float(m.group(1))
    return None


class LivablClient:
    """Playwright-based scraper for Livabl.com pre-construction listings."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._base_url = self.settings.livabl_base_url.rstrip("/")
        self._delay = self.settings.livabl_request_delay
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def _launch_browser(self) -> Page:
        """Launch Playwright browser and return a new page."""
        pw = await async_playwright().start()
        self._browser = await pw.chromium.launch(
            headless=self.settings.browser_headless,
            slow_mo=self.settings.browser_slowmo,
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=DEFAULT_USER_AGENT,
        )
        return await self._context.new_page()

    async def _close(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
            self._context = None

    async def _polite_delay(self) -> None:
        """Random delay between page loads to be respectful."""
        wait = random.uniform(self._delay * 0.75, self._delay * 1.5)
        await asyncio.sleep(wait)

    async def _try_extract_next_data(self, page: Page) -> dict | None:
        """Try to extract __NEXT_DATA__ JSON from a Next.js page."""
        try:
            data = await page.evaluate('''() => {
                const el = document.querySelector('script#__NEXT_DATA__');
                if (!el) return null;
                try { return JSON.parse(el.textContent); }
                catch { return null; }
            }''')
            return data
        except Exception:
            return None

    async def _extract_listing_cards(self, page: Page) -> list[dict[str, Any]]:
        """Extract project cards from a city listing page."""
        # Try __NEXT_DATA__ first
        next_data = await self._try_extract_next_data(page)
        if next_data:
            try:
                page_props = next_data.get("props", {}).get("pageProps", {})
                # Common Next.js patterns for listing data
                for key in ("listings", "communities", "projects", "results", "data"):
                    items = page_props.get(key)
                    if isinstance(items, list) and items:
                        return [self._normalize_next_data_card(item) for item in items]
                # Check for nested structure
                for key in page_props:
                    val = page_props[key]
                    if isinstance(val, dict):
                        for subkey in ("listings", "communities", "results", "items"):
                            items = val.get(subkey)
                            if isinstance(items, list) and items:
                                return [self._normalize_next_data_card(item) for item in items]
            except Exception as e:
                logger.debug("__NEXT_DATA__ parsing failed: %s", e)

        # DOM fallback: extract cards from page
        cards: list[dict[str, Any]] = []
        card_selectors = [
            "article", "[data-testid*='community']", "[data-testid*='listing']",
            "[class*='CommunityCard']", "[class*='ProjectCard']",
            "[class*='community-card']", "[class*='listing-card']",
            ".search-results a[href]",
        ]

        for sel in card_selectors:
            try:
                elements = await page.query_selector_all(sel)
                if not elements or len(elements) < 2:
                    continue

                for el in elements:
                    card = await self._parse_card_element(page, el)
                    if card and card.get("name"):
                        cards.append(card)

                if cards:
                    break
            except Exception:
                continue

        # Deduplicate by URL
        seen = set()
        unique = []
        for c in cards:
            url = c.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(c)
        return unique

    def _normalize_next_data_card(self, item: dict) -> dict[str, Any]:
        """Normalize a project item from __NEXT_DATA__ into our schema."""
        name = (
            item.get("name") or item.get("title") or
            item.get("projectName") or item.get("communityName") or ""
        )
        url_slug = item.get("slug") or item.get("url") or item.get("uri") or ""
        if url_slug and not url_slug.startswith("http"):
            url_slug = f"{self._base_url}/{url_slug.lstrip('/')}"

        developer = (
            item.get("developer") or item.get("developerName") or
            item.get("builder") or item.get("builderName") or ""
        )
        if isinstance(developer, dict):
            developer = developer.get("name", "")

        price_text = item.get("priceRange") or item.get("price") or ""
        if isinstance(price_text, dict):
            price_text = f"${price_text.get('min', '')} - ${price_text.get('max', '')}"

        return {
            "name": str(name).strip(),
            "developer": str(developer).strip() if developer else None,
            "url": str(url_slug),
            "price_text": str(price_text) if price_text else None,
            "status": item.get("status") or item.get("salesStatus") or None,
            "image_url": item.get("image") or item.get("imageUrl") or item.get("thumbnail") or None,
            "city": item.get("city") or item.get("cityName") or None,
            "address": item.get("address") or item.get("streetAddress") or None,
        }

    async def _parse_card_element(self, page: Page, el: Any) -> dict[str, Any]:
        """Parse a single card DOM element into a dict."""
        card: dict[str, Any] = {}
        try:
            # Name
            for sel in ["h2", "h3", "h4", "[class*='title']", "[class*='name']"]:
                name_el = await el.query_selector(sel)
                if name_el:
                    card["name"] = (await name_el.inner_text()).strip()
                    break

            # URL
            link = await el.query_selector("a[href]")
            if link:
                href = await link.get_attribute("href")
                if href:
                    if not href.startswith("http"):
                        href = f"{self._base_url}{href}"
                    card["url"] = href
            elif await el.get_attribute("href"):
                href = await el.get_attribute("href")
                if href and not href.startswith("http"):
                    href = f"{self._base_url}{href}"
                card["url"] = href

            # Developer
            for sel in ["[class*='developer']", "[class*='builder']", "[class*='Developer']"]:
                dev_el = await el.query_selector(sel)
                if dev_el:
                    card["developer"] = (await dev_el.inner_text()).strip()
                    break

            # Price
            for sel in ["[class*='price']", "[class*='Price']"]:
                price_el = await el.query_selector(sel)
                if price_el:
                    card["price_text"] = (await price_el.inner_text()).strip()
                    break

            # Status
            for sel in ["[class*='status']", "[class*='Status']", "[class*='badge']"]:
                status_el = await el.query_selector(sel)
                if status_el:
                    card["status"] = (await status_el.inner_text()).strip()
                    break

            # Image
            img = await el.query_selector("img[src]")
            if img:
                card["image_url"] = await img.get_attribute("src")

        except Exception as e:
            logger.debug("Error parsing card element: %s", e)

        return card

    async def _detect_pagination(self, page: Page) -> int:
        """Detect the last page number from pagination links."""
        max_page = 1
        try:
            links = await page.query_selector_all("a[href*='/page-']")
            for link in links:
                href = await link.get_attribute("href") or ""
                m = re.search(r"/page-(\d+)", href)
                if m:
                    max_page = max(max_page, int(m.group(1)))
        except Exception:
            pass

        # Also check __NEXT_DATA__ for pagination metadata
        next_data = await self._try_extract_next_data(page)
        if next_data:
            try:
                props = next_data.get("props", {}).get("pageProps", {})
                for key in props:
                    val = props[key]
                    if isinstance(val, dict):
                        total_pages = val.get("totalPages") or val.get("lastPage") or val.get("total_pages")
                        if total_pages and int(total_pages) > max_page:
                            max_page = int(total_pages)
            except Exception:
                pass

        return max_page

    async def _extract_project_detail(self, page: Page, url: str) -> dict[str, Any]:
        """Extract full details from a project page."""
        detail: dict[str, Any] = {"url": url, "detail_scraped": True}

        # Try __NEXT_DATA__ first
        next_data = await self._try_extract_next_data(page)
        if next_data:
            try:
                props = next_data.get("props", {}).get("pageProps", {})
                # Look for the main project/community object
                project = None
                for key in ("community", "project", "listing", "development", "data"):
                    if key in props and isinstance(props[key], dict):
                        project = props[key]
                        break
                if not project:
                    project = props

                if project:
                    detail.update(self._normalize_project_detail(project))
                    if detail.get("name"):
                        return detail
            except Exception as e:
                logger.debug("__NEXT_DATA__ detail parsing failed: %s", e)

        # DOM fallback
        await self._extract_detail_from_dom(page, detail)
        return detail

    def _normalize_project_detail(self, data: dict) -> dict[str, Any]:
        """Normalize project detail from __NEXT_DATA__."""
        result: dict[str, Any] = {}

        result["name"] = (
            data.get("name") or data.get("title") or
            data.get("projectName") or data.get("communityName") or ""
        )

        dev = data.get("developer") or data.get("builder") or data.get("developerName") or ""
        if isinstance(dev, dict):
            dev = dev.get("name", "")
        result["developer"] = dev or None

        result["address"] = data.get("address") or data.get("streetAddress") or None
        result["city"] = data.get("city") or data.get("cityName") or None
        result["status"] = data.get("status") or data.get("salesStatus") or None
        result["occupancy_date"] = data.get("occupancy") or data.get("occupancyDate") or data.get("completionDate") or None
        result["storeys"] = data.get("storeys") or data.get("stories") or data.get("numStoreys") or None
        result["total_suites"] = data.get("totalSuites") or data.get("totalUnits") or data.get("numUnits") or None
        result["description"] = data.get("description") or data.get("about") or None
        result["deposit_info"] = data.get("deposit") or data.get("depositStructure") or None
        result["maintenance_fee"] = data.get("maintenanceFee") or data.get("maintenanceFees") or None
        result["parking_price"] = data.get("parkingPrice") or data.get("parking") or None
        result["locker_price"] = data.get("lockerPrice") or data.get("locker") or None

        # Price range
        price = data.get("priceRange") or data.get("price") or {}
        if isinstance(price, dict):
            result["price_range"] = {
                "min": price.get("min") or price.get("from"),
                "max": price.get("max") or price.get("to"),
                "text": None,
            }
        elif isinstance(price, str):
            result["price_range"] = {"min": _parse_price(price), "max": None, "text": price}

        # Floor plans
        plans = data.get("floorPlans") or data.get("floorplans") or data.get("suites") or []
        if isinstance(plans, list):
            result["floor_plans"] = [
                {
                    "name": p.get("name") or p.get("title") or None,
                    "beds": p.get("beds") or p.get("bedrooms") or None,
                    "baths": p.get("baths") or p.get("bathrooms") or None,
                    "size_sqft": p.get("size") or p.get("sqft") or p.get("area") or None,
                    "price": p.get("price") or None,
                }
                for p in plans
            ]

        # Amenities
        amenities = data.get("amenities") or data.get("features") or []
        if isinstance(amenities, list):
            result["amenities"] = [
                a.get("name", a) if isinstance(a, dict) else str(a)
                for a in amenities
            ]

        # Images
        images = data.get("images") or data.get("gallery") or data.get("photos") or data.get("media") or []
        if isinstance(images, list):
            result["images"] = [
                img.get("url", img) if isinstance(img, dict) else str(img)
                for img in images
            ]

        return result

    async def _extract_detail_from_dom(self, page: Page, detail: dict[str, Any]) -> None:
        """Extract project details from DOM elements."""
        # Name
        for sel in ["h1", "[class*='ProjectName']", "[class*='title']"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text and len(text) < 200:
                        detail["name"] = text
                        break
            except Exception:
                continue

        # Developer
        for sel in ["[class*='developer']", "[class*='Developer']", "[class*='builder']"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    detail["developer"] = (await el.inner_text()).strip()
                    break
            except Exception:
                continue

        # Address
        for sel in ["[class*='address']", "[class*='Address']", "[class*='location']", "address"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    detail["address"] = (await el.inner_text()).strip()
                    break
            except Exception:
                continue

        # Price
        for sel in ["[class*='price']", "[class*='Price']"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    detail["price_range"] = {"min": _parse_price(text), "max": None, "text": text}
                    break
            except Exception:
                continue

        # Status
        for sel in ["[class*='status']", "[class*='Status']"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    detail["status"] = (await el.inner_text()).strip()
                    break
            except Exception:
                continue

        # Description
        for sel in ["[class*='description']", "[class*='Description']", "[class*='about']"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    detail["description"] = (await el.inner_text()).strip()
                    break
            except Exception:
                continue

        # Amenities
        for sel in ["[class*='amenity'] li", "[class*='Amenity'] li", "[class*='feature'] li"]:
            try:
                items = await page.query_selector_all(sel)
                if items:
                    detail["amenities"] = [
                        (await item.inner_text()).strip() for item in items
                    ]
                    break
            except Exception:
                continue

        # Images
        try:
            imgs = await page.query_selector_all(
                "[class*='gallery'] img, [class*='Gallery'] img, "
                "[class*='carousel'] img, [class*='hero'] img"
            )
            if imgs:
                detail["images"] = []
                for img in imgs:
                    src = await img.get_attribute("src") or await img.get_attribute("data-src")
                    if src:
                        detail["images"].append(src)
        except Exception:
            pass

    # -------------------------------------------------------------------
    # High-level scraping methods
    # -------------------------------------------------------------------

    async def scrape_city_listings(self, page: Page, city_slug: str) -> list[dict[str, Any]]:
        """Scrape all listing pages for a city. Returns project summary dicts."""
        all_cards: list[dict[str, Any]] = []
        base = f"{self._base_url}/{city_slug}-on/new-condos"

        # Page 1
        try:
            await page.goto(base, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning("Failed to load %s: %s", base, e)
            return []

        cards = await self._extract_listing_cards(page)
        all_cards.extend(cards)
        max_page = await self._detect_pagination(page)

        logger.info("%s page 1: %d cards, %d total pages", city_slug, len(cards), max_page)

        # Remaining pages
        for pg in range(2, max_page + 1):
            await self._polite_delay()
            url = f"{base}/page-{pg}"
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(1.5)
                cards = await self._extract_listing_cards(page)
                all_cards.extend(cards)
                logger.info("%s page %d: %d cards", city_slug, pg, len(cards))
            except Exception as e:
                logger.warning("Failed to load %s: %s", url, e)
                continue

        # Tag city on all cards
        city_name = _city_from_slug(city_slug)
        for card in all_cards:
            card.setdefault("city", city_name)

        return all_cards

    async def scrape_project(self, page: Page, project_url: str) -> dict[str, Any]:
        """Scrape a single project detail page."""
        try:
            await page.goto(project_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            return await self._extract_project_detail(page, project_url)
        except Exception as e:
            logger.warning("Failed to scrape project %s: %s", project_url, e)
            return {"url": project_url, "detail_scraped": False, "error": str(e)}

    async def scrape_ontario_condos(
        self,
        cities: list[str] | None = None,
        max_projects: int | None = None,
        skip_detail_pages: bool = False,
    ) -> dict[str, Any]:
        """Full extraction pipeline: discover listings, then scrape details."""
        city_list = cities or DEFAULT_ONTARIO_CITIES
        page = await self._launch_browser()
        all_projects: list[dict[str, Any]] = []
        errors: list[str] = []

        try:
            # Phase 1: Discover listings from each city
            print(f"Phase 1: Scanning {len(city_list)} Ontario cities for condos...")
            seen_urls: set[str] = set()

            for city_slug in city_list:
                print(f"  Scanning {_city_from_slug(city_slug)}...")
                await self._polite_delay()
                cards = await self.scrape_city_listings(page, city_slug)

                for card in cards:
                    url = card.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        card["scraped_at"] = datetime.now(timezone.utc).isoformat()
                        card["detail_scraped"] = False
                        all_projects.append(card)

                print(f"    Found {len(cards)} projects ({len(all_projects)} total unique)")

            # Phase 2: Scrape detail pages
            if not skip_detail_pages and all_projects:
                targets = all_projects[:max_projects] if max_projects else all_projects
                print(f"\nPhase 2: Scraping {len(targets)} project detail pages...")

                for i, project in enumerate(targets, 1):
                    url = project.get("url", "")
                    if not url:
                        continue
                    print(f"  [{i}/{len(targets)}] {project.get('name', url)}")
                    await self._polite_delay()
                    detail = await self.scrape_project(page, url)
                    if detail.get("detail_scraped"):
                        project.update(detail)
                    elif detail.get("error"):
                        errors.append(f"{url}: {detail['error']}")

        finally:
            await self._close()

        return {
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "source": "livabl.com",
            "cities_scraped": city_list,
            "total_projects": len(all_projects),
            "total_with_details": len([p for p in all_projects if p.get("detail_scraped")]),
            "errors": errors,
            "projects": all_projects,
        }
