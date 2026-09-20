"""
The Hindu Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class TheHinduAdapter(BaseSourceAdapter):
    source_id = "the_hindu"
    name = "The Hindu"
    languages = ["en"]
    region = "India"
    priority = "high"
    reliability = "high"
    domain = "thehindu.com"
    rss_urls = [
        "https://www.thehindu.com/news/national/feeder/default.rss",
        "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
        "https://www.thehindu.com/news/cities/chennai/feeder/default.rss",
    ]
