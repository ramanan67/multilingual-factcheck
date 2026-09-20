"""
Dinamani Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class DinamaniAdapter(BaseSourceAdapter):
    source_id = "dinamani"
    name = "Dinamani"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "high"
    reliability = "medium-high"
    domain = "dinamani.com"
    rss_urls = [
        "https://www.dinamani.com/tamilnadu/rssfeed.xml",
        "https://www.dinamani.com/all-sections/rssfeed.xml",
    ]
