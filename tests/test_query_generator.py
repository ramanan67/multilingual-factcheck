"""
Tests for Multilingual Query Generator.
"""

import pytest
from backend.app.services.query_generator import QueryGenerator
from backend.app.services.claim_extractor import ClaimExtractor


def test_query_generation_english():
    text = "Chennai schools holiday tomorrow heavy rain"
    entities = ClaimExtractor.extract(text)
    queries = QueryGenerator.generate_queries(text, entities, "en")
    
    assert "en" in queries
    assert len(queries["en"]) > 0
    assert any("chennai" in q.lower() for q in queries["en"])
    # Check that Tamil equivalents were also generated
    assert "ta" in queries
    assert len(queries["ta"]) > 0


def test_query_generation_tamil():
    text = "சென்னையில் நாளை பள்ளிகளுக்கு விடுமுறை"
    entities = ClaimExtractor.extract(text)
    queries = QueryGenerator.generate_queries(text, entities, "ta")
    
    assert "ta" in queries
    assert len(queries["ta"]) > 0
    # Check that English equivalents were also generated
    assert "en" in queries
    assert len(queries["en"]) > 0
