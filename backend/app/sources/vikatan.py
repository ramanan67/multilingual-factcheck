"""
Vikatan Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class VikatanAdapter(BaseSourceAdapter):
    source_id = "vikatan"
    name = "Vikatan"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "medium"
    reliability = "medium-high"
    domain = "vikatan.com"
    rss_urls = [
        "https://www.vikatan.com/api/v1/collections/tamil-nadu-news.rss",
    ]
