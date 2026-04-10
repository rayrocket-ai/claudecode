"""Trending data collection from free sources."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── RSS Feed Sources ──────────────────────────────────────────────────

RSS_FEEDS: dict[str, list[dict[str, str]]] = {
    "real_estate": [
        {"name": "BlogTO Real Estate", "url": "https://www.blogto.com/real-estate-toronto/feed/"},
        {"name": "Better Dwelling", "url": "https://betterdwelling.com/feed/"},
        {"name": "Globe RE", "url": "https://www.theglobeandmail.com/topics/real-estate/feed/"},
    ],
    "mortgage": [
        {"name": "RateSpy", "url": "https://www.ratespy.com/feed"},
        {"name": "Bank of Canada", "url": "https://www.bankofcanada.ca/feed/"},
    ],
    "politics": [
        {"name": "CBC Politics", "url": "https://www.cbc.ca/webfeed/rss/rss-politics"},
        {"name": "Globe Politics", "url": "https://www.theglobeandmail.com/topics/federal-politics/feed/"},
    ],
    "sports": [
        {"name": "TSN", "url": "https://www.tsn.ca/rss/feed"},
        {"name": "Sportsnet", "url": "https://www.sportsnet.ca/feed/"},
    ],
}

# ── HTTP Client ───────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "VideoScriptDashboard/1.0 (Content Research Bot)",
    "Accept": "application/json, text/html, application/rss+xml",
}


async def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=HEADERS, timeout=15.0, follow_redirects=True)


# ── RSS Parsing (stdlib xml.etree) ────────────────────────────────────

def _parse_rss_items(xml_text: str, limit: int = 5) -> list[dict[str, str]]:
    """Parse RSS/Atom XML and return list of {title, summary, link, published}."""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    # Handle RSS 2.0
    for item in root.iter("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        desc = item.findtext("description", "").strip()
        pub = item.findtext("pubDate", "").strip()
        if title:
            items.append({"title": title, "link": link, "summary": desc[:300], "published": pub})
        if len(items) >= limit:
            break

    # Handle Atom feeds if no RSS items found
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title = (entry.findtext("atom:title", "", ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            summary = (entry.findtext("atom:summary", "", ns) or entry.findtext("atom:content", "", ns) or "").strip()
            pub = (entry.findtext("atom:published", "", ns) or entry.findtext("atom:updated", "", ns) or "").strip()
            if title:
                items.append({"title": title, "link": link, "summary": summary[:300], "published": pub})
            if len(items) >= limit:
                break

    return items


# ── Google Trends ─────────────────────────────────────────────────────

async def fetch_google_trends() -> list[dict[str, Any]]:
    """Fetch daily trending searches for Canada via Google Trends RSS."""
    items = []
    try:
        async with await _get_client() as client:
            resp = await client.get(
                "https://trends.google.com/trending/rss?geo=CA"
            )
            if resp.status_code == 200:
                for entry in _parse_rss_items(resp.text, limit=15):
                    items.append({
                        "source": "google_trends",
                        "category": "general",
                        "title": entry["title"],
                        "summary": entry["summary"],
                        "url": entry["link"],
                        "raw_data": {"published": entry["published"]},
                    })
    except Exception as e:
        logger.warning(f"Google Trends fetch failed: {e}")
    return items


# ── RSS News Feeds ────────────────────────────────────────────────────

async def fetch_rss_feeds() -> list[dict[str, Any]]:
    """Fetch top headlines from RSS feeds across all categories."""
    items = []
    async with await _get_client() as client:
        for category, feeds in RSS_FEEDS.items():
            for feed_info in feeds:
                try:
                    resp = await client.get(feed_info["url"])
                    if resp.status_code == 200:
                        for entry in _parse_rss_items(resp.text, limit=5):
                            items.append({
                                "source": "rss_news",
                                "category": category,
                                "title": entry["title"],
                                "summary": entry["summary"],
                                "url": entry["link"],
                                "raw_data": {
                                    "feed_name": feed_info["name"],
                                    "published": entry["published"],
                                },
                            })
                except Exception as e:
                    logger.warning(f"RSS fetch failed for {feed_info['name']}: {e}")
    return items


# ── Bank of Canada Rates ─────────────────────────────────────────────

async def fetch_boc_rates() -> list[dict[str, Any]]:
    """Fetch current Bank of Canada overnight rate."""
    items = []
    try:
        async with await _get_client() as client:
            resp = await client.get(
                "https://www.bankofcanada.ca/valet/observations/V39079/json?recent=2"
            )
            if resp.status_code == 200:
                data = resp.json()
                observations = data.get("observations", [])
                if observations:
                    latest = observations[-1]
                    rate = latest.get("V39079", {}).get("v", "unknown")
                    rate_date = latest.get("d", "")
                    prev_rate = observations[-2].get("V39079", {}).get("v", "") if len(observations) > 1 else ""

                    summary = f"Bank of Canada overnight rate: {rate}%"
                    if prev_rate and prev_rate != rate:
                        summary += f" (changed from {prev_rate}%)"
                    else:
                        summary += " (unchanged)"

                    items.append({
                        "source": "bank_of_canada",
                        "category": "mortgage",
                        "title": f"BoC Overnight Rate: {rate}%",
                        "summary": summary,
                        "url": "https://www.bankofcanada.ca/rates/interest-rates/canadian-interest-rates/",
                        "raw_data": {"rate": rate, "previous_rate": prev_rate, "date": rate_date},
                    })
    except Exception as e:
        logger.warning(f"Bank of Canada fetch failed: {e}")
    return items


# ── Reddit ────────────────────────────────────────────────────────────

REDDIT_SUBS = [
    {"sub": "PersonalFinanceCanada", "category": "mortgage"},
    {"sub": "canadahousing", "category": "real_estate"},
    {"sub": "TorontoRealEstate", "category": "real_estate"},
    {"sub": "CanadaPolitics", "category": "politics"},
    {"sub": "sports", "category": "sports"},
]


async def fetch_reddit_posts() -> list[dict[str, Any]]:
    """Fetch hot posts from relevant subreddits (public JSON, no auth)."""
    items = []
    async with await _get_client() as client:
        for sub_info in REDDIT_SUBS:
            try:
                resp = await client.get(
                    f"https://www.reddit.com/r/{sub_info['sub']}/hot.json?limit=5",
                    headers={"User-Agent": "VideoScriptBot/1.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    posts = data.get("data", {}).get("children", [])
                    for post in posts:
                        pd = post.get("data", {})
                        if pd.get("stickied"):
                            continue
                        items.append({
                            "source": "reddit",
                            "category": sub_info["category"],
                            "title": pd.get("title", ""),
                            "summary": (pd.get("selftext", "") or "")[:300],
                            "url": f"https://reddit.com{pd.get('permalink', '')}",
                            "raw_data": {
                                "subreddit": sub_info["sub"],
                                "score": pd.get("score", 0),
                                "num_comments": pd.get("num_comments", 0),
                            },
                        })
            except Exception as e:
                logger.warning(f"Reddit fetch failed for r/{sub_info['sub']}: {e}")
    return items


# ── Main Collector ────────────────────────────────────────────────────

async def collect_all_trends() -> dict[str, list[dict[str, Any]]]:
    """Collect trending data from all free sources.

    Returns a dict keyed by category with lists of trending items.
    """
    all_items: list[dict[str, Any]] = []

    # Fetch from all sources
    google = await fetch_google_trends()
    rss = await fetch_rss_feeds()
    boc = await fetch_boc_rates()
    reddit = await fetch_reddit_posts()

    all_items.extend(google)
    all_items.extend(rss)
    all_items.extend(boc)
    all_items.extend(reddit)

    # Group by category
    by_category: dict[str, list[dict[str, Any]]] = {
        "real_estate": [],
        "mortgage": [],
        "politics": [],
        "sports": [],
        "general": [],
    }

    for item in all_items:
        cat = item.get("category", "general")
        if cat in by_category:
            by_category[cat].append(item)
        else:
            by_category["general"].append(item)

    # Sort each category by relevance (Reddit score, recency, etc.)
    for cat in by_category:
        by_category[cat] = sorted(
            by_category[cat],
            key=lambda x: x.get("raw_data", {}).get("score", 0),
            reverse=True,
        )

    logger.info(
        f"Collected trends: "
        + ", ".join(f"{k}={len(v)}" for k, v in by_category.items())
    )
    return by_category
