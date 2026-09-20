"""
Dinamalar Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class DinamalarAdapter(BaseSourceAdapter):
    source_id = "dinamalar"
    name = "Dinamalar"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "high"
    reliability = "medium"
    domain = "dinamalar.com"
    rss_urls = [
        "https://www.dinamalar.com/rss/tamil_news.xml",
        "https://www.dinamalar.com/rss/chennai_news.xml",
    ]
