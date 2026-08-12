import httpx
from typing import List, Dict
from app.core.config import settings

CSE_URL = "https://www.googleapis.com/customsearch/v1"


async def whitelisted_search(query: str, num: int = 10) -> List[Dict]:
    """
    Query Google Programmable Search Engine, restricted to the whitelist.

    IMPORTANT: create your CSE at https://programmablesearchengine.google.com/
    and under "Sites to search" add each of the 7 domains individually
    (one per line) rather than relying on OR'd site: operators in the query
    -- the CSE UI restriction is far more reliable than query-time site:
    filters, which can silently drop results when combined with OR across
    many domains.
    """
    if not settings.GOOGLE_CSE_API_KEY or not settings.GOOGLE_CSE_ENGINE_ID:
        raise RuntimeError(
            "GOOGLE_CSE_API_KEY / GOOGLE_CSE_ENGINE_ID not configured. "
            "See .env.example."
        )

    params = {
        "key": settings.GOOGLE_CSE_API_KEY,
        "cx": settings.GOOGLE_CSE_ENGINE_ID,
        "q": query,
        "num": min(num, 10),
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(CSE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("items", []):
        results.append(
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
                "domain": item.get("displayLink", ""),
            }
        )
    return results


def per_domain_fallback_queries(claim: str) -> List[str]:
    """
    If OR'd multi-site queries return sparse/empty results (a known CSE
    quirk), fall back to issuing one query per domain and merge client-side.
    """
    from app.core.config import settings as s

    return [f"site:{domain} {claim}" for domain in s.WHITELIST.keys()]
