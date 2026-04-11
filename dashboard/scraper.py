"""Trending data scraper using RSS feeds — real estate & mortgage focus."""

import feedparser
import httpx
import asyncio
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    {
        "name": "Toronto Star Real Estate",
        "url": "https://www.thestar.com/content/thestar/feed.RSSManagerServlet.tag.real-estate.rss",
        "category": "real_estate",
    },
    {
        "name": "Globe and Mail Real Estate",
        "url": "https://www.theglobeandmail.com/real-estate/feed/",
        "category": "real_estate",
    },
    {
        "name": "CBC Toronto",
        "url": "https://www.cbc.ca/cmlink/rss-canada-toronto",
        "category": "local_news",
    },
    {
        "name": "BNN Bloomberg Real Estate",
        "url": "https://www.bnnbloomberg.ca/topic/real-estate/feed",
        "category": "market",
    },
    {
        "name": "Mortgage Broker News",
        "url": "https://www.mortgagebrokernews.ca/rss/articles",
        "category": "mortgage",
    },
    {
        "name": "Canadian Real Estate Magazine",
        "url": "https://www.canadianrealestatemagazine.ca/rss/news",
        "category": "real_estate",
    },
    {
        "name": "CREA News",
        "url": "https://www.crea.ca/feed/",
        "category": "real_estate",
    },
    {
        "name": "Bank of Canada",
        "url": "https://www.bankofcanada.ca/news/press-releases/feed/",
        "category": "mortgage",
    },
]

FALLBACK_ITEMS = [
    {
        "title": "GTA home prices show resilience despite rate uncertainty",
        "summary": "The Greater Toronto Area housing market continues to see stable demand in Brampton, Vaughan, and Mississauga despite ongoing interest rate discussions.",
        "link": "#",
        "category": "real_estate",
        "source": "Market Pulse",
        "published": datetime.utcnow().isoformat(),
    },
    {
        "title": "Bank of Canada holds rates — what it means for GTA buyers",
        "summary": "The latest rate decision creates a window of opportunity for pre-approved buyers in the GTA who have been waiting on the sidelines.",
        "link": "#",
        "category": "mortgage",
        "source": "Mortgage Insights",
        "published": datetime.utcnow().isoformat(),
    },
    {
        "title": "Pre-construction in Vaughan and Markham: 2024-2025 outlook",
        "summary": "Developers are launching new pre-construction projects in Vaughan and Markham as inventory tightens across the 905 corridor.",
        "link": "#",
        "category": "real_estate",
        "source": "GTA Property Report",
        "published": datetime.utcnow().isoformat(),
    },
    {
        "title": "First-time buyers in Brampton: How to compete in a tight market",
        "summary": "Brampton remains one of the most competitive markets for first-time buyers in the GTA, with multiple offers returning on entry-level detached homes.",
        "link": "#",
        "category": "real_estate",
        "source": "GTA Market Watch",
        "published": datetime.utcnow().isoformat(),
    },
    {
        "title": "Mortgage stress test update affects GTA affordability calculations",
        "summary": "Changes to the mortgage stress test are reshaping what buyers in the GTA can qualify for, with significant implications for Mississauga and Oakville buyers.",
        "link": "#",
        "category": "mortgage",
        "source": "Mortgage Insider",
        "published": datetime.utcnow().isoformat(),
    },
]


def parse_feed(feed_info: Dict) -> List[Dict]:
    """Parse a single RSS feed and return items."""
    try:
        feedparser.api._FeedParserMixin  # noqa
        import socket
        socket.setdefaulttimeout(5)
        parsed = feedparser.parse(feed_info["url"])
        items = []
        for entry in parsed.entries[:3]:  # Top 3 per feed
            item = {
                "title": getattr(entry, "title", ""),
                "summary": getattr(entry, "summary", getattr(entry, "description", "")),
                "link": getattr(entry, "link", "#"),
                "category": feed_info["category"],
                "source": feed_info["name"],
                "published": getattr(entry, "published", datetime.utcnow().isoformat()),
            }
            # Clean up HTML in summary
            if "<" in item["summary"]:
                import re
                item["summary"] = re.sub(r"<[^>]+>", "", item["summary"])[:300]
            if item["title"]:
                items.append(item)
        return items
    except Exception as e:
        logger.warning(f"Failed to parse feed {feed_info['name']}: {e}")
        return []


def get_trending_items(max_items: int = 10) -> List[Dict]:
    """Fetch trending items from all RSS feeds. Falls back to curated items."""
    all_items = []

    for feed_info in RSS_FEEDS:
        items = parse_feed(feed_info)
        all_items.extend(items)

    if not all_items:
        logger.info("No RSS items fetched — using fallback items")
        return FALLBACK_ITEMS[:max_items]

    # Deduplicate by title
    seen = set()
    unique = []
    for item in all_items:
        key = item["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # Prioritize real_estate and mortgage
    priority = [i for i in unique if i["category"] in ("real_estate", "mortgage")]
    rest = [i for i in unique if i not in priority]
    result = (priority + rest)[:max_items]

    if len(result) < 3:
        # Pad with fallbacks
        result.extend(FALLBACK_ITEMS[:max_items - len(result)])

    return result


def format_trending_for_prompt(items: List[Dict]) -> str:
    """Format trending items as a string for Claude prompts."""
    if not items:
        return "No trending items available. Use general GTA real estate context."

    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. [{item['category'].upper()}] {item['title']}")
        if item.get("summary"):
            summary = item["summary"][:200]
            lines.append(f"   {summary}")
    return "\n".join(lines)
