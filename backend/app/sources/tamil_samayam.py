"""
Tamil Samayam Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class TamilSamayamAdapter(BaseSourceAdapter):
    source_id = "tamil_samayam"
    name = "Tamil Samayam"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "medium"
    reliability = "medium"
    domain = "tamil.samayam.com"
    rss_urls = [
        "https://tamil.samayam.com/rssfeedsdefault.cms",
        "https://tamil.samayam.com/tamil-nadu-news/articlelist/47743282.cms",
    ]
