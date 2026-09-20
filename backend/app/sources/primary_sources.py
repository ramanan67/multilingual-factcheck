"""
Primary and Official Government Source Adapters.
Handles Tamil Nadu Government DIPR, PIB India, and IMD Weather verification.
"""

from typing import List
from backend.app.sources.base_source import BaseSourceAdapter
from backend.app.models.models import SourceType


class TNGovDIPRAdapter(BaseSourceAdapter):
    """Tamil Nadu Directorate of Information and Public Relations (DIPR)."""
    source_id = "tn_gov_dipr"
    name = "Tamil Nadu Government (DIPR)"
    languages = ["ta", "en"]
    region = "Tamil Nadu Government"
    priority = "high"
    reliability = "primary"
    domain = "dipr.tn.gov.in"
    rss_urls = [
        "https://dipr.tn.gov.in/feed/",
    ]
    is_primary = True


class PIBIndiaAdapter(BaseSourceAdapter):
    """Press Information Bureau (PIB) India / PIB Fact Check."""
    source_id = "pib_india"
    name = "PIB India (Fact Check & Official Releases)"
    languages = ["en", "ta"]
    region = "Government of India"
    priority = "high"
    reliability = "primary"
    domain = "pib.gov.in"
    rss_urls = [
        "https://pib.gov.in/RssMain.aspx?ModId=6&LangId=1",
    ]
    is_primary = True


class IMDChennaiAdapter(BaseSourceAdapter):
    """India Meteorological Department (Regional Met Centre Chennai)."""
    source_id = "imd_chennai"
    name = "IMD Chennai (Regional Met Centre)"
    languages = ["en", "ta"]
    region = "Weather / Disaster Management"
    priority = "high"
    reliability = "primary"
    domain = "mausam.imd.gov.in"
    is_primary = True
