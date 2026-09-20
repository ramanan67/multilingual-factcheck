"""
Puthiya Thalaimurai Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class PuthiyaThalaimuraiAdapter(BaseSourceAdapter):
    source_id = "puthiya_thalaimurai"
    name = "Puthiya Thalaimurai"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "high"
    reliability = "medium-high"
    domain = "puthiyathalaimurai.com"
    rss_urls = [
        "https://www.puthiyathalaimurai.com/rss/tamilnadu",
        "https://www.puthiyathalaimurai.com/rss/all",
    ]
