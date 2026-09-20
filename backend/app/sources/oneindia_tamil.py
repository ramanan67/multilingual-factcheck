"""
OneIndia Tamil Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class OneIndiaTamilAdapter(BaseSourceAdapter):
    source_id = "oneindia_tamil"
    name = "OneIndia Tamil"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "medium"
    reliability = "medium"
    domain = "tamil.oneindia.com"
    rss_urls = [
        "https://tamil.oneindia.com/rss/tamil-news-fb.xml",
    ]
