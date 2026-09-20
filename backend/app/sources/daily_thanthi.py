"""
Daily Thanthi (Dina Thanthi) Source Adapter.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class DailyThanthiAdapter(BaseSourceAdapter):
    source_id = "daily_thanthi"
    name = "Daily Thanthi"
    languages = ["ta"]
    region = "Tamil Nadu"
    priority = "high"
    reliability = "medium"
    domain = "dailythanthi.com"
    rss_urls = [
        "https://www.dailythanthi.com/rss/all",
        "https://www.dailythanthi.com/rss/News/State",
    ]
