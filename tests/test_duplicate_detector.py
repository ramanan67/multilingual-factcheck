"""
Tests for Duplicate and Syndication Detection (ANI, PTI, IANS, etc.).
"""

import pytest
from backend.app.services.duplicate_detector import DuplicateDetector
from backend.app.models.models import Article, SourceType


def test_detect_wire_agency_syndication():
    articles = [
        Article(
            source="News18",
            source_id="news18",
            title="Tamil Nadu rains: School holiday in Chennai",
            url="https://news18.com/article1",
            snippet="(ANI) - Tamil Nadu government announced a holiday for schools in Chennai following heavy rains.",
            author="ANI",
            source_type=SourceType.INDEPENDENT,
            relevance_score=0.8
        ),
        Article(
            source="NDTV",
            source_id="ndtv",
            title="School holiday declared in Chennai due to rains: Report",
            url="https://ndtv.com/article2",
            snippet="Reported by PTI: District authorities declared school holiday tomorrow.",
            source_type=SourceType.INDEPENDENT,
            relevance_score=0.8
        ),
        Article(
            source="The Hindu",
            source_id="the_hindu",
            title="Chennai schools closed as rain batters coastal districts",
            url="https://thehindu.com/article3",
            snippet="Our Special Correspondent: Following heavy rainfall since morning, authorities ordered school closure.",
            source_type=SourceType.INDEPENDENT,
            relevance_score=0.85
        )
    ]
    
    deduped, stats = DuplicateDetector.analyze_articles(articles)
    
    assert stats.total_articles == 3
    assert stats.syndicated_reports >= 2  # ANI and PTI detected
    assert stats.independent_reports >= 1  # The Hindu original report
