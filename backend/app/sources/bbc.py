"""
BBC News Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class BBCAdapter(BaseSourceAdapter):
    source_id = "bbc"
    name = "BBC"
    languages = ["en"]
    region = "International"
    priority = "high"
    reliability = "high"
    domain = "bbc.com"
    rss_urls = [
        "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ]
