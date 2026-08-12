import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Dict

from app.core.config import settings
from app.services.vectorstore import get_collection

HEADERS = {"User-Agent": "Mozilla/5.0 (FactCheckBot/1.0; +https://example.com/bot)"}


async def fetch_rss(domain: str, feed_url: str) -> List[Dict]:
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        resp = await client.get(feed_url)
        resp.raise_for_status()
    parsed = feedparser.parse(resp.text)
    items = []
    for entry in parsed.entries:
        items.append(
            {
                "domain": domain,
                "outlet": settings.WHITELIST[domain]["name"],
                "lang": settings.WHITELIST[domain]["lang"],
                "headline": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "published": entry.get("published", datetime.now(timezone.utc).isoformat()),
            }
        )
    return items


async def scrape_homepage_headlines(domain: str, max_items: int = 20) -> List[Dict]:
    """
    Fallback for outlets without a reliable RSS feed (e.g. Daily Thanthi,
    Polimer News). Pulls headline links off the homepage. This is
    intentionally generic -- for production, replace the CSS selector
    per-outlet after inspecting their markup, since homepage structures
    change and a single generic selector will need tuning per site.
    """
    url = f"https://{domain}/"
    async with httpx.AsyncClient(timeout=15, headers=HEADERS, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    items = []
    seen = set()
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if not text or len(text) < 15:
            continue
        if href.startswith("/"):
            href = f"https://{domain}{href}"
        if domain not in href or href in seen:
            continue
        seen.add(href)
        items.append(
            {
                "domain": domain,
                "outlet": settings.WHITELIST[domain]["name"],
                "lang": settings.WHITELIST[domain]["lang"],
                "headline": text,
                "summary": "",
                "url": href,
                "published": datetime.now(timezone.utc).isoformat(),
            }
        )
        if len(items) >= max_items:
            break
    return items


async def ingest_all() -> int:
    """Pull fresh items from every whitelisted outlet and upsert into Chroma.
    Returns count of items indexed. Call this from the scheduler or a
    one-off `python -m app.services.ingest` run."""
    collection = get_collection()
    total = 0

    for domain, meta in settings.WHITELIST.items():
        try:
            if meta["rss"]:
                items = await fetch_rss(domain, meta["rss"])
            else:
                items = await scrape_homepage_headlines(domain)
        except Exception as e:
            print(f"[ingest] {domain} failed: {e}")
            continue

        if not items:
            continue

        docs = [f"{it['headline']} {it['summary']}".strip() for it in items]
        ids = [it["url"] for it in items]
        metadatas = [
            {
                "domain": it["domain"],
                "outlet": it["outlet"],
                "lang": it["lang"],
                "headline": it["headline"],
                "url": it["url"],
                "published": it["published"],
            }
            for it in items
        ]
        try:
            collection.upsert(documents=docs, ids=ids, metadatas=metadatas)
            total += len(docs)
        except Exception as e:
            print(f"[ingest] chroma upsert failed for {domain}: {e}")

    return total
