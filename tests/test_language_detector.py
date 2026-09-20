"""
Tests for Language Detector (English, Tamil, Mixed, Unknown).
"""

import pytest
from backend.app.services.language_detector import LanguageDetector
from backend.app.models.models import LanguageType


def test_detect_english_headline():
    text = "Chennai schools will remain closed tomorrow due to heavy rain."
    result = LanguageDetector.detect(text)
    assert result["language"] == LanguageType.EN.value
    assert result["english_ratio"] > 0.8
    assert result["confidence"] >= 0.7


def test_detect_tamil_headline():
    text = "சென்னையில் கனமழை காரணமாக நாளை பள்ளிகளுக்கு விடுமுறை அறிவிக்கப்பட்டுள்ளது."
    result = LanguageDetector.detect(text)
    assert result["language"] == LanguageType.TA.value
    assert result["tamil_ratio"] > 0.8
    assert result["confidence"] >= 0.7


def test_detect_mixed_headline():
    text = "Chennai Heavy Rain: சென்னையில் நாளை பள்ளிகளுக்கு holiday அறிவிப்பு."
    result = LanguageDetector.detect(text)
    assert result["language"] in (LanguageType.MIXED.value, LanguageType.TA.value)


def test_detect_empty_or_numbers():
    text = "12345 67890 !@#$%"
    result = LanguageDetector.detect(text)
    assert result["language"] == LanguageType.UNKNOWN.value
