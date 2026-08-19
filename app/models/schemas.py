from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class Verdict(str, Enum):
    VERIFIED = "Verified Real"
    UNVERIFIED = "Unverified / Potential Fake"
    REFUTED = "Directly Refuted"


class ClaimRequest(BaseModel):
    text: str
    url: Optional[str] = None


class EvidenceCard(BaseModel):
    outlet: str
    domain: str
    headline: str
    url: str
    published: Optional[str] = None
    stance: str          # "entailment" | "contradiction" | "neutral"
    matched_snippet: str
    similarity: float


class ClaimResponse(BaseModel):
    claim: str
    language_detected: str
    verdict: Verdict
    is_true: bool                # simple True/Fake flag the UI leads with
    note: str                    # one-line explanation, always shown
    matching_outlets: int
    threshold: int
    evidence: List[EvidenceCard]  # only populated when is_true is True
    candidates_considered: int  # how many articles were retrieved before filtering
    filtered_out: int           # how many were dropped as irrelevant (low similarity or NLI-neutral)


class MediaClaimResponse(ClaimResponse):
    extracted_text: str   # what OCR/frame-sampling actually read from the file
    media_type: str        # "image" | "video"
