"""
Dedicated Fact-Checking Source Adapters.
Handles dedicated fact-checking organizations: BoomLive, Factly, Newschecker Tamil, and The Quint WebQoof.
"""

from backend.app.sources.base_source import BaseSourceAdapter


class BoomLiveAdapter(BaseSourceAdapter):
    """BoomLive Fact-Checking Organization (IFCN signatory)."""
    source_id = "boomlive"
    name = "BoomLive (Fact Check)"
    languages = ["en"]
    region = "India Fact Check"
    priority = "high"
    reliability = "primary"
    domain = "boomlive.in"
    rss_urls = [
        "https://www.boomlive.in/feed",
    ]


class FactlyAdapter(BaseSourceAdapter):
    """Factly Fact-Checking Organization (IFCN signatory)."""
    source_id = "factly"
    name = "Factly (Fact Check)"
    languages = ["en"]
    region = "India Fact Check"
    priority = "high"
    reliability = "primary"
    domain = "factly.in"
    rss_urls = [
        "https://factly.in/feed/",
    ]


class NewscheckerTamilAdapter(BaseSourceAdapter):
    """Newschecker Tamil Fact-Checking Portal (IFCN signatory)."""
    source_id = "newschecker_tamil"
    name = "Newschecker Tamil"
    languages = ["ta"]
    region = "Tamil Fact Check"
    priority = "high"
    reliability = "primary"
    domain = "newschecker.in/ta"
    rss_urls = [
        "https://newschecker.in/ta/feed/",
    ]


class TheQuintWebQoofAdapter(BaseSourceAdapter):
    """The Quint WebQoof Fact Check."""
    source_id = "the_quint"
    name = "The Quint (WebQoof Fact Check)"
    languages = ["en"]
    region = "India Fact Check"
    priority = "high"
    reliability = "primary"
    domain = "thequint.com"
    rss_urls = [
        "https://www.thequint.com/news/webqoof",
    ]
