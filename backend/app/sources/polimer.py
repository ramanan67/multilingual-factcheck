"""
Polimer News Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class PolimerNewsAdapter(BaseSourceAdapter):
    source_id = "polimer"
    name = "Polimer News"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "medium"
    reliability = "medium"
    domain = "polimernews.com"
    rss_urls = [
        "https://polimernews.com/rss",
    ]
