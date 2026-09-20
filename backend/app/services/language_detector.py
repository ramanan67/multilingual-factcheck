"""
Language Detector for English, Tamil, and Mixed text.
"""

import re
from typing import Dict, Any, Tuple
from backend.app.models.models import LanguageType
from backend.app.utils.text_cleaner import clean_text


class LanguageDetector:
    """Detects if text is English, Tamil, Mixed Tamil-English, or Unknown."""

    # Tamil Unicode block: U+0B80 - U+0BFF
    TAMIL_REGEX = re.compile(r'[\u0B80-\u0BFF]')
    ENGLISH_REGEX = re.compile(r'[a-zA-Z]')

    @classmethod
    def detect(cls, text: str) -> Dict[str, Any]:
        """
        Analyzes character distribution and returns detected language, script ratios, and confidence.
        """
        cleaned = clean_text(text)
        if not cleaned:
            return {
                "language": LanguageType.UNKNOWN.value,
                "display_name": "Unknown",
                "tamil_ratio": 0.0,
                "english_ratio": 0.0,
                "confidence": 0.0
            }

        tamil_chars = len(cls.TAMIL_REGEX.findall(cleaned))
        english_chars = len(cls.ENGLISH_REGEX.findall(cleaned))
        total_alpha = tamil_chars + english_chars

        if total_alpha == 0:
            return {
                "language": LanguageType.UNKNOWN.value,
                "display_name": "Unknown",
                "tamil_ratio": 0.0,
                "english_ratio": 0.0,
                "confidence": 0.0
            }

        tamil_ratio = tamil_chars / total_alpha
        english_ratio = english_chars / total_alpha

        if tamil_ratio > 0.70:
            lang = LanguageType.TA.value
            display = "தமிழ் (Tamil)"
            confidence = min(0.99, 0.7 + (tamil_ratio * 0.3))
        elif english_ratio > 0.70:
            lang = LanguageType.EN.value
            display = "English"
            confidence = min(0.99, 0.7 + (english_ratio * 0.3))
        elif tamil_chars >= 3 and english_chars >= 3:
            lang = LanguageType.MIXED.value
            display = "Tamil + English (Mixed)"
            confidence = 0.85
        elif tamil_ratio > english_ratio:
            lang = LanguageType.TA.value
            display = "தமிழ் (Tamil)"
            confidence = 0.65
        else:
            lang = LanguageType.EN.value
            display = "English"
            confidence = 0.65

        return {
            "language": lang,
            "display_name": display,
            "tamil_ratio": round(tamil_ratio, 3),
            "english_ratio": round(english_ratio, 3),
            "confidence": round(confidence, 2)
        }
