"""Apify-powered trending data scraper.

Replaces the RSS-only scraper with multi-platform data from Instagram hashtags,
Reddit communities, Google Trends, and news sources. Falls back to RSS if
APIFY_TOKEN is missing or actors fail.

Actor selection:
- Instagram: apify/instagram-hashtag-scraper (public posts by hashtag, no login)
- Reddit: trudax/reddit-scraper (hot posts from subreddits)
- Google Trends: emastra/google-trends-scraper (rising queries, geo-filtered to Canada)
- News: lukaskrivka/article-extractor-smart (headline extraction from news sites)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# GTA-focused hashtags for Instagram scraping
INSTAGRAM_HASHTAGS = [
    "torontorealestate", "bramptonhomes", "vaughanrealestate",
    "mississaugahomes", "gtaliving", "ontariorealestate",
    "torontomortgage", "canadianrealestate", "firsttimehomebuyer",
    "gtainvestment",
]

# Subreddits to scrape
REDDIT_SUBREDDITS = [
    "toronto", "PersonalFinanceCanada", "canadahousing",
    "RealEstateCanada", "brampton", "mississauga",
    "ontario", "canada",
]

# News sites for article extraction
NEWS_URLS = [
    "https://www.cbc.ca/news/canada",
    "https://www.bnnbloomberg.ca/",
    "https://www.theglobeandmail.com/business/",
]

# Keyword → category mapping
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "real_estate": ["real estate", "home", "house", "condo", "listing", "buyer", "seller", "realtor", "property", "housing", "pre-construction"],
    "mortgage": ["mortgage", "interest rate", "bank of canada", "fixed rate", "variable rate", "refinance", "lending", "amortization"],
    "politics": ["trudeau", "poilievre", "carney", "election", "liberal", "conservative", "ndp", "policy", "government", "parliament", "senate"],
    "sports": ["raptors", "leafs", "blue jays", "tfc", "nhl", "nba", "mlb", "soccer", "hockey", "basketball", "game", "playoff"],
    "business": ["ai", "crypto", "startup", "layoff", "earnings", "stock", "market", "tech", "investment", "economy", "inflation", "gdp"],
    "lifestyle": ["food", "restaurant", "travel", "fitness", "car", "drive", "recipe", "fashion"],
    "viral": ["viral", "trending", "meme", "challenge", "tiktok", "broke the internet"],
}


def _categorize(text: str) -> str:
    """Map text content to a topic category based on keyword matching."""
    lower = text.lower()
    scores: dict[str, int] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def _velocity_score(engagement: dict, hours_old: float) -> float:
    """Score 0-10 based on engagement velocity (engagement / hours since post)."""
    total = sum([
        engagement.get("likes", 0),
        engagement.get("comments", 0) * 3,
        engagement.get("shares", 0) * 5,
        engagement.get("views", 0) * 0.01,
    ])
    if hours_old <= 0:
        hours_old = 1
    velocity = total / hours_old
    return min(10.0, round(velocity / 100, 1))


class ApifyTrendingEngine:
    """Fetches trending data from multiple platforms via Apify actors."""

    def __init__(self, token: str, enabled_actors: str = "instagram,reddit,google_trends,news"):
        from apify_client import ApifyClientAsync
        self.client = ApifyClientAsync(token)
        self.enabled = set(a.strip() for a in enabled_actors.split(",") if a.strip())

    async def fetch_all_trending(self) -> dict[str, list[dict[str, Any]]]:
        """Run all enabled actors in parallel, merge and categorize results."""
        tasks = []
        if "instagram" in self.enabled:
            tasks.append(("instagram", self._fetch_instagram()))
        if "reddit" in self.enabled:
            tasks.append(("reddit", self._fetch_reddit()))
        if "google_trends" in self.enabled:
            tasks.append(("google_trends", self._fetch_google_trends()))
        if "news" in self.enabled:
            tasks.append(("news", self._fetch_news()))

        if not tasks:
            return {}

        # Run all actors concurrently
        labels = [t[0] for t in tasks]
        coros = [t[1] for t in tasks]
        raw_results = await asyncio.gather(*coros, return_exceptions=True)

        all_items: list[dict[str, Any]] = []
        for label, result in zip(labels, raw_results):
            if isinstance(result, Exception):
                logger.warning(f"Apify actor '{label}' failed: {result}")
                continue
            if isinstance(result, list):
                all_items.extend(result)
                logger.info(f"Apify '{label}' returned {len(result)} items")

        # Categorize and bucket
        by_category: dict[str, list[dict[str, Any]]] = {}
        for item in all_items:
            cat = item.get("category") or _categorize(f"{item.get('title', '')} {item.get('summary', '')}")
            item["category"] = cat
            by_category.setdefault(cat, []).append(item)

        # Sort each category by velocity descending
        for cat in by_category:
            by_category[cat].sort(key=lambda x: x.get("velocity_score", 0), reverse=True)

        return by_category

    async def _fetch_instagram(self) -> list[dict[str, Any]]:
        """Fetch top posts from GTA real estate hashtags."""
        items: list[dict[str, Any]] = []
        try:
            run_input = {
                "hashtags": INSTAGRAM_HASHTAGS[:5],
                "resultsLimit": 30,
                "resultsType": "posts",
            }
            run = await self.client.actor("apify/instagram-hashtag-scraper").call(
                run_input=run_input,
                timeout_secs=120,
            )
            dataset = self.client.dataset(run["defaultDatasetId"])
            async for post in dataset.iterate_items():
                caption = (post.get("caption") or "")[:500]
                likes = post.get("likesCount") or post.get("likes") or 0
                comments = post.get("commentsCount") or post.get("comments") or 0
                posted_str = post.get("timestamp") or post.get("takenAtTimestamp") or ""
                author = post.get("ownerUsername") or post.get("owner", {}).get("username", "")

                engagement = {"likes": likes, "comments": comments}
                hours_old = 24  # default
                if posted_str:
                    try:
                        posted_dt = datetime.fromisoformat(str(posted_str).replace("Z", "+00:00"))
                        delta = datetime.now(timezone.utc) - posted_dt
                        hours_old = max(1, delta.total_seconds() / 3600)
                    except (ValueError, TypeError):
                        pass

                title = caption[:120] if caption else f"Instagram post by @{author}"
                items.append({
                    "source": "apify_instagram",
                    "platform": "instagram",
                    "title": title,
                    "summary": caption,
                    "url": post.get("url") or post.get("shortCode", ""),
                    "author": f"@{author}" if author else "",
                    "engagement": engagement,
                    "velocity_score": _velocity_score(engagement, hours_old),
                    "posted_at": posted_str,
                    "raw_data": {},
                })
        except Exception as e:
            logger.error(f"Instagram scrape failed: {e}")
            raise
        return items[:20]

    async def _fetch_reddit(self) -> list[dict[str, Any]]:
        """Fetch hot posts from GTA + finance subreddits."""
        items: list[dict[str, Any]] = []
        try:
            run_input = {
                "startUrls": [{"url": f"https://www.reddit.com/r/{sub}/hot/"} for sub in REDDIT_SUBREDDITS[:6]],
                "maxItems": 50,
                "sort": "hot",
            }
            run = await self.client.actor("trudax/reddit-scraper").call(
                run_input=run_input,
                timeout_secs=120,
            )
            dataset = self.client.dataset(run["defaultDatasetId"])
            async for post in dataset.iterate_items():
                title = (post.get("title") or "")[:200]
                body = (post.get("body") or post.get("selftext") or "")[:500]
                ups = post.get("numberOfUpvotes") or post.get("ups") or post.get("score") or 0
                comments = post.get("numberOfComments") or post.get("num_comments") or 0
                author = post.get("username") or post.get("author") or ""
                sub = post.get("communityName") or post.get("subreddit") or ""
                url = post.get("url") or ""

                engagement = {"likes": ups, "comments": comments}
                items.append({
                    "source": "apify_reddit",
                    "platform": "reddit",
                    "title": title,
                    "summary": body or f"r/{sub} — {ups} upvotes, {comments} comments",
                    "url": url,
                    "author": f"u/{author}" if author else f"r/{sub}",
                    "engagement": engagement,
                    "velocity_score": _velocity_score(engagement, 12),
                    "raw_data": {},
                })
        except Exception as e:
            logger.error(f"Reddit scrape failed: {e}")
            raise
        return items[:30]

    async def _fetch_google_trends(self) -> list[dict[str, Any]]:
        """Fetch rising Google Trends queries for Canada."""
        items: list[dict[str, Any]] = []
        try:
            run_input = {
                "searchTerms": [
                    "real estate Ontario", "mortgage rates Canada",
                    "Brampton homes", "GTA housing",
                    "Toronto news", "Canadian politics",
                ],
                "geo": "CA",
                "isPublic": True,
                "timeRange": "now 7-d",
                "maxItems": 30,
            }
            run = await self.client.actor("emastra/google-trends-scraper").call(
                run_input=run_input,
                timeout_secs=90,
            )
            dataset = self.client.dataset(run["defaultDatasetId"])
            async for trend in dataset.iterate_items():
                query = trend.get("term") or trend.get("query") or trend.get("title") or ""
                value = trend.get("value") or trend.get("interest") or 0

                items.append({
                    "source": "apify_google_trends",
                    "platform": "google_trends",
                    "title": query,
                    "summary": f"Trending in Canada — relative interest: {value}",
                    "url": f"https://trends.google.com/trends/explore?q={query}&geo=CA",
                    "author": "",
                    "engagement": {"interest": value},
                    "velocity_score": min(10.0, round(float(value) / 10, 1)) if value else 3.0,
                    "raw_data": {},
                })
        except Exception as e:
            logger.error(f"Google Trends scrape failed: {e}")
            raise
        return items[:20]

    async def _fetch_news(self) -> list[dict[str, Any]]:
        """Fetch headlines from Canadian news sources."""
        items: list[dict[str, Any]] = []
        try:
            run_input = {
                "startUrls": [{"url": url} for url in NEWS_URLS],
                "maxPagesPerCrawl": 20,
                "onlyNewArticles": True,
            }
            run = await self.client.actor("lukaskrivka/article-extractor-smart").call(
                run_input=run_input,
                timeout_secs=120,
            )
            dataset = self.client.dataset(run["defaultDatasetId"])
            async for article in dataset.iterate_items():
                title = (article.get("title") or "")[:200]
                text = (article.get("text") or article.get("description") or "")[:500]
                url = article.get("url") or ""
                source_name = article.get("source") or article.get("domain") or "news"
                pub_date = article.get("date") or article.get("publishedAt") or ""

                items.append({
                    "source": f"apify_news_{source_name}",
                    "platform": "news",
                    "title": title,
                    "summary": text,
                    "url": url,
                    "author": source_name,
                    "engagement": {},
                    "velocity_score": 5.0,
                    "posted_at": pub_date,
                    "raw_data": {},
                })
        except Exception as e:
            logger.error(f"News scrape failed: {e}")
            raise
        return items[:20]
