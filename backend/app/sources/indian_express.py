"""
The Indian Express Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class IndianExpressAdapter(BaseSourceAdapter):
    source_id = "indian_express"
    name = "The Indian Express"
    languages = ["en"]
    region = "India"
    priority = "high"
    reliability = "high"
    domain = "indianexpress.com"
    rss_urls = [
        "https://indianexpress.com/feed/",
        "https://indianexpress.com/section/cities/chennai/feed/",
    ]
