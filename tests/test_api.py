"""
Tests for FastAPI Endpoints (/health, /api/sources, /api/check, /api/latest-news, /api/history).
"""

import pytest
import io
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Tamil & Multilingual News Truth Checker" in data["app_name"]


def test_latest_news_endpoint():
    response = client.get("/api/latest-news?limit=5")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)


def test_list_sources_endpoint():
    response = client.get("/api/sources")
    assert response.status_code == 200
    sources = response.json()
    assert isinstance(sources, list)
    assert len(sources) >= 15
    source_names = [s["name"] for s in sources]
    assert "The Hindu" in source_names
    assert "Puthiya Thalaimurai" in source_names
    assert "Dinamalar" in source_names


def test_check_news_endpoint_validation():
    # Too short input
    response = client.post("/api/check", json={"text": "ab"})
    assert response.status_code == 422 or response.status_code == 400


def test_toggle_source_endpoint():
    response = client.post("/api/sources/the_hindu/toggle", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    # Restore
    response = client.post("/api/sources/the_hindu/toggle", json={"enabled": True})
    assert response.status_code == 200
    assert response.json()["enabled"] is True


def test_translate_endpoint():
    response = client.post("/api/translate", json={"text": "school holiday", "target_lang": "ta"})
    assert response.status_code == 200
    data = response.json()
    assert "பள்ளி" in data["translated_text"]
