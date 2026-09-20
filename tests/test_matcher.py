"""
Tests for Article Matcher and Multi-factor Scoring.
"""

import pytest
from datetime import datetime, timezone
from backend.app.services.article_matcher import ArticleMatcher
from backend.app.services.claim_extractor import ClaimExtractor
from backend.app.models.models import Article, SourceType


def test_matching_high_relevance_article():
    claim = "Chennai schools closed tomorrow due to heavy rain"
    entities = ClaimExtractor.extract(claim)
    
    article = Article(
        source="The Hindu",
        source_id="the_hindu",
        title="Heavy rain lashes Chennai: District Collector declares school holiday tomorrow",
        url="https://thehindu.com/news/cities/chennai/schools-holiday",
        snippet="District Collector announced holiday for all schools in Chennai tomorrow in view of continuous heavy rainfall.",
        publication_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        source_type=SourceType.INDEPENDENT
    )
    
    match_result = ArticleMatcher.match_article(claim, entities, article)
    assert match_result["relevance_score"] >= 0.50
    assert match_result["is_outdated"] is False


def test_matching_outdated_article():
    claim = "Chennai schools closed tomorrow"
    entities = ClaimExtractor.extract(claim)
    
    article = Article(
        source="Times of India",
        source_id="times_of_india",
        title="Chennai schools closed tomorrow due to rain",
        url="https://timesofindia.indiatimes.com/city/chennai/holiday-2023",
        snippet="School holiday declared in Chennai due to heavy rainfall across the state.",
        publication_date="2023-11-15",
        source_type=SourceType.INDEPENDENT
    )
    
    match_result = ArticleMatcher.match_article(claim, entities, article)
    assert match_result["is_outdated"] is True
    assert match_result["discrepancy_note"] is not None
