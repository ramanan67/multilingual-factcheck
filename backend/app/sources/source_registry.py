"""
Central Source Registry for News Truth Checker.
Manages all news source adapters, dynamic enabling/disabling, priority lookups, and metadata.
"""

from typing import List, Dict, Optional, Type
from backend.app.models.models import SourceDefinition
from backend.app.sources.base_source import BaseSourceAdapter

# Import National / English sources
from backend.app.sources.the_hindu import TheHinduAdapter
from backend.app.sources.times_of_india import TimesOfIndiaAdapter
from backend.app.sources.bbc import BBCAdapter
from backend.app.sources.bbc_tamil import BBCTamilAdapter
from backend.app.sources.indian_express import IndianExpressAdapter
from backend.app.sources.hindustan_times import HindustanTimesAdapter
from backend.app.sources.ndtv import NDTVAdapter
from backend.app.sources.news18 import News18Adapter

# Import Tamil Nadu sources
from backend.app.sources.puthiya_thalaimurai import PuthiyaThalaimuraiAdapter
from backend.app.sources.polimer import PolimerNewsAdapter
from backend.app.sources.sun_news import SunNewsAdapter
from backend.app.sources.dinamalar import DinamalarAdapter
from backend.app.sources.dinamani import DinamaniAdapter
from backend.app.sources.daily_thanthi import DailyThanthiAdapter
from backend.app.sources.vikatan import VikatanAdapter
from backend.app.sources.nakkheeran import NakkheeranAdapter
from backend.app.sources.tamil_samayam import TamilSamayamAdapter
from backend.app.sources.oneindia_tamil import OneIndiaTamilAdapter
from backend.app.sources.news_tamil24x7 import NewsTamil24x7Adapter

# Import Fact-Checking & Primary Sources
from backend.app.sources.primary_sources import TNGovDIPRAdapter, PIBIndiaAdapter, IMDChennaiAdapter
from backend.app.sources.fact_checkers import (
    BoomLiveAdapter, FactlyAdapter, NewscheckerTamilAdapter, TheQuintWebQoofAdapter
)


class SourceRegistry:
    """Singleton registry holding all active source adapters."""

    def __init__(self):
        self._adapters: Dict[str, BaseSourceAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self):
        default_classes: List[Type[BaseSourceAdapter]] = [
            # High Priority English & National
            TheHinduAdapter,
            TimesOfIndiaAdapter,
            BBCAdapter,
            IndianExpressAdapter,
            HindustanTimesAdapter,
            NDTVAdapter,
            News18Adapter,
            # Tamil Nadu Sources
            BBCTamilAdapter,
            PuthiyaThalaimuraiAdapter,
            PolimerNewsAdapter,
            SunNewsAdapter,
            DinamalarAdapter,
            DinamaniAdapter,
            DailyThanthiAdapter,
            VikatanAdapter,
            NakkheeranAdapter,
            TamilSamayamAdapter,
            OneIndiaTamilAdapter,
            NewsTamil24x7Adapter,
            # Fact Checking Portals
            BoomLiveAdapter,
            FactlyAdapter,
            NewscheckerTamilAdapter,
            TheQuintWebQoofAdapter,
            # Primary Sources
            TNGovDIPRAdapter,
            PIBIndiaAdapter,
            IMDChennaiAdapter,
        ]

        for cls in default_classes:
            adapter = cls()
            self._adapters[adapter.source_id] = adapter

    def get_all_sources(self) -> List[SourceDefinition]:
        """Returns metadata list of all registered sources."""
        sources: List[SourceDefinition] = []
        for a in self._adapters.values():
            sources.append(SourceDefinition(
                id=a.source_id,
                name=a.name,
                languages=a.languages,
                region=a.region,
                priority=a.priority,
                reliability=a.reliability,
                domain=a.domain,
                rss_urls=a.rss_urls,
                enabled=a.enabled,
                is_primary=a.is_primary
            ))
        return sources

    def get_adapter(self, source_id: str) -> Optional[BaseSourceAdapter]:
        """Retrieves an adapter instance by source ID."""
        return self._adapters.get(source_id)

    def get_active_adapters(self, language: Optional[str] = None) -> List[BaseSourceAdapter]:
        """
        Retrieves all enabled source adapters, optionally prioritizing/filtering by language.
        If language is 'ta', returns Tamil adapters and primary adapters first, then high-priority English.
        """
        active = [a for a in self._adapters.values() if a.enabled]
        if not language or language in ("all", "auto"):
            return active

        lang = language.lower()
        if lang == "ta":
            return sorted(active, key=lambda a: (
                0 if a.is_primary else (1 if "ta" in a.languages else 2),
                0 if a.priority == "high" else 1
            ))
        elif lang == "en":
            return sorted(active, key=lambda a: (
                0 if a.is_primary else (1 if "en" in a.languages else 2),
                0 if a.priority == "high" else 1
            ))
        return active

    def toggle_source(self, source_id: str, enabled: bool) -> bool:
        """Enables or disables a source by ID."""
        if source_id in self._adapters:
            self._adapters[source_id].enabled = enabled
            return True
        return False

    def add_custom_source(self, source_data: dict) -> bool:
        """Dynamically registers a new custom news source."""
        source_id = source_data.get("id") or source_data.get("domain", "").replace(".", "_")
        if not source_id:
            return False

        class CustomAdapter(BaseSourceAdapter):
            pass

        CustomAdapter.source_id = source_id
        CustomAdapter.name = source_data.get("name", source_id)
        CustomAdapter.languages = source_data.get("languages", ["en"])
        CustomAdapter.region = source_data.get("region", "India")
        CustomAdapter.priority = source_data.get("priority", "medium")
        CustomAdapter.reliability = source_data.get("reliability", "medium")
        CustomAdapter.domain = source_data.get("domain", "")
        CustomAdapter.rss_urls = source_data.get("rss_urls", [])
        CustomAdapter.is_primary = source_data.get("is_primary", False)
        CustomAdapter.enabled = source_data.get("enabled", True)

        self._adapters[source_id] = CustomAdapter()
        return True


# Global registry instance
source_registry = SourceRegistry()
