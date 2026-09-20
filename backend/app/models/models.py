"""
Data models and type definitions for News Truth Checker.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class VerdictType(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    MISLEADING = "MISLEADING"
    UNVERIFIED = "UNVERIFIED"


class LanguageType(str, Enum):
    EN = "en"
    TA = "ta"
    MIXED = "mixed"
    UNKNOWN = "unknown"
    AUTO = "auto"


class EvidencePolarity(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    MISLEADING_CONTEXT = "MISLEADING_CONTEXT"
    NEUTRAL = "NEUTRAL"


class SourceType(str, Enum):
    INDEPENDENT = "Independent"
    SYNDICATED = "Syndicated"
    PRIMARY = "Primary Source"


class ReliabilityTier(str, Enum):
    HIGH = "high"
    MEDIUM_HIGH = "medium-high"
    MEDIUM = "medium"
    LOW = "low"
    PRIMARY = "primary"


class SourceDefinition(BaseModel):
    """Definition of a news source in the registry."""
    id: str
    name: str
    languages: List[str]
    region: str
    priority: str = "medium"
    reliability: str = "medium"
    domain: str
    rss_urls: List[str] = Field(default_factory=list)
    enabled: bool = True
    is_primary: bool = False


class ExtractedEntities(BaseModel):
    """Structured entities extracted from the news claim."""
    persons: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    numbers: List[str] = Field(default_factory=list)
    event_keywords: List[str] = Field(default_factory=list)
    main_statement: str = ""
    polarity_negated: bool = False
    is_public_figure: bool = False
    is_sensational_claim: bool = False


class Article(BaseModel):
    """Collected article metadata and evidence analysis."""
    source: str
    source_id: str
    title: str
    url: str
    publication_date: Optional[str] = None
    author: Optional[str] = None
    language: str = "en"
    summary: str = ""
    snippet: str = ""
    matched_claim: str = ""
    relevance_score: float = 0.0
    evidence_score: float = 0.0
    polarity: EvidencePolarity = EvidencePolarity.NEUTRAL
    source_type: SourceType = SourceType.INDEPENDENT
    is_syndicated: bool = False
    wire_agency: Optional[str] = None
    is_outdated: bool = False
    date_discrepancy_note: Optional[str] = None


class SourceComparisonItem(BaseModel):
    """Row in the source comparison matrix."""
    source_name: str
    found: bool
    supports: bool
    contradicts: bool
    date: Optional[str] = None
    source_type: str
    reliability: str
    article_title: Optional[str] = None
    article_url: Optional[str] = None


class SourceStatus(BaseModel):
    """Live search status for a specific source."""
    source_name: str
    status: str  # "success", "error", "no_results"
    articles_found: int = 0
    latency_ms: float = 0.0
    error_message: Optional[str] = None


class VerificationStats(BaseModel):
    """Summary statistics for duplicate, syndication, and independence detection."""
    total_articles: int = 0
    independent_reports: int = 0
    syndicated_reports: int = 0
    primary_sources: int = 0
    sources_searched: int = 0
    sources_successful: int = 0


class VerificationResult(BaseModel):
    """Complete fact check and verification response."""
    id: str
    verdict: VerdictType
    verdict_display: str
    confidence: float
    confidence_display: str
    language: str
    claim: str
    original_text: Optional[str] = None
    url: Optional[str] = None
    reason: str
    detailed_explanation: str
    executive_summary: Optional[Dict[str, Any]] = None
    supporting_sources: List[str] = Field(default_factory=list)
    contradicting_sources: List[str] = Field(default_factory=list)
    primary_sources: List[str] = Field(default_factory=list)
    articles: List[Article] = Field(default_factory=list)
    comparison_table: List[SourceComparisonItem] = Field(default_factory=list)
    source_statuses: List[SourceStatus] = Field(default_factory=list)
    stats: VerificationStats = Field(default_factory=VerificationStats)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
