"""
News Tamil 24x7 Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class NewsTamil24x7Adapter(BaseSourceAdapter):
    source_id = "news_tamil24x7"
    name = "News Tamil 24x7"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "medium"
    reliability = "medium"
    domain = "newstamil24x7.tv"
    rss_urls = [
        "https://newstamil24x7.tv/feed/",
    ]
