"""
Base News Source Adapter.
Defines standard interface for all news source collectors with high-precision query filtering.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
import feedparser
import urllib.parse
import re
from datetime import datetime, timezone

from backend.app.models.models import Article, EvidencePolarity, SourceType
from backend.app.utils.text_cleaner import clean_html, clean_text, remove_boilerplate, truncate_snippet
from backend.app.utils.url_validator import is_safe_url, normalize_url
from backend.app.utils.logger import logger
from backend.app.config import settings

# Common stop words to exclude from loose matching
STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "with", "by", "from",
    "is", "was", "are", "were", "be", "been", "being", "have", "has", "had",
    "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "this", "that", "these", "those", "due", "because"
}


class BaseSourceAdapter(ABC):
    """
    Abstract base class for all news source adapters.
    Each adapter handles searching, RSS parsing, fetching and metadata extraction for a specific news source.
    """

    source_id: str = "base"
    name: str = "Base News Source"
    languages: List[str] = ["en"]
    region: str = "India"
    priority: str = "medium"
    reliability: str = "medium"
    domain: str = "example.com"
    rss_urls: List[str] = []
    is_primary: bool = False
    enabled: bool = True

    def __init__(self):
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
        }

    async def search(self, query: str, client: httpx.AsyncClient, max_results: int = 5) -> List[Article]:
        """
        High-precision multi-channel search implementation:
        1. Queries Google News RSS scoped specifically to this domain.
        2. Queries source RSS feeds with multi-keyword validation.
        3. Returns standardized Article objects.
        """
        articles: List[Article] = []
        if not self.enabled or not query:
            return articles

        # Method 1: Google News RSS scoped to source domain
        try:
            scoped_articles = await self._search_via_domain_feed(query, client, max_results)
            articles.extend(scoped_articles)
        except Exception as e:
            logger.debug(f"[{self.name}] Scoped feed search error: {str(e)}")

        # Method 2: Check active RSS feeds if results < max_results
        if len(articles) < max_results and self.rss_urls:
            try:
                rss_articles = await self._search_direct_rss(query, client, max_results - len(articles))
                existing_urls = {a.url for a in articles}
                for a in rss_articles:
                    if a.url not in existing_urls:
                        articles.append(a)
            except Exception as e:
                logger.debug(f"[{self.name}] Direct RSS error: {str(e)}")

        return articles[:max_results]

    async def _search_via_domain_feed(self, query: str, client: httpx.AsyncClient, max_results: int) -> List[Article]:
        """Searches Google News RSS filtered by source domain and formatted keywords."""
        clean_q = f"site:{self.domain} {query}".strip()
        encoded_q = urllib.parse.quote(clean_q)
        hl = "ta" if "ta" in self.languages and len(self.languages) == 1 else "en-IN"
        gl = "IN"
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl={hl}&gl={gl}&ceid=IN:{hl}"

        response = await client.get(url, headers=self.headers, timeout=settings.REQUEST_TIMEOUT_SECONDS)
        if response.status_code != 200:
            return []

        feed = feedparser.parse(response.text)
        results: List[Article] = []

        for entry in feed.entries[:max_results]:
            title = getattr(entry, "title", "").strip()
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()

            link = getattr(entry, "link", "")
            pub_date = getattr(entry, "published", None) or getattr(entry, "updated", None)
            summary_raw = getattr(entry, "summary", "") or getattr(entry, "description", "")
            snippet = clean_html(summary_raw)
            if not snippet:
                snippet = title

            author = getattr(entry, "author", None)
            is_prim = self.is_primary
            src_type = SourceType.PRIMARY if is_prim else SourceType.INDEPENDENT

            article = Article(
                source=self.name,
                source_id=self.source_id,
                title=title,
                url=normalize_url(link),
                publication_date=pub_date,
                author=author,
                language="ta" if "ta" in self.languages else "en",
                summary=truncate_snippet(snippet),
                snippet=snippet,
                matched_claim=query,
                source_type=src_type
            )
            results.append(article)

        return results

    async def _search_direct_rss(self, query: str, client: httpx.AsyncClient, max_results: int) -> List[Article]:
        """Fetches direct source RSS feeds and matches against significant query keywords."""
        results: List[Article] = []
        raw_words = re.findall(r'[\u0B80-\u0BFF]+|[a-zA-Z0-9]+', query.lower())
        query_words = [w for w in raw_words if len(w) > 2 and w not in STOP_WORDS]
        if not query_words:
            query_words = [w for w in raw_words if len(w) > 2]

        min_matches_required = 2 if len(query_words) >= 2 else 1

        for feed_url in self.rss_urls[:2]:
            try:
                resp = await client.get(feed_url, headers=self.headers, timeout=settings.REQUEST_TIMEOUT_SECONDS)
                if resp.status_code != 200:
                    continue
                feed = feedparser.parse(resp.text)
                for entry in feed.entries:
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                    combined_text = f"{title} {summary}".lower()

                    match_count = sum(1 for w in query_words if w in combined_text)
                    if match_count >= min_matches_required:
                        link = getattr(entry, "link", "")
                        pub_date = getattr(entry, "published", None)
                        author = getattr(entry, "author", None)
                        snippet = clean_html(summary) or clean_text(title)

                        results.append(Article(
                            source=self.name,
                            source_id=self.source_id,
                            title=clean_text(title),
                            url=normalize_url(link),
                            publication_date=pub_date,
                            author=author,
                            language="ta" if "ta" in self.languages else "en",
                            summary=truncate_snippet(snippet),
                            snippet=snippet,
                            matched_claim=query,
                            source_type=SourceType.PRIMARY if self.is_primary else SourceType.INDEPENDENT
                        ))
                    if len(results) >= max_results:
                        break
            except Exception as e:
                logger.debug(f"Direct RSS fetch failed for {feed_url}: {str(e)}")

        return results

    async def fetch_article(self, url: str, client: httpx.AsyncClient) -> Optional[Article]:
        """Fetches full article page and extracts clean content and metadata."""
        is_safe, reason = is_safe_url(url)
        if not is_safe:
            logger.warning(f"Rejected unsafe URL: {url} ({reason})")
            return None

        try:
            resp = await client.get(url, headers=self.headers, timeout=settings.REQUEST_TIMEOUT_SECONDS, follow_redirects=True)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            metadata = self.extract_metadata(soup, url)
            content = self.extract_content(soup)

            return Article(
                source=self.name,
                source_id=self.source_id,
                title=metadata.get("title", ""),
                url=normalize_url(str(resp.url)),
                publication_date=metadata.get("publication_date"),
                author=metadata.get("author"),
                language=metadata.get("language", "en"),
                summary=truncate_snippet(content),
                snippet=content[:600],
                source_type=SourceType.PRIMARY if self.is_primary else SourceType.INDEPENDENT
            )
        except Exception as e:
            logger.error(f"[{self.name}] Failed to fetch article at {url}: {str(e)}")
            return None

    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = clean_text(og_title["content"])
        elif soup.title and soup.title.string:
            title = clean_text(soup.title.string)

        pub_date = None
        date_meta = soup.find("meta", property="article:published_time") or \
                    soup.find("meta", attrs={"name": "publish-date"}) or \
                    soup.find("meta", attrs={"name": "pubdate"}) or \
                    soup.find("time")
        if date_meta:
            pub_date = date_meta.get("content") or date_meta.get("datetime") or date_meta.get_text()
            if pub_date:
                pub_date = pub_date.strip()

        author = None
        author_meta = soup.find("meta", attrs={"name": "author"}) or \
                      soup.find("meta", property="article:author")
        if author_meta and author_meta.get("content"):
            author = clean_text(author_meta["content"])

        return {
            "title": title,
            "publication_date": pub_date,
            "author": author,
            "language": "ta" if "ta" in self.languages else "en"
        }

    def extract_content(self, soup: BeautifulSoup) -> str:
        article_tag = soup.find("article") or soup.find("div", class_=re.compile(r'article[-_]?body|story[-_]?content|post[-_]?content', re.I))
        if article_tag:
            paragraphs = article_tag.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        text_blocks = [p.get_text(separator=" ", strip=True) for p in paragraphs if len(p.get_text()) > 20]
        full_text = "\n".join(text_blocks)
        cleaned = remove_boilerplate(clean_text(full_text))
        return cleaned
