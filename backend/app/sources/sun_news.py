"""
Sun News Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class SunNewsAdapter(BaseSourceAdapter):
    source_id = "sun_news"
    name = "Sun News"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "medium"
    reliability = "medium"
    domain = "sunnewstamil.com"
    rss_urls = [
        "https://sunnewstamil.com/feed/",
    ]
