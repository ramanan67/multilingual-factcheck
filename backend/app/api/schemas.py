"""
Pydantic API Schemas for Requests and Responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.models import VerificationResult, SourceDefinition, SourceStatus


class NewsCheckRequest(BaseModel):
    """Payload for submitting a news claim or text for fact-checking."""
    text: str = Field(..., min_length=3, description="The news headline, claim, or complete text to verify")
    url: Optional[str] = Field(None, description="Optional news article URL")
    language: str = Field("auto", description="Preferred language: auto, en, ta")


class UrlCheckRequest(BaseModel):
    """Payload for verifying a direct news article URL."""
    url: str = Field(..., description="The news URL to fetch and verify")
    language: str = Field("auto", description="Preferred language")


class LatestNewsItem(BaseModel):
    """Real-time breaking news item."""
    title: str
    source: str
    source_id: str
    url: str
    publication_date: str
    snippet: str
    language: str
    category: str = "general"
    is_official: bool = False


class MediaVerificationResult(VerificationResult):
    """Verification result with multimodal extracted media metadata."""
    extracted_text: str = ""
    media_type: str = "image"
    ocr_confidence: float = 0.0


class TranslationRequest(BaseModel):
    """Payload for simple cross-lingual translation."""
    text: str = Field(..., min_length=1)
    target_lang: str = Field("ta", description="Target language: en or ta")


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    target_lang: str


class SourceToggleRequest(BaseModel):
    enabled: bool


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    app_name: str
