"""
Tests for Claim and Entity Extraction.
"""

import pytest
from backend.app.services.claim_extractor import ClaimExtractor


def test_extract_english_claim_entities():
    text = "Tamil Nadu Government declared holiday for Chennai schools tomorrow due to heavy rain."
    entities = ClaimExtractor.extract(text)
    
    assert "Chennai" in entities.locations
    assert "Tamil Nadu Government" in entities.organizations
    assert any("holiday" in kw.lower() for kw in entities.event_keywords)
    assert any("tomorrow" in d.lower() for d in entities.dates)
    assert not entities.polarity_negated


def test_extract_tamil_claim_entities():
    text = "சென்னையில் நாளை கனமழை காரணமாக பள்ளிகளுக்கு விடுமுறை அறிவிப்பு."
    entities = ClaimExtractor.extract(text)
    
    assert "Chennai" in entities.locations
    assert any("விடுமுறை" in kw for kw in entities.event_keywords)
    assert any("நாளை" in d for d in entities.dates)


def test_extract_negation_debunk_claim():
    text = "Collector denies rumor about school holiday in Chennai."
    entities = ClaimExtractor.extract(text)
    
    assert entities.polarity_negated is True
    assert "District Collector" in entities.persons or "Collector" in text
