"""
News Search Orchestration Service.
Coordinates parallel searching across multiple registered news source adapters
with rate limiting, latency tracking, and multi-category live breaking news aggregation.
"""

import asyncio
import time
from typing import List, Dict, Any, Tuple, Optional
import httpx
import feedparser
from dateutil import parser as date_parser
from datetime import datetime, timezone

from backend.app.models.models import Article, SourceStatus, SourceType
from backend.app.sources.base_source import BaseSourceAdapter
from backend.app.sources.source_registry import source_registry
from backend.app.utils.text_cleaner import clean_html, clean_text, truncate_snippet
from backend.app.utils.url_validator import normalize_url
from backend.app.utils.logger import logger
from backend.app.config import settings


class NewsSearchOrchestrator:
    """Orchestrates multi-source concurrent search and live breaking news feeds."""

    @classmethod
    async def search_all_sources(
        cls, 
        queries: Dict[str, List[str]], 
        language: str = "en"
    ) -> Tuple[List[Article], List[SourceStatus]]:
        """
        Executes parallel searches across all active news sources.
        """
        sources = source_registry.get_all_sources()
        articles: List[Article] = []
        statuses: List[SourceStatus] = []

        timeout = httpx.Timeout(
            settings.REQUEST_TIMEOUT_SECONDS, 
            connect=getattr(settings, "CONNECT_TIMEOUT_SECONDS", 4.0)
        )
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)

        async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True) as client:
            tasks = []
            for src_def in sources:
                adapter = source_registry.get_adapter(src_def.id)
                if not adapter or not adapter.enabled:
                    continue

                if "ta" in adapter.languages and len(adapter.languages) == 1:
                    src_queries = queries.get("ta", [])
                elif "en" in adapter.languages and len(adapter.languages) == 1:
                    src_queries = queries.get("en", [])
                else:
                    src_queries = queries.get("ta" if language == "ta" else "en", [])

                if adapter.is_primary and queries.get("primary"):
                    src_queries = queries["primary"] + src_queries

                if not src_queries:
                    src_queries = [queries.get("en", [""])[0]]

                target_query = src_queries[0]
                tasks.append(cls._search_single_source(adapter, target_query, client))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Search task error: {str(res)}")
                    continue
                art_list, status = res
                articles.extend(art_list)
                statuses.append(status)

        limited_articles = articles[:settings.MAX_TOTAL_ARTICLES]
        return limited_articles, statuses

    @classmethod
    async def _search_single_source(
        cls, 
        adapter: BaseSourceAdapter, 
        query: str, 
        client: httpx.AsyncClient
    ) -> Tuple[List[Article], SourceStatus]:
        start_time = time.perf_counter()
        try:
            results = await adapter.search(
                query=query, 
                client=client, 
                max_results=settings.MAX_ARTICLES_PER_SOURCE
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            status = SourceStatus(
                source_name=adapter.name,
                status="success" if results else "no_results",
                articles_found=len(results),
                latency_ms=round(elapsed_ms, 1),
                error_message=None
            )
            return results, status
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.debug(f"Source search failed for {adapter.name}: {str(e)}")
            status = SourceStatus(
                source_name=adapter.name,
                status="error",
                articles_found=0,
                latency_ms=round(elapsed_ms, 1),
                error_message=str(e)
            )
            return [], status

    @classmethod
    async def fetch_latest_breaking_news(
        cls, 
        limit: int = 12, 
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches live breaking news headlines across official government portals,
        top Tamil Nadu news outlets, and national English organizations.
        Enforces source diversity and balanced category distribution.
        """
        official_items: List[Dict[str, Any]] = []
        tamil_items: List[Dict[str, Any]] = []
        national_items: List[Dict[str, Any]] = []

        timeout = httpx.Timeout(6.0, connect=3.0)
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }

        # 1. Official Government & Primary Portal Endpoints
        official_feeds = [
            ("https://news.google.com/rss/search?q=site:pib.gov.in&hl=en-IN&gl=IN&ceid=IN:en", "PIB India (Official)", "pib_india", "en"),
            ("https://news.google.com/rss/search?q=site:dipr.tn.gov.in+OR+site:tn.gov.in+OR+தமிழ்நாடு+அரசு+அறிவிப்பு&hl=ta&gl=IN&ceid=IN:ta", "Tamil Nadu Govt (DIPR)", "tn_gov_dipr", "ta"),
            ("https://news.google.com/rss/search?q=site:mausam.imd.gov.in+OR+IMD+Chennai+weather+bulletin&hl=en-IN&gl=IN&ceid=IN:en", "IMD Chennai (Official)", "imd_chennai", "en"),
        ]

        # 2. Tamil Nadu Top News Adapters
        tamil_adapters = [
            source_registry.get_adapter("puthiya_thalaimurai"),
            source_registry.get_adapter("dinamalar"),
            source_registry.get_adapter("daily_thanthi"),
            source_registry.get_adapter("dinamani"),
            source_registry.get_adapter("bbc_tamil"),
            source_registry.get_adapter("vikatan"),
            source_registry.get_adapter("polimer_news"),
        ]
        tamil_adapters = [a for a in tamil_adapters if a and a.enabled]

        # 3. National / English News Adapters
        national_adapters = [
            source_registry.get_adapter("the_hindu"),
            source_registry.get_adapter("times_of_india"),
            source_registry.get_adapter("indian_express"),
            source_registry.get_adapter("ndtv"),
            source_registry.get_adapter("bbc"),
        ]
        national_adapters = [a for a in national_adapters if a and a.enabled]

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            tasks = []
            # Official Government Feeds
            for url, label, src_id, lang in official_feeds:
                tasks.append(cls._fetch_categorized_feed(url, label, src_id, lang, "official", True, client, headers))

            # Tamil Feeds
            tasks.append(cls._fetch_categorized_feed("https://news.google.com/rss?hl=ta&gl=IN&ceid=IN:ta", "Tamil Nadu Breaking News", "top_tamil", "ta", "tamil", False, client, headers))
            for adapter in tamil_adapters:
                if adapter.rss_urls:
                    tasks.append(cls._fetch_adapter_items(adapter, adapter.rss_urls[0], "tamil", client))

            # National / English Feeds
            tasks.append(cls._fetch_categorized_feed("https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en", "National Breaking News", "top_national", "en", "national", False, client, headers))
            for adapter in national_adapters:
                if adapter.rss_urls:
                    tasks.append(cls._fetch_adapter_items(adapter, adapter.rss_urls[0], "national", client))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    for item in res:
                        cat = item.get("category", "general")
                        if cat == "official" or item.get("is_official"):
                            official_items.append(item)
                        elif cat == "tamil":
                            tamil_items.append(item)
                        else:
                            national_items.append(item)

        # Deduplicate within each stream
        def dedupe_stream(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            seen = set()
            out = []
            source_counts: Dict[str, int] = {}
            for it in items:
                title_clean = it.get("title", "").strip().lower()
                src = it.get("source", "")
                if not title_clean or title_clean in seen:
                    continue
                # Enforce max 2 articles per source in top stream
                if source_counts.get(src, 0) >= 2:
                    continue
                seen.add(title_clean)
                source_counts[src] = source_counts.get(src, 0) + 1
                out.append(it)
            return out

        clean_official = dedupe_stream(official_items)
        clean_tamil = dedupe_stream(tamil_items)
        clean_national = dedupe_stream(national_items)

        # Date sorting helper
        def parse_date_epoch(item):
            d = item.get("publication_date")
            if not d or d == "Just Now":
                return datetime.now(timezone.utc).timestamp()
            try:
                dt = date_parser.parse(str(d), fuzzy=True)
                return dt.timestamp()
            except Exception:
                return 0

        clean_official.sort(key=parse_date_epoch, reverse=True)
        clean_tamil.sort(key=parse_date_epoch, reverse=True)
        clean_national.sort(key=parse_date_epoch, reverse=True)

        if category == "official":
            return clean_official[:limit]
        elif category == "tamil":
            return clean_tamil[:limit]
        elif category == "national":
            return clean_national[:limit]

        # Balanced Interleaving for "All / Default" view:
        # Guarantee Official Govt, Tamil News, and National News are fairly represented
        combined: List[Dict[str, Any]] = []
        max_len = max(len(clean_official), len(clean_tamil), len(clean_national))
        
        for i in range(max_len):
            if i < len(clean_official):
                combined.append(clean_official[i])
            if i < len(clean_tamil):
                combined.append(clean_tamil[i])
            if i < len(clean_national):
                combined.append(clean_national[i])
            if len(combined) >= limit:
                break

        return combined[:limit]

    @classmethod
    async def _fetch_categorized_feed(
        cls, 
        url: str, 
        fallback_source: str, 
        src_id: str,
        lang: str, 
        category: str,
        is_official: bool,
        client: httpx.AsyncClient, 
        headers: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:6]:
                raw_title = getattr(entry, "title", "").strip()
                if not raw_title:
                    continue
                source_name = fallback_source
                if " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    if not is_official:
                        source_name = parts[1].strip()
                else:
                    title = raw_title

                link = getattr(entry, "link", "")
                pub_date = getattr(entry, "published", None) or getattr(entry, "updated", None)
                summary = clean_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))

                items.append({
                    "title": clean_text(title),
                    "source": source_name,
                    "source_id": src_id,
                    "url": normalize_url(link),
                    "publication_date": pub_date or "Just Now",
                    "snippet": truncate_snippet(summary or title, 140),
                    "language": lang,
                    "category": category,
                    "is_official": is_official
                })
            return items
        except Exception as e:
            logger.debug(f"Failed to fetch categorized feed {url}: {str(e)}")
            return []

    @classmethod
    async def _fetch_adapter_items(
        cls, 
        adapter: BaseSourceAdapter, 
        feed_url: str, 
        category: str, 
        client: httpx.AsyncClient
    ) -> List[Dict[str, Any]]:
        try:
            resp = await client.get(feed_url, headers=adapter.headers)
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:3]:
                title = getattr(entry, "title", "").strip()
                if not title:
                    continue
                link = getattr(entry, "link", "")
                pub_date = getattr(entry, "published", None) or getattr(entry, "updated", None)
                summary = clean_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))
                items.append({
                    "title": clean_text(title),
                    "source": adapter.name,
                    "source_id": adapter.source_id,
                    "url": normalize_url(link),
                    "publication_date": pub_date or "Just Now",
                    "snippet": truncate_snippet(summary or title, 140),
                    "language": "ta" if "ta" in adapter.languages else "en",
                    "category": category,
                    "is_official": adapter.is_primary
                })
            return items
        except Exception as e:
            logger.debug(f"Failed to fetch adapter feed {feed_url}: {str(e)}")
            return []
