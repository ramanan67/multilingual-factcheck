"""
Times of India Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class TimesOfIndiaAdapter(BaseSourceAdapter):
    source_id = "times_of_india"
    name = "Times of India"
    languages = ["en"]
    region = "India"
    priority = "high"
    reliability = "high"
    domain = "timesofindia.indiatimes.com"
    rss_urls = [
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://timesofindia.indiatimes.com/rssfeeds/2950623.cms", # Chennai
    ]
