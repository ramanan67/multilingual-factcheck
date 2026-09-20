"""
News18 Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class News18Adapter(BaseSourceAdapter):
    source_id = "news18"
    name = "News18"
    languages = ["en"]
    region = "India"
    priority = "medium"
    reliability = "medium-high"
    domain = "news18.com"
    rss_urls = [
        "https://www.news18.com/commonfeeds/v1/eng/rss/india.xml",
    ]
