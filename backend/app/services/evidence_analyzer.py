"""
Evidence Analysis Service.
Classifies article stance (SUPPORTS, CONTRADICTS, MISLEADING_CONTEXT, NEUTRAL)
and extracts factual corroboration or refutation across Tamil and English news.
"""

import re
from typing import List, Dict, Any, Tuple
from backend.app.models.models import Article, EvidencePolarity, ExtractedEntities
from backend.app.services.source_reliability import SourceReliabilityEvaluator
from backend.app.utils.text_cleaner import clean_text


# Contradiction and Debunking markers
DEBUNK_MARKERS_EN = [
    r'\b(fake news|fact check|debunked|false claim|hoax|rumour|rumor|misleading|clarifies|denies|refutes|baseless|untrue|no truth)\b',
    r'\b(no holiday declared|schools will function|classes will be held|normal schedule|not true|no announcement made|denies report)\b',
]

DEBUNK_MARKERS_TA = [
    r'(போலிச் செய்தி|வதந்தி|உண்மையல்ல|செய்தி தவறு|மறுப்பு|பள்ளிகள் வழக்கம் போல் இயங்கும்|விடுமுறை அறிவிக்கப்படவில்லை|அரசு விளக்கம்|வதந்திகளை நம்ப வேண்டாம்|உண்மையில்லை)',
]

SUPPORT_MARKERS_EN = [
    r'\b(announced|declared|ordered|holiday declared|schools closed|heavy rain|red alert|confirmed|approved|rescue|rescued|safe|safety|stranded|flood|floods|evacuated|action|reported|details|relief|immersion|visarjan|procession|idol|idols|vinayagar|ganesh|chaturthi|diwali|deepavali|bonus|pongal|festival|celebration|special buses)\b',
]

SUPPORT_MARKERS_TA = [
    r'(மீட்பு|மீட்கப்பட்டு|மீட்க|பாதுகாப்பாக|பத்திரமாக|வெள்ளத்தில் சிக்கிய|வெள்ளம்|தவித்த|உள்ளனர்|உறுதி|அறிவிப்பு|நடவடிக்கை|உத்தரவு|உதவி|துயர் துடைப்பு|செய்தி|தகவல்|பயணிகள்|விடுமுறை|அரசு|கனமழை|ரெட் அலர்ட்|கரைப்பு|கரைக்க|சிலை|சிலைகள்|விநாயகர்|ஊர்வலம்|பாதுகாப்பு|அனுமதி|போனஸ்|பொங்கல்|பரிசு|தீபாவளி|சிறப்பு பேருந்து)',
]


class EvidenceAnalyzer:
    """Analyzes stance of articles and evaluates corroborating vs refuting signals."""

    @classmethod
    def analyze_stance(
        cls, 
        claim_text: str, 
        entities: ExtractedEntities, 
        article: Article,
        match_details: Dict[str, Any]
    ) -> Article:
        """
        Determines if the article SUPPORTS, CONTRADICTS, has MISLEADING_CONTEXT, or is NEUTRAL.
        Computes evidence_score based on relevance, source reliability, and stance clarity.
        """
        relevance = match_details.get("relevance_score", 0.0)
        is_outdated = match_details.get("is_outdated", False)

        combined_text = clean_text(f"{article.title} {article.snippet}").lower()

        # Check if article is outdated / old news being recycled
        if is_outdated and relevance > 0.45:
            article.polarity = EvidencePolarity.MISLEADING_CONTEXT
            article.is_outdated = True
            article.date_discrepancy_note = match_details.get("discrepancy_note")
            multiplier = SourceReliabilityEvaluator.get_multiplier(article.source_id, article.source_type.value == "Primary Source")
            article.evidence_score = round(relevance * multiplier, 3)
            return article

        # Check for explicit debunk / contradiction signals
        has_debunk_en = any(re.search(p, combined_text, re.I) for p in DEBUNK_MARKERS_EN)
        has_debunk_ta = any(re.search(p, combined_text) for p in DEBUNK_MARKERS_TA)

        # Check for support / factual event signals
        has_support_en = any(re.search(p, combined_text, re.I) for p in SUPPORT_MARKERS_EN)
        has_support_ta = any(re.search(p, combined_text) for p in SUPPORT_MARKERS_TA)

        if relevance < 0.20:
            article.polarity = EvidencePolarity.NEUTRAL
        elif has_debunk_en or has_debunk_ta:
            if entities.polarity_negated:
                article.polarity = EvidencePolarity.SUPPORTS
            else:
                article.polarity = EvidencePolarity.CONTRADICTS
        elif has_support_en or has_support_ta or relevance >= 0.35:
            if entities.polarity_negated:
                article.polarity = EvidencePolarity.CONTRADICTS
            else:
                article.polarity = EvidencePolarity.SUPPORTS
        else:
            article.polarity = EvidencePolarity.NEUTRAL

        # Calculate final evidence score
        multiplier = SourceReliabilityEvaluator.get_multiplier(
            article.source_id, 
            article.source_type.value == "Primary Source"
        )
        article.evidence_score = round(relevance * multiplier, 3)
        return article
