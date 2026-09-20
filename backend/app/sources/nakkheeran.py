"""
Nakkheeran Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class NakkheeranAdapter(BaseSourceAdapter):
    source_id = "nakkheeran"
    name = "Nakkheeran"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "medium"
    reliability = "medium"
    domain = "nakkheeran.in"
    rss_urls = [
        "https://www.nakkheeran.in/rss/all",
    ]
