"""
Tests for Verdict Engine Logic across TRUE, FALSE, MISLEADING, UNVERIFIED, and Viral Rumors.
"""

import pytest
from backend.app.services.verdict_engine import VerdictEngine
from backend.app.services.claim_extractor import ClaimExtractor
from backend.app.models.models import (
    VerdictType, EvidencePolarity, SourceType, Article,
    SourceStatus, VerificationStats
)


def test_verdict_true_multiple_sources():
    claim = "Chennai schools closed tomorrow due to heavy rain"
    entities = ClaimExtractor.extract(claim)
    
    articles = [
        Article(
            source="The Hindu",
            source_id="the_hindu",
            title="Schools closed in Chennai due to heavy rain",
            url="https://thehindu.com/1",
            polarity=EvidencePolarity.SUPPORTS,
            relevance_score=0.85,
            source_type=SourceType.INDEPENDENT
        ),
        Article(
            source="Times of India",
            source_id="times_of_india",
            title="Holiday declared for Chennai schools tomorrow",
            url="https://timesofindia.indiatimes.com/2",
            polarity=EvidencePolarity.SUPPORTS,
            relevance_score=0.82,
            source_type=SourceType.INDEPENDENT
        ),
        Article(
            source="Puthiya Thalaimurai",
            source_id="puthiya_thalaimurai",
            title="சென்னையில் நாளை பள்ளிகளுக்கு விடுமுறை",
            url="https://puthiyathalaimurai.com/3",
            polarity=EvidencePolarity.SUPPORTS,
            relevance_score=0.80,
            source_type=SourceType.INDEPENDENT
        )
    ]
    
    stats = VerificationStats(total_articles=3, independent_reports=3, syndicated_reports=0, primary_sources=0)
    result = VerdictEngine.evaluate(claim, entities, articles, [], stats, "en")
    
    assert result.verdict == VerdictType.TRUE
    assert result.confidence >= 0.80
    assert "The Hindu" in result.supporting_sources


def test_verdict_false_contradicted_by_official_source():
    claim = "Tamil Nadu government announces free electricity for all factories"
    entities = ClaimExtractor.extract(claim)
    
    articles = [
        Article(
            source="Tamil Nadu Government (DIPR)",
            source_id="tn_gov_dipr",
            title="Fact Check: Fake news circulating regarding free electricity announcement",
            url="https://dipr.tn.gov.in/fact-check",
            polarity=EvidencePolarity.CONTRADICTS,
            relevance_score=0.90,
            source_type=SourceType.PRIMARY
        ),
        Article(
            source="The Hindu",
            source_id="the_hindu",
            title="Government denies social media rumor on power subsidy",
            url="https://thehindu.com/clarification",
            polarity=EvidencePolarity.CONTRADICTS,
            relevance_score=0.85,
            source_type=SourceType.INDEPENDENT
        )
    ]
    
    stats = VerificationStats(total_articles=2, independent_reports=1, syndicated_reports=0, primary_sources=1)
    result = VerdictEngine.evaluate(claim, entities, articles, [], stats, "en")
    
    assert result.verdict == VerdictType.FALSE
    assert result.confidence >= 0.85
    assert len(result.contradicting_sources) > 0


def test_verdict_false_viral_public_figure_hoax():
    claim = "Cm vijay is married actress trish at june 20"
    entities = ClaimExtractor.extract(claim)
    assert entities.is_sensational_claim is True or entities.is_public_figure is True

    articles = []
    statuses = [SourceStatus(source_name="The Hindu", status="no_results")]
    stats = VerificationStats(total_articles=0, independent_reports=0, syndicated_reports=0, primary_sources=0, sources_searched=20)

    result = VerdictEngine.evaluate(claim, entities, articles, statuses, stats, "en")

    assert result.verdict == VerdictType.FALSE
    assert "FAKE" in result.verdict_display
    assert result.confidence >= 0.90
    assert result.executive_summary is not None
    assert "Fabricated" in result.executive_summary["headline"]


def test_verdict_misleading_outdated_news():
    claim = "Severe cyclone alert issued for Chennai"
    entities = ClaimExtractor.extract(claim)
    
    articles = [
        Article(
            source="The Hindu",
            source_id="the_hindu",
            title="Cyclone alert for Chennai coastal areas",
            url="https://thehindu.com/old-cyclone",
            polarity=EvidencePolarity.MISLEADING_CONTEXT,
            relevance_score=0.75,
            is_outdated=True,
            date_discrepancy_note="Article was published in November 2023.",
            source_type=SourceType.INDEPENDENT
        )
    ]
    
    stats = VerificationStats(total_articles=1, independent_reports=1, syndicated_reports=0, primary_sources=0)
    result = VerdictEngine.evaluate(claim, entities, articles, [], stats, "en")
    
    assert result.verdict == VerdictType.MISLEADING
    assert "MISLEADING" in result.verdict_display


def test_verdict_unverified_absence_of_evidence():
    claim = "Random unconfirmed private announcement"
    entities = ClaimExtractor.extract(claim)
    
    # 0 matching articles found
    articles = []
    statuses = [SourceStatus(source_name="The Hindu", status="no_results")]
    stats = VerificationStats(total_articles=0, independent_reports=0, syndicated_reports=0, primary_sources=0, sources_searched=10)
    
    result = VerdictEngine.evaluate(claim, entities, articles, statuses, stats, "en")
    
    # Core Epistemic Rule: Must be UNVERIFIED, NOT FALSE!
    assert result.verdict == VerdictType.UNVERIFIED
    assert "UNVERIFIED" in result.verdict_display
    assert "Absence of reports is NOT proof" in result.reason
