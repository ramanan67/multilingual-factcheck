"""
NDTV Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class NDTVAdapter(BaseSourceAdapter):
    source_id = "ndtv"
    name = "NDTV"
    languages = ["en"]
    region = "India"
    priority = "high"
    reliability = "high"
    domain = "ndtv.com"
    rss_urls = [
        "https://feeds.feedburner.com/ndtvnews-top-stories",
        "https://feeds.feedburner.com/ndtvnews-india-news",
    ]
