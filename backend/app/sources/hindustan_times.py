"""
Hindustan Times Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class HindustanTimesAdapter(BaseSourceAdapter):
    source_id = "hindustan_times"
    name = "Hindustan Times"
    languages = ["en"]
    region = "India"
    priority = "high"
    reliability = "high"
    domain = "hindustantimes.com"
    rss_urls = [
        "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    ]
