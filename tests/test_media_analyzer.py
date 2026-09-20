"""
Tests for Multimodal Media Analyzer (Image OCR & Video Keyframe Processing).
"""

import pytest
import io
from PIL import Image, ImageDraw, ImageFont
from backend.app.services.media_analyzer import MediaAnalyzer


def create_sample_news_image(text: str = "Chennai Heavy Rain: School Holiday Tomorrow") -> bytes:
    """Creates a sample test image with clear text."""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw simple text
    draw.text((20, 80), text, fill=(0, 0, 0))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_preprocessing():
    import numpy as np
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    processed = MediaAnalyzer.preprocess_image(dummy_img)
    assert processed is not None
    assert len(processed.shape) == 2  # Grayscale enhanced


def test_extract_text_empty_bytes():
    res = MediaAnalyzer.extract_text_from_image_bytes(b"")
    assert res["success"] is False
    assert res["text"] == ""


def test_extract_text_from_synthetic_image():
    image_bytes = create_sample_news_image("Chennai Heavy Rain School Holiday")
    res = MediaAnalyzer.extract_text_from_image_bytes(image_bytes)
    # Should attempt OCR and return result dictionary structure
    assert "text" in res
    assert "lines" in res
    assert "confidence" in res
