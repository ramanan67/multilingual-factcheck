"""
Configuration Module for News Truth Checker.
Defines application settings, NLP scoring weights, and reliability tiers.
"""

from typing import Dict, List, Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings with environment override support."""
    
    APP_NAME: str = "Tamil & Multilingual News Truth Checker"
    APP_SUBTITLE: str = "Verify the news. See the evidence. Know why."
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # API Keys (Optional)
    NEWS_SEARCH_API_KEY: Optional[str] = None
    TRANSLATION_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Search & Crawling Limits
    MAX_ARTICLES_PER_SOURCE: int = 5
    MAX_TOTAL_ARTICLES: int = 40
    REQUEST_TIMEOUT_SECONDS: float = 10.0
    CONNECT_TIMEOUT_SECONDS: float = 4.0
    MAX_CONCURRENT_SEARCHES: int = 8
    CACHE_TTL_SECONDS: int = 1800  # 30 minutes

    # Database
    DATABASE_URL: str = "sqlite:///./truth_checker.db"

    # HTTP User Agent
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 (NewsVerificationBot/1.0)"
    )

    # NLP Similarity Weights (Configurable)
    SIMILARITY_WEIGHTS: Dict[str, float] = {
        "headline_similarity": 0.20,
        "claim_similarity": 0.30,
        "entity_similarity": 0.15,
        "date_similarity": 0.10,
        "location_similarity": 0.10,
        "keyword_similarity": 0.15,
    }

    # Verdict Confidence Thresholds
    CONFIDENCE_THRESHOLD_TRUE: float = 0.70
    CONFIDENCE_THRESHOLD_FALSE: float = 0.70
    CONFIDENCE_THRESHOLD_MISLEADING: float = 0.60
    MIN_INDEPENDENT_SOURCES_FOR_TRUE: int = 2

    # Reliability Tier Multipliers
    RELIABILITY_MULTIPLIERS: Dict[str, float] = {
        "high": 1.0,
        "medium-high": 0.85,
        "medium": 0.70,
        "low": 0.40,
        "primary": 1.25,
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
