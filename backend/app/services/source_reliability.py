"""
Source Reliability Evaluation Service.
Calculates reliability weights based on domain, track record, and primary status.
"""

from typing import Dict
from backend.app.config import settings
from backend.app.models.models import ReliabilityTier


SOURCE_RELIABILITY_RATINGS: Dict[str, str] = {
    # Primary Sources
    "tn_gov_dipr": ReliabilityTier.PRIMARY.value,
    "pib_india": ReliabilityTier.PRIMARY.value,
    "imd_chennai": ReliabilityTier.PRIMARY.value,

    # High Reliability National / International
    "the_hindu": ReliabilityTier.HIGH.value,
    "times_of_india": ReliabilityTier.HIGH.value,
    "bbc": ReliabilityTier.HIGH.value,
    "bbc_tamil": ReliabilityTier.HIGH.value,
    "indian_express": ReliabilityTier.HIGH.value,
    "hindustan_times": ReliabilityTier.HIGH.value,
    "ndtv": ReliabilityTier.HIGH.value,

    # Medium-High Reliability
    "news18": ReliabilityTier.MEDIUM_HIGH.value,
    "puthiya_thalaimurai": ReliabilityTier.MEDIUM_HIGH.value,
    "dinamani": ReliabilityTier.MEDIUM_HIGH.value,
    "vikatan": ReliabilityTier.MEDIUM_HIGH.value,

    # Medium Reliability
    "polimer": ReliabilityTier.MEDIUM.value,
    "sun_news": ReliabilityTier.MEDIUM.value,
    "dinamalar": ReliabilityTier.MEDIUM.value,
    "daily_thanthi": ReliabilityTier.MEDIUM.value,
    "nakkheeran": ReliabilityTier.MEDIUM.value,
    "tamil_samayam": ReliabilityTier.MEDIUM.value,
    "oneindia_tamil": ReliabilityTier.MEDIUM.value,
    "news_tamil24x7": ReliabilityTier.MEDIUM.value,
}


class SourceReliabilityEvaluator:
    """Provides reliability score multipliers and tier classifications."""

    @staticmethod
    def get_tier(source_id: str, is_primary: bool = False) -> str:
        if is_primary:
            return ReliabilityTier.PRIMARY.value
        return SOURCE_RELIABILITY_RATINGS.get(source_id, ReliabilityTier.MEDIUM.value)

    @staticmethod
    def get_multiplier(source_id: str, is_primary: bool = False) -> float:
        tier = SourceReliabilityEvaluator.get_tier(source_id, is_primary)
        return settings.RELIABILITY_MULTIPLIERS.get(tier, 0.70)
