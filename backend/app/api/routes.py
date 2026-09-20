"""
REST API Route Endpoints for News Verification, Media OCR Check, Latest News, Source Management, and History.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, UploadFile, File, Form
from typing import List, Dict, Any, Optional
import httpx
import re
from pathlib import Path as FilePath
from datetime import datetime, timezone
from dateutil import parser as dt_parser

from backend.app.api.schemas import (
    NewsCheckRequest, UrlCheckRequest, TranslationRequest,
    TranslationResponse, SourceToggleRequest, HealthResponse,
    LatestNewsItem, MediaVerificationResult
)
from backend.app.models.models import (
    VerificationResult, SourceDefinition, SourceStatus, Article, EvidencePolarity
)
from backend.app.services.language_detector import LanguageDetector
from backend.app.services.claim_extractor import ClaimExtractor
from backend.app.services.query_generator import QueryGenerator, EN_TO_TA_KEYWORDS, TA_TO_EN_KEYWORDS
from backend.app.services.news_search import NewsSearchOrchestrator
from backend.app.services.article_parser import ArticleParser
from backend.app.services.article_matcher import ArticleMatcher
from backend.app.services.duplicate_detector import DuplicateDetector
from backend.app.services.evidence_analyzer import EvidenceAnalyzer
from backend.app.services.verdict_engine import VerdictEngine
from backend.app.services.media_analyzer import MediaAnalyzer
from backend.app.sources.source_registry import source_registry
from backend.app.utils.url_validator import is_safe_url, normalize_url
from backend.app.utils.text_cleaner import clean_text
from backend.app.utils.database import (
    save_verification, get_verifications, get_verification_by_id,
    delete_verification, clear_all_history
)
from backend.app.utils.logger import logger
from backend.app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint for monitoring uptime."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        app_name=settings.APP_NAME
    )


@router.get("/api/latest-news", response_model=List[LatestNewsItem], tags=["News Feed"])
async def get_latest_news(
    limit: int = Query(12, ge=1, le=30),
    category: Optional[str] = Query(None, description="Category filter: all, official, tamil, national")
):
    """
    Fetches real-time latest breaking news from official government portals,
    top Tamil Nadu outlets, and national organizations.
    Always sorted so newest news appears first with source diversity.
    """
    items = await NewsSearchOrchestrator.fetch_latest_breaking_news(limit=limit, category=category)
    return items


@router.post("/api/check", response_model=VerificationResult, tags=["Verification"])
async def check_news(payload: NewsCheckRequest):
    """
    Complete fact-checking pipeline for a news headline, claim, or text passage.
    """
    raw_text = clean_text(payload.text)
    if not raw_text or len(raw_text) < 3:
        raise HTTPException(status_code=400, detail="Please enter a valid news claim (at least 3 characters).")

    try:
        # Step 1: Language Detection
        lang_info = LanguageDetector.detect(raw_text)
        detected_lang = payload.language if payload.language != "auto" else lang_info["language"]

        # Step 2: Claim & Named Entity Extraction
        entities = ClaimExtractor.extract(raw_text)
        main_claim = entities.main_statement or raw_text

        # Step 3: Query Generation (Multilingual)
        queries = QueryGenerator.generate_queries(raw_text, entities, detected_lang)

        # Step 4: Multi-source Concurrent News Search
        raw_articles, source_statuses = await NewsSearchOrchestrator.search_all_sources(
            queries=queries, 
            language=detected_lang
        )

        # Check if the claim specifically mentions a historical past year
        has_historical_year = any(re.match(r'^(201\d|202[0-5])$', d) for d in entities.dates)
        now_dt = datetime.now(timezone.utc)

        # Step 5 & 6: Article Parsing, Matching & Strict Relevance + Recency Filtering
        matched_articles: List[Article] = []
        for art in raw_articles:
            match_details = ArticleMatcher.match_article(
                claim_text=main_claim, 
                entities=entities, 
                article=art
            )
            art.relevance_score = match_details["relevance_score"]
            art.matched_claim = main_claim

            # STRICT FILTER: Only retain articles with verified semantic relevance (>= 0.35)
            if art.relevance_score >= 0.35:
                # Step 8: Evidence Stance Analysis
                analyzed_art = EvidenceAnalyzer.analyze_stance(
                    claim_text=main_claim, 
                    entities=entities, 
                    article=art, 
                    match_details=match_details
                )

                # RECENCY FILTER: Exclude articles older than 60 days unless claim is historical or specifically debunking old news
                if analyzed_art.publication_date and not has_historical_year:
                    try:
                        pub_dt = dt_parser.parse(str(analyzed_art.publication_date), fuzzy=True)
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                        age_days = (now_dt - pub_dt).days
                        if age_days > 60 and analyzed_art.polarity != EvidencePolarity.MISLEADING_CONTEXT:
                            # Skip ancient articles that are irrelevant to current claims
                            continue
                    except Exception:
                        pass

                matched_articles.append(analyzed_art)

        # Update source_statuses: mark as success only if relevant articles were retrieved
        relevant_source_names = {a.source for a in matched_articles}
        for st in source_statuses:
            if st.source_name not in relevant_source_names:
                st.status = "no_results"
                st.articles_found = 0

        # Sort by relevance score and recency descending
        matched_articles.sort(key=lambda a: (a.relevance_score, a.publication_date or ""), reverse=True)

        # Step 7: Duplicate and Syndication Detection
        deduped_articles, stats = DuplicateDetector.analyze_articles(matched_articles)

        # Step 9: Verdict Calculation & Plain-Language Explanation
        result = VerdictEngine.evaluate(
            claim=main_claim,
            entities=entities,
            articles=deduped_articles,
            source_statuses=source_statuses,
            stats=stats,
            language=detected_lang,
            original_text=raw_text,
            url=payload.url or ""
        )

        # Step 10: Save to History DB
        try:
            save_verification(result.model_dump())
        except Exception as db_err:
            logger.error(f"Failed to save verification to database: {str(db_err)}")

        return result

    except Exception as e:
        logger.error(f"Error processing news verification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/api/check-media", response_model=MediaVerificationResult, tags=["Verification"])
async def check_media(
    file: UploadFile = File(..., description="Uploaded image (screenshot/poster) or video file"),
    language: str = Form("auto", description="Preferred language")
):
    """
    Extracts text and claims from uploaded screenshots, images, or video frames using OCR,
    and runs the full multi-source fact-checking verification engine.
    """
    filename = file.filename or "media_upload"
    ext = FilePath(filename).suffix.lower()
    
    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
    video_extensions = {".mp4", ".webm", ".avi", ".mov", ".mkv"}

    contents = await file.read()
    if not contents or len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extracted_text = ""
    ocr_confidence = 0.0
    media_type = "image"

    if ext in video_extensions:
        media_type = "video"
        media_res = MediaAnalyzer.extract_text_from_video_bytes(contents, filename)
        if not media_res.get("success"):
            raise HTTPException(
                status_code=400, 
                detail=f"Could not extract readable news text from video: {media_res.get('error', 'No text overlay detected')}"
            )
        extracted_text = media_res["text"]
        ocr_confidence = 0.80
    else:
        # Default to image
        media_type = "image"
        media_res = MediaAnalyzer.extract_text_from_image_bytes(contents)
        if not media_res.get("success"):
            raise HTTPException(
                status_code=400, 
                detail=f"Could not extract readable text from image: {media_res.get('error', 'No text detected in screenshot')}"
            )
        extracted_text = media_res["text"]
        ocr_confidence = media_res.get("confidence", 0.85)

    if not extracted_text or len(extracted_text.strip()) < 3:
        raise HTTPException(status_code=400, detail="No readable text or news headline found in uploaded media.")

    # Run verification pipeline on extracted OCR text
    verification = await check_news(NewsCheckRequest(
        text=extracted_text,
        url=None,
        language=language
    ))

    # Convert to MediaVerificationResult
    res_dict = verification.model_dump()
    res_dict["extracted_text"] = extracted_text
    res_dict["media_type"] = media_type
    res_dict["ocr_confidence"] = ocr_confidence

    return MediaVerificationResult(**res_dict)


@router.post("/api/check-url", response_model=VerificationResult, tags=["Verification"])
async def check_url(payload: UrlCheckRequest):
    """
    Fetches an article URL with SSRF protection, extracts its text, and verifies its factual accuracy.
    """
    is_safe, error_reason = is_safe_url(payload.url)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"Unsafe URL provided: {error_reason}")

    try:
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = await client.get(
                payload.url, 
                headers={"User-Agent": settings.USER_AGENT}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Unable to fetch URL (HTTP status {resp.status_code})")

            parsed = ArticleParser.parse_article_html(resp.text, payload.url)
            text_to_verify = parsed.get("title") or parsed.get("snippet") or parsed.get("full_text")
            if not text_to_verify:
                raise HTTPException(status_code=400, detail="Could not extract readable article content from URL.")

            return await check_news(NewsCheckRequest(
                text=text_to_verify,
                url=payload.url,
                language=payload.language
            ))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching URL {payload.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking URL: {str(e)}")


@router.get("/api/sources", response_model=List[SourceDefinition], tags=["Sources"])
async def list_sources():
    """Returns metadata for all registered news source adapters."""
    return source_registry.get_all_sources()


@router.post("/api/sources/{source_id}/toggle", tags=["Sources"])
async def toggle_source(source_id: str, payload: SourceToggleRequest):
    """Enables or disables a specific news source by ID."""
    success = source_registry.toggle_source(source_id, payload.enabled)
    if not success:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")
    return {"source_id": source_id, "enabled": payload.enabled, "status": "updated"}


@router.get("/api/search-status", response_model=List[SourceStatus], tags=["Sources"])
async def search_status():
    """Returns sample connectivity check for active sources."""
    sources = source_registry.get_all_sources()
    statuses = []
    for s in sources:
        statuses.append(SourceStatus(
            source_name=s.name,
            status="available" if s.enabled else "disabled",
            articles_found=0,
            latency_ms=0.0,
            error_message=None if s.enabled else "Source is currently disabled"
        ))
    return statuses


@router.get("/api/history", response_model=List[Dict[str, Any]], tags=["History"])
async def list_history(limit: int = Query(20, ge=1, le=100)):
    """Retrieves recent verification history from SQLite database."""
    return get_verifications(limit=limit)


@router.get("/api/history/{verification_id}", tags=["History"])
async def get_history_item(verification_id: str = Path(...)):
    """Retrieves a single historical fact check record by ID."""
    item = get_verification_by_id(verification_id)
    if not item:
        raise HTTPException(status_code=404, detail="Verification record not found.")
    return item


@router.delete("/api/history/{verification_id}", tags=["History"])
async def delete_history_item(verification_id: str = Path(...)):
    """Deletes a single historical fact check record."""
    success = delete_verification(verification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found.")
    return {"deleted": True, "id": verification_id}


@router.delete("/api/history", tags=["History"])
async def clear_history():
    """Clears all stored verification records."""
    clear_all_history()
    return {"cleared": True}


@router.post("/api/translate", response_model=TranslationResponse, tags=["Multilingual"])
async def translate_text(payload: TranslationRequest):
    """Translates key terms and news claims between English and Tamil."""
    text = clean_text(payload.text)
    target = payload.target_lang.lower()
    
    if target == "ta":
        words = text.split()
        translated_words = [EN_TO_TA_KEYWORDS.get(w.lower(), w) for w in words]
        result_text = " ".join(translated_words)
    else:
        words = text.split()
        translated_words = [TA_TO_EN_KEYWORDS.get(w, w) for w in words]
        result_text = " ".join(translated_words)

    return TranslationResponse(
        original_text=text,
        translated_text=result_text,
        target_lang=target
    )
