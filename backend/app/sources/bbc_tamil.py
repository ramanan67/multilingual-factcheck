"""
BBC Tamil Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class BBCTamilAdapter(BaseSourceAdapter):
    source_id = "bbc_tamil"
    name = "BBC Tamil"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "high"
    reliability = "high"
    domain = "bbc.com/tamil"
    rss_urls = [
        "https://feeds.bbci.co.uk/tamil/rss.xml",
    ]
