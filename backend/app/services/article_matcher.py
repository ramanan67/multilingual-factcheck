"""
Article Matching and Semantic Similarity Engine.
Implements multi-factor relevance scoring combining Headline, Claim, Entity, Date, Location, and Keywords.
Enforces strict semantic relevance floors to eliminate off-topic/irrelevant articles.
"""

import re
import math
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from dateutil import parser as date_parser

from backend.app.models.models import Article, ExtractedEntities
from backend.app.config import settings
from backend.app.utils.text_cleaner import clean_text, tokenize_words


# Common English & Tamil news synonym sets
SYNONYM_GROUPS = [
    {"school", "schools", "schooling", "பள்ளி", "பள்ளிகள்", "பள்ளிகளுக்கு"},
    {"college", "colleges", "university", "universities", "கல்லூரி", "கல்லூரிகள்"},
    {"holiday", "closed", "closure", "shut", "shutdown", "விடுமுறை", "இயங்காது"},
    {"rain", "rainfall", "rains", "heavy rain", "downpour", "மழை", "கனமழை", "மழையளவு"},
    {"cyclone", "storm", "depression", "புயல்", "சூறாவளி"},
    {"flood", "floods", "inundation", "waterlogging", "வெள்ளம்", "வெள்ளத்தில்", "நீர் தேக்கம்"},
    {"government", "govt", "administration", "authorities", "அரசு", "நிர்வாகம்"},
    {"announcement", "declares", "declared", "announced", "orders", "ordered", "அறிவிப்பு", "உத்தரவு"},
    {"free bus", "bus travel", "fare free", "இலவச பேருந்து", "இலவச பயணம்"},
    {"electricity", "power", "subsidy", "மின்சாரம்", "இலவச மின்சாரம்"},
    {"nepal", "nepalese", "kathmandu", "நேபாள", "நேபாளம்", "நேபாளத்தில்"},
    {"rescue", "rescued", "safely", "safe", "evacuated", "மீட்கப்பட்டு", "மீட்பு", "பத்திரமாக", "பாதுகாப்பாக"},
    {"stranded", "trapped", "stuck", "சிக்கிய", "தவித்த"},
    {"tamils", "pilgrims", "tourists", "passengers", "தமிழர்கள்", "பயணிகள்", "தமிழ்நாட்டு பயணிகள்"},
    {"tomorrow", "நாளை"},
    {"today", "இன்று"},
    {"vinayagar", "vinayaka", "ganesh", "ganesha", "விநாயகர்", "விநாயக", "விநாயகர் சதுர்த்தி", "ganesh chaturthi"},
    {"idol", "idols", "statue", "statues", "சிலை", "சிலைகள்"},
    {"immersion", "immersed", "visarjan", "கரைப்பு", "கரைக்க", "கரைக்கப்பட்டன", "கரைக்கப்பட்டது"},
    {"procession", "rally", "processions", "ஊர்வலம்", "ஊர்வலங்கள்"},
    {"diwali", "deepavali", "தீபாவளி"},
    {"bonus", "incentive", "allowance", "போனஸ்", "ஊக்கத்தொகை", "அகவிலைப்படி", "da hike"},
    {"pongal", "பொங்கல்"},
    {"gift", "package", "hampers", "பரிசு", "பரிசுத்தொகுப்பு"},
    {"special buses", "bus service", "போக்குவரத்து", "சிறப்பு பேருந்துகள்", "பேருந்துகள்"},
]

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "with", "by", "from",
    "is", "was", "are", "were", "be", "been", "being", "have", "has", "had",
    "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "this", "that", "these", "those", "due", "because"
}


def stem_token(token: str) -> str:
    """Basic rule-based suffix normalization for English tokens."""
    t = token.lower()
    if len(t) > 4:
        if t.endswith("ing"):
            return t[:-3]
        if t.endswith("ed") or t.endswith("es"):
            return t[:-2]
        if t.endswith("s") and not t.endswith("ss"):
            return t[:-1]
    return t


def compute_jaccard_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Computes exact Jaccard word token overlap."""
    if not tokens_a or not tokens_b:
        return 0.0
    set_a = {w for w in tokens_a if w not in STOP_WORDS}
    set_b = {w for w in tokens_b if w not in STOP_WORDS}
    if not set_a or not set_b:
        set_a = set(tokens_a)
        set_b = set(tokens_b)
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / float(union) if union > 0 else 0.0


def compute_stemmed_jaccard(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Computes Jaccard overlap expanding synonyms and word stems."""
    if not tokens_a or not tokens_b:
        return 0.0

    stems_a = {stem_token(t) for t in tokens_a if t not in STOP_WORDS}
    stems_b = {stem_token(t) for t in tokens_b if t not in STOP_WORDS}
    if not stems_a or not stems_b:
        stems_a = {stem_token(t) for t in tokens_a}
        stems_b = {stem_token(t) for t in tokens_b}

    expanded_a = set(stems_a)
    for t in stems_a:
        for group in SYNONYM_GROUPS:
            if t in group or any(stem_token(g) == t for g in group):
                expanded_a.update(stem_token(g) for g in group)

    expanded_b = set(stems_b)
    for t in stems_b:
        for group in SYNONYM_GROUPS:
            if t in group or any(stem_token(g) == t for g in group):
                expanded_b.update(stem_token(g) for g in group)

    intersection = len(expanded_a.intersection(expanded_b))
    union = len(expanded_a.union(expanded_b))
    return float(intersection) / float(union) if union > 0 else 0.0


def compute_ngram_similarity(text_a: str, text_b: str, n: int = 3) -> float:
    """Computes character n-gram overlap for Tamil and English phrases."""
    if not text_a or not text_b:
        return 0.0
    a = text_a.lower().replace(" ", "")
    b = text_b.lower().replace(" ", "")
    if len(a) < n or len(b) < n:
        return 1.0 if a == b else 0.0
    
    ngrams_a = set(a[i:i+n] for i in range(len(a) - n + 1))
    ngrams_b = set(b[i:i+n] for i in range(len(b) - n + 1))
    
    intersection = len(ngrams_a.intersection(ngrams_b))
    union = len(ngrams_a.union(ngrams_b))
    return float(intersection) / float(union) if union > 0 else 0.0


class ArticleMatcher:
    """Evaluates multi-factor semantic and contextual similarity between claims and collected articles."""

    @classmethod
    def match_article(
        cls, 
        claim_text: str, 
        entities: ExtractedEntities, 
        article: Article
    ) -> Dict[str, Any]:
        """
        Computes composite relevance score and analyzes date discrepancy.
        Enforces strict semantic relevance floors.
        """
        claim_clean = clean_text(claim_text).lower()
        title_clean = clean_text(article.title).lower()
        snippet_clean = clean_text(f"{article.title} {article.snippet}").lower()

        claim_tokens = tokenize_words(claim_clean)
        title_tokens = tokenize_words(title_clean)
        snippet_tokens = tokenize_words(snippet_clean)

        # 1. Headline Similarity (20%)
        headline_jaccard = compute_stemmed_jaccard(claim_tokens, title_tokens)
        headline_ngram = compute_ngram_similarity(claim_clean, title_clean, n=3)
        headline_similarity = (headline_jaccard * 0.6) + (headline_ngram * 0.4)

        # 2. Claim Similarity against full snippet (30%)
        claim_jaccard = compute_stemmed_jaccard(claim_tokens, snippet_tokens)
        claim_ngram = compute_ngram_similarity(claim_clean, snippet_clean, n=3)
        claim_similarity = (claim_jaccard * 0.6) + (claim_ngram * 0.4)

        # 3. Entity Similarity (15%)
        entity_score = 0.0
        target_entities = entities.persons + entities.organizations + entities.numbers
        if target_entities:
            matched_ent = sum(1 for e in target_entities if e.lower() in snippet_clean)
            entity_score = matched_ent / len(target_entities)
        else:
            entity_score = max(claim_jaccard, headline_jaccard)

        # 4. Location Similarity (10%)
        location_score = 1.0
        if entities.locations:
            matched_loc = 0
            for l in entities.locations:
                loc_lower = l.lower()
                if loc_lower in snippet_clean:
                    matched_loc += 1
                else:
                    for grp in SYNONYM_GROUPS:
                        if loc_lower in grp and any(g in snippet_clean for g in grp):
                            matched_loc += 1
                            break
            location_score = 1.0 if matched_loc > 0 else 0.2

        # 5. Keyword Similarity (15%)
        keyword_score = 0.0
        if entities.event_keywords:
            matched_kw = 0
            for kw in entities.event_keywords:
                kw_lower = kw.lower()
                if kw_lower in snippet_clean:
                    matched_kw += 1
                else:
                    for grp in SYNONYM_GROUPS:
                        if kw_lower in grp and any(g in snippet_clean for g in grp):
                            matched_kw += 1
                            break
            keyword_score = min(1.0, matched_kw / len(entities.event_keywords))
        else:
            keyword_score = headline_similarity

        # 6. Date Similarity (10%)
        date_score = 1.0
        is_outdated = False
        discrepancy_note = None

        if article.publication_date:
            try:
                pub_dt = date_parser.parse(str(article.publication_date), fuzzy=True)
                now_dt = datetime.now(timezone.utc)
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                age_days = (now_dt - pub_dt).days
                if age_days > 60:
                    is_outdated = True
                    date_score = max(0.1, 1.0 - (age_days / 365.0))
                    discrepancy_note = f"Article was published {pub_dt.strftime('%B %Y')} (older than 60 days). May be outdated or recycled news."
                else:
                    date_score = 1.0
            except Exception:
                date_score = 0.8

        # --- STRICT SEMANTIC RELEVANCE FLOOR ---
        if (headline_similarity < 0.10 and claim_similarity < 0.12 and keyword_score == 0):
            return {
                "relevance_score": 0.0,
                "headline_similarity": round(headline_similarity, 3),
                "claim_similarity": round(claim_similarity, 3),
                "entity_score": 0.0,
                "location_score": 0.0,
                "keyword_score": 0.0,
                "date_score": round(date_score, 3),
                "is_outdated": False,
                "discrepancy_note": None
            }

        # Weighted calculation
        weights = settings.SIMILARITY_WEIGHTS
        composite_score = (
            (headline_similarity * weights.get("headline_similarity", 0.20)) +
            (claim_similarity * weights.get("claim_similarity", 0.30)) +
            (entity_score * weights.get("entity_similarity", 0.15)) +
            (date_score * weights.get("date_similarity", 0.10)) +
            (location_score * weights.get("location_similarity", 0.10)) +
            (keyword_score * weights.get("keyword_similarity", 0.15))
        )

        composite_score = min(1.0, max(0.0, composite_score))

        return {
            "relevance_score": round(composite_score, 3),
            "headline_similarity": round(headline_similarity, 3),
            "claim_similarity": round(claim_similarity, 3),
            "entity_score": round(entity_score, 3),
            "location_score": round(location_score, 3),
            "keyword_score": round(keyword_score, 3),
            "date_score": round(date_score, 3),
            "is_outdated": is_outdated,
            "discrepancy_note": discrepancy_note
        }
