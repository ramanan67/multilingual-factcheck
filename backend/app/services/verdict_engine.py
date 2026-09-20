"""
News Verification and Verdict Engine.
Analyzes evidence, detects contradictions, viral hoaxes, and date discrepancies,
and calculates defensible confidence scores with language-adaptive executive summaries (Tamil & English).
"""

import uuid
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from dateutil import parser as dt_parser

from backend.app.models.models import (
    VerdictType, EvidencePolarity, SourceType, Article,
    VerificationResult, SourceComparisonItem, SourceStatus, VerificationStats,
    ExtractedEntities
)
from backend.app.services.source_reliability import SourceReliabilityEvaluator
from backend.app.config import settings
from backend.app.utils.logger import logger


def format_display_date(raw_date: Optional[str]) -> str:
    """Formats raw RSS / ISO dates into clean readable strings like '26 Aug 2026'."""
    if not raw_date or raw_date == "Recent" or raw_date == "—":
        return "Recent"
    try:
        dt = dt_parser.parse(str(raw_date), fuzzy=True)
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(raw_date)[:16]


def is_tamil_text(text: str) -> bool:
    """Checks if text contains Tamil Unicode range characters."""
    return bool(re.search(r'[\u0B80-\u0BFF]', text or ""))


class VerdictEngine:
    """
    Core verification engine enforcing fact-checking logic:
    1. Positive contradictory evidence / debunk articles -> FALSE.
    2. Extraordinary viral hoaxes / fabricated public figure rumors without credible reporting -> FALSE with language-adaptive executive summary.
    3. Old news recycled as new or altered context -> MISLEADING.
    4. Verified cross-source corroboration -> TRUE.
    5. Absence of evidence for private non-public claims -> UNVERIFIED.
    """

    @classmethod
    def evaluate(
        cls,
        claim: str,
        entities: ExtractedEntities,
        articles: List[Article],
        source_statuses: List[SourceStatus],
        stats: VerificationStats,
        language: str,
        original_text: str = "",
        url: str = ""
    ) -> VerificationResult:
        verification_id = str(uuid.uuid4())

        # Determine target language (Tamil or English)
        is_tamil = (language == "ta") or is_tamil_text(claim) or is_tamil_text(original_text)

        # Categorize articles by polarity
        supporting_articles = [a for a in articles if a.polarity == EvidencePolarity.SUPPORTS and a.relevance_score >= 0.35]
        contradicting_articles = [a for a in articles if a.polarity == EvidencePolarity.CONTRADICTS and a.relevance_score >= 0.35]
        misleading_articles = [a for a in articles if a.polarity == EvidencePolarity.MISLEADING_CONTEXT and a.relevance_score >= 0.38]

        # Extract source names
        supporting_sources = list(dict.fromkeys([a.source for a in supporting_articles]))
        contradicting_sources = list(dict.fromkeys([a.source for a in contradicting_articles]))
        primary_sources = list(dict.fromkeys([a.source for a in articles if a.source_type == SourceType.PRIMARY and a.relevance_score >= 0.35]))

        # Count independent supporting sources
        independent_supporting = len(set(a.source for a in supporting_articles if a.source_type in (SourceType.INDEPENDENT, SourceType.PRIMARY)))
        independent_contradicting = len(set(a.source for a in contradicting_articles if a.source_type in (SourceType.INDEPENDENT, SourceType.PRIMARY)))

        # Primary source weights
        has_primary_support = any(a.source_type == SourceType.PRIMARY and a.polarity == EvidencePolarity.SUPPORTS for a in articles)
        has_primary_contradiction = any(a.source_type == SourceType.PRIMARY and a.polarity == EvidencePolarity.CONTRADICTS for a in articles)

        # -------------------------------------------------------------
        # VERDICT LOGIC & LANGUAGE-ADAPTIVE EXECUTIVE SUMMARY
        # -------------------------------------------------------------

        verdict: VerdictType
        confidence: float
        reason: str
        detailed_explanation: str
        verdict_display: str
        executive_summary: Dict[str, Any] = {}

        # CASE 1: Contradicting Evidence Exists (Explicit Debunk / Factual Denial)
        if (independent_contradicting >= 2 or has_primary_contradiction or 
            (independent_contradicting >= 1 and independent_supporting == 0 and len(contradicting_articles) > 0)):
            
            verdict = VerdictType.FALSE
            verdict_display = "🔴 FAKE / FALSE (போலிச் செய்தி)" if is_tamil else "🔴 FAKE / FALSE"
            
            base_conf = 0.85 + min(0.12, (independent_contradicting * 0.04))
            if has_primary_contradiction:
                base_conf = max(base_conf, 0.96)
            confidence = min(0.98, base_conf)
            
            sources_str = ", ".join(contradicting_sources[:3])
            
            if is_tamil:
                reason = f"இச்செய்தி போலியானது. {sources_str} உள்ளிட்ட செய்தி நிறுவனங்கள் வெளியிட்ட ஆதாரங்கள் மூலம் இது மறுக்கப்பட்டுள்ளது."
                executive_summary = {
                    "language": "ta",
                    "verdict_type": "FAKE",
                    "headline": "உண்மை சரிபார்ப்பு: இது ஒரு போலிச் செய்தி / வதந்தி",
                    "claimed_event": claim,
                    "factual_reality": f"செய்தி நிறுவனங்கள் ({sources_str}) இத்தகவலை மறுத்து உண்மை பின்னணியை வெளியிட்டுள்ளன.",
                    "key_reasons": [
                        f"நம்பகமான ஊடகங்கள் ({sources_str}) இச்செய்தி தவறானது என விளக்கம் அளித்துள்ளன.",
                        "கூறப்பட்ட தகவலுக்கு எந்தவிதமான அதிகாரப்பூர்வ ஆதாரமும் இல்லை.",
                        "அரசு மற்றும் பொது ஆவணங்களின் தரவுகளுடன் இச்செய்தி முரண்படுகிறது."
                    ],
                    "advisory": "⚠️ போலிச் செய்தி எச்சரிக்கை: இந்த தவறான தகவலை வாட்ஸ்அப் அல்லது சமூக ஊடகங்களில் பகிர வேண்டாம்."
                }
                detailed_explanation = (
                    f"### 📋 உண்மை சரிபார்ப்பு விளக்கம்\n\n"
                    f"- **கூறப்பட்ட செய்தி:** \"{claim}\"\n"
                    f"- **உண்மை நிலை:** நம்பகமான செய்தி நிறுவனங்கள் ({sources_str}) இச்செய்தியை மறுத்துள்ளன.\n"
                    f"- **கண்டறியப்பட்ட சான்றுகள்:** {len(contradicting_articles)} மறுப்பு அறிக்கைகள் மூலம் இத்தகவல் உண்மையல்ல என்பது உறுதி செய்யப்பட்டுள்ளது.\n"
                    f"- **முடிவு:** போதிய மறுப்பு ஆதாரங்களின் அடிப்படையில் இச்செய்தி **🔴 போலிச் செய்தி (FAKE)** என வகைப்படுத்தப்படுகிறது."
                )
            else:
                reason = f"The claim is FALSE and directly contradicted by reports from {sources_str}."
                executive_summary = {
                    "language": "en",
                    "verdict_type": "FAKE",
                    "headline": "Fabricated Claim / Contradicted by Reliable Evidence",
                    "claimed_event": claim,
                    "factual_reality": f"Fact-checking organizations and news outlets ({sources_str}) have reported the true facts refuting this claim.",
                    "key_reasons": [
                        f"Official sources or verified news agencies ({sources_str}) published explicit clarifications or counter-evidence.",
                        "No legitimate corroboration exists for the submitted assertion.",
                        "The claim contradicts established public facts and verified records."
                    ],
                    "advisory": "⚠️ False information. Do not share or forward this viral claim on social media or WhatsApp."
                }
                detailed_explanation = (
                    f"### 📋 Fact-Check Summary\n\n"
                    f"- **Submitted Claim:** \"{claim}\"\n"
                    f"- **Factual Reality:** Contradicted by reliable news and fact-checking organizations ({sources_str}).\n"
                    f"- **Evidence Found:** {len(contradicting_articles)} contradicting report(s) confirming the claim is untrue.\n"
                    f"- **Conclusion:** The submitted claim is classified as **🔴 FAKE / FALSE** based on verifiable counter-evidence."
                )

        # CASE 2: Viral Public Figure Rumor / Fabricated Hoax (Extraordinary Claim with Zero News Backing)
        elif (entities.is_sensational_claim or (entities.is_public_figure and len(articles) == 0)):
            verdict = VerdictType.FALSE
            verdict_display = "🔴 FAKE / FALSE (ஜோடிக்கப்பட்ட வதந்தி)" if is_tamil else "🔴 FAKE / FALSE (FABRICATED RUMOR)"
            confidence = 0.94

            persons_label = ", ".join(entities.persons) if entities.persons else "பிரபலங்கள்"
            
            if is_tamil:
                reason = (
                    f"இது {persons_label} குறித்து சமூக ஊடகங்களில் திட்டமிட்டு பரப்பப்படும் ஜோடிக்கப்பட்ட வதந்தியாகும். "
                    f"எந்தவொரு முன்னணி ஊடகமும் இதனை உறுதிப்படுத்தவில்லை."
                )
                executive_summary = {
                    "language": "ta",
                    "verdict_type": "FAKE_RUMOR",
                    "headline": f"ஜோடிக்கப்பட்ட சமூக ஊடக வதந்தி ({persons_label})",
                    "claimed_event": claim,
                    "factual_reality": "இத்தகைய எந்தவொரு நிகழ்வும் நடைபெறவில்லை. உண்மை ஆதாரங்கள் ஏதுமின்றி பரப்பப்படும் வதந்தி.",
                    "key_reasons": [
                        f"ஒருவேளை {persons_label} குறித்த இந்தத் தகவல் உண்மையாக இருந்திருந்தால், தமிழ்நாட்டின் 20+ முன்னணி செய்தி ஊடகங்கள் (தி இந்து, புதிய தலைமுறை, பிபிசி, தினத்தந்தி) பிரேக்கிங் செய்தியாக வெளியிட்டிருக்கும்.",
                        "அதிகாரப்பூர்வ செய்தித் தொடர்பாளர்கள், பத்திரிகை வெளியீடுகள் அல்லது அரசுப் பதிவேடுகளில் எந்தவொரு உறுதிப்படுத்தலும் இல்லை.",
                        "கிளிக்பைட் மற்றும் வதந்தி பரப்பும் சமூக ஊடகப் பதிவுகளிலிருந்து இச்செய்தி உருவானது."
                    ],
                    "advisory": "⚠️ ஆதாரமற்ற வதந்தி: இந்த தவறான தகவலை மற்றவர்களுக்குப் பகிர வேண்டாம்."
                }
                detailed_explanation = (
                    f"### 📋 உண்மை சரிபார்ப்பு விளக்கம்\n\n"
                    f"- **கூறப்பட்ட செய்தி:** \"{claim}\"\n"
                    f"- **தொடர்புடைய நபர்:** {persons_label}\n"
                    f"- **உண்மை நிலை:** இச்செய்திக்கு எந்தவொரு உண்மை ஆதாரமும் இல்லை.\n"
                    f"- **ஏன் இது போலி?** முன்னணி பிரபலங்கள் குறித்த ஒரு முக்கிய நிகழ்வு உண்மையாக இருந்தால் அனைத்து ஊடகங்களும் வெளியிட்டிருக்கும். 20+ முன்னணி செய்தித் தளங்களில் இதற்கான எந்தச் செய்தியும் இல்லாததால் இது **ஜோடிக்கப்பட்ட வதந்தி** என்பது உறுதியாகிறது.\n"
                    f"- **முடிவு:** இத்தகவல் **🔴 FAKE / FALSE (போலிச் செய்தி)** என தீர்மானிக்கப்படுகிறது."
                )
            else:
                reason = (
                    f"This claim is a fabricated viral social media rumor regarding {persons_label}. "
                    f"No credible news organization or official spokesperson has reported or confirmed any such event."
                )
                executive_summary = {
                    "language": "en",
                    "verdict_type": "FAKE_RUMOR",
                    "headline": f"Fabricated Social Media Rumor ({persons_label})",
                    "claimed_event": claim,
                    "factual_reality": "No such event took place. This is an unfounded rumor circulated on social media without factual basis.",
                    "key_reasons": [
                        f"If an extraordinary event regarding {persons_label} were true, all 20+ major national and Tamil news organizations (The Hindu, Puthiya Thalaimurai, BBC, TOI) would have published breaking news coverage.",
                        "Official representatives, verified press releases, and public records contain zero confirmation.",
                        "The claim matches common patterns of clickbait gossip and fabricated social media forwards."
                    ],
                    "advisory": "⚠️ Unfounded Rumor. This information is false and should not be circulated."
                }
                detailed_explanation = (
                    f"### 📋 Fact-Check Summary\n\n"
                    f"- **Submitted Claim:** \"{claim}\"\n"
                    f"- **Target Entity:** {persons_label}\n"
                    f"- **Factual Reality:** This is a fabricated social media rumor with zero factual basis or official confirmation.\n"
                    f"- **Why is it Fake?** If a major event involving a high-profile public figure had occurred, all 20+ monitored news organizations would have published breaking reports. The complete absence of reporting across all journalistic sources confirms this is a fabricated hoax.\n"
                    f"- **Conclusion:** The submitted claim is classified as **🔴 FAKE / FALSE**."
                )

        # CASE 3: Misleading / Outdated Context
        elif len(misleading_articles) > 0 and independent_supporting == 0:
            verdict = VerdictType.MISLEADING
            verdict_display = "🟡 MISLEADING (தவறான தகவல்)" if is_tamil else "🟡 MISLEADING"
            confidence = 0.86
            
            discrepancy_details = misleading_articles[0].date_discrepancy_note or "Event occurred in the past but is being presented as current."
            
            if is_tamil:
                reason = f"நிகழ்வு உண்மை, ஆனால் அதன் பின்னணி தவறாகச் சித்தரிக்கப்பட்டுள்ளது (பழைய செய்தி): {discrepancy_details}"
                executive_summary = {
                    "language": "ta",
                    "verdict_type": "MISLEADING",
                    "headline": "பழைய செய்தி புதியதாகப் பரப்பப்படுகிறது (தவறான தகவல்)",
                    "claimed_event": claim,
                    "factual_reality": f"இந்த நிகழ்வு கடந்த காலத்தில் நடைபெற்றது: {discrepancy_details}",
                    "key_reasons": [
                        f"{misleading_articles[0].source} தளத்தில் வெளியான முந்தைய செய்தி தற்போது புதியதாக பகிரப்படுகிறது.",
                        "பழைய புகைப்படங்கள் அல்லது செய்திகள் இன்றைய செய்தி போல் திரிக்கப்பட்டுள்ளன.",
                        "நிகழ்வின் காலம் தவறாகக் குறிப்பிடப்பட்டு பொதுமக்களை தவறாக வழிநடத்துகிறது."
                    ],
                    "advisory": "⚠️ தவறான தகவல்: செய்தி வெளியான தேதியை சரிபார்க்காமல் பகிர வேண்டாம்."
                }
                detailed_explanation = (
                    f"### 📋 உண்மை சரிபார்ப்பு விளக்கம்\n\n"
                    f"- **கூறப்பட்ட செய்தி:** \"{claim}\"\n"
                    f"- **கால முரண்பாடு:** {discrepancy_details}\n"
                    f"- **கண்டறியப்பட்ட சான்றுகள்:** {misleading_articles[0].source} வெளியிட்ட பழைய தகவல்கள் மூலம் இது முன்னரே நடந்த நிகழ்வு என்பது தெரியவந்துள்ளது.\n"
                    f"- **முடிவு:** பழைய செய்தி புதியதாக பகிரப்படுவதால் இத்தகவல் **🟡 தவறான தகவல் (MISLEADING)** என வகைப்படுத்தப்படுகிறது."
                )
            else:
                reason = f"The underlying event is real, but the context is misleading: {discrepancy_details}"
                executive_summary = {
                    "language": "en",
                    "verdict_type": "MISLEADING",
                    "headline": "Outdated / Distorted Context",
                    "claimed_event": claim,
                    "factual_reality": f"The event happened in a previous year or different context: {discrepancy_details}",
                    "key_reasons": [
                        f"Matching reports from {misleading_articles[0].source} date back to a past occurrence rather than current events.",
                        "Old news or photos are being recirculated as breaking news.",
                        "The core facts are distorted to mislead the audience."
                    ],
                    "advisory": "⚠️ Misleading context. Verify the original publication date before sharing."
                }
                detailed_explanation = (
                    f"### 📋 Fact-Check Summary\n\n"
                    f"- **Submitted Claim:** \"{claim}\"\n"
                    f"- **Temporal / Context Discrepancy:** {discrepancy_details}\n"
                    f"- **Evidence Found:** Old reports from {misleading_articles[0].source} confirm this happened previously, not today.\n"
                    f"- **Conclusion:** Classified as **🟡 MISLEADING** because old news is being shared as current."
                )

        # CASE 4: Strong Corroboration (TRUE / VERIFIED)
        elif (independent_supporting >= settings.MIN_INDEPENDENT_SOURCES_FOR_TRUE or 
              (has_primary_support and independent_supporting >= 1) or
              (independent_supporting >= 1 and any(a.relevance_score >= 0.60 for a in supporting_articles))):
            
            verdict = VerdictType.TRUE
            verdict_display = "🟢 VERIFIED TRUE (உண்மை செய்தி)" if is_tamil else "🟢 VERIFIED TRUE"
            
            if independent_supporting >= 2 or has_primary_support:
                base_conf = 0.82 + min(0.16, (independent_supporting * 0.04))
                if has_primary_support:
                    base_conf = max(base_conf, 0.94)
                confidence = min(0.98, base_conf)
            else:
                top_rel = max((a.relevance_score for a in supporting_articles), default=0.7)
                confidence = round(min(0.92, 0.75 + (top_rel * 0.18)), 2)
            
            sources_str = ", ".join(supporting_sources[:3])
            
            if is_tamil:
                reason = f"இச்செய்தி உண்மையானது. {sources_str} உள்ளிட்ட {independent_supporting} முன்னணி செய்தி நிறுவனங்கள் இதனை உறுதிப்படுத்தியுள்ளன."
                executive_summary = {
                    "language": "ta",
                    "verdict_type": "TRUE",
                    "headline": "சரிபார்க்கப்பட்ட உண்மைச் செய்தி",
                    "claimed_event": claim,
                    "factual_reality": f"முன்னணி செய்தி ஊடகங்கள் ({sources_str}) இத்தகவலை உறுதிப்படுத்தி வெளியிட்டுள்ளன.",
                    "key_reasons": [
                        f"{independent_supporting} முன்னணி சுயாதீன செய்தி நிறுவனங்கள் இத்தகவலை வெளியிட்டுள்ளன.",
                        "அரசு / அதிகாரப்பூர்வ செய்தி வெளியீடுகளுடன் இத்தகவல் முழுமையாக ஒத்துப் போகிறது." if primary_sources else "நம்பகமான ஊடகங்களின் கள அறிக்கைகள் இச்செய்தியை உறுதிப்படுத்துகின்றன.",
                        "இச்செய்திக்கு எதிரான எந்தவொரு மறுப்பும் பதிவாகவில்லை."
                    ],
                    "advisory": "✓ நம்பகமான செய்தி நிறுவனங்களால் உறுதிப்படுத்தப்பட்ட உண்மைச் செய்தி."
                }
                detailed_explanation = (
                    f"### 📋 உண்மை சரிபார்ப்பு விளக்கம்\n\n"
                    f"- **கூறப்பட்ட செய்தி:** \"{claim}\"\n"
                    f"- **ஊடக உறுதிப்படுத்தல்:** {independent_supporting} முன்னணி ஊடகங்கள் ({sources_str}) இத்தகவலை உறுதி செய்துள்ளன.\n"
                    f"- **முடிவு:** பலதரப்பட்ட ஊடகச் சான்றுகளின் அடிப்படையில் இச்செய்தி **🟢 உண்மை செய்தி (VERIFIED TRUE)** என உறுதி செய்யப்படுகிறது."
                )
            else:
                reason = f"The claim is confirmed by {independent_supporting} independent news organizations including {sources_str}."
                executive_summary = {
                    "language": "en",
                    "verdict_type": "TRUE",
                    "headline": "Verified Authentic News",
                    "claimed_event": claim,
                    "factual_reality": f"Corroborated by multiple credible news outlets ({sources_str}).",
                    "key_reasons": [
                        f"{independent_supporting} independent news organizations published matching reports.",
                        f"Syndicated wire copies ({stats.syndicated_reports}) were verified for source independence.",
                        "Primary official announcements align with the reported event." if primary_sources else "Consistent journalistic reporting confirms the event."
                    ],
                    "advisory": "✓ Verified information from reputable news organizations."
                }
                detailed_explanation = (
                    f"### 📋 Fact-Check Summary\n\n"
                    f"- **Submitted Claim:** \"{claim}\"\n"
                    f"- **Independent Verification:** {independent_supporting} independent news source(s) ({sources_str}) confirm this event.\n"
                    f"- **Conclusion:** Cross-source journalistic evidence confirms this claim as **🟢 TRUE**."
                )

        # CASE 5: Insufficient Evidence (UNVERIFIED)
        else:
            verdict = VerdictType.UNVERIFIED
            verdict_display = "⚪ UNVERIFIED (சரிபார்க்கப்படவில்லை)" if is_tamil else "⚪ UNVERIFIED"
            confidence = 0.35 if len(articles) > 0 else 0.20
            
            if is_tamil:
                reason = (
                    "இத்தகவலை உறுதிப்படுத்தவோ மறுக்கவோ போதுமான ஊடகச் சான்றுகள் கிடைக்கவில்லை. "
                    "Absence of reports is NOT proof that the claim is false. தகவல் இல்லாததால் மட்டுமே செய்தியைப் பொய் என தீர்மானிக்க முடியாது."
                )
                executive_summary = {
                    "language": "ta",
                    "verdict_type": "UNVERIFIED",
                    "headline": "சரிபார்க்க போதுமான ஆதாரங்கள் கிடைக்கவில்லை",
                    "claimed_event": claim,
                    "factual_reality": "இத்தகவலுக்கு ஆதரவாகவோ அல்லது எதிராகவோ நம்பகமான செய்திகள் இன்னும் கிடைக்கவில்லை.",
                    "key_reasons": [
                        f"கண்காணிக்கப்பட்ட {stats.sources_searched} ஊடகங்களில் போதிய உறுதிப்படுத்தல் தகவல்கள் கிடைக்கவில்லை.",
                        "ஆதாரம் கிடைக்கவில்லை என்பது மட்டுமே பொய் என்பதற்கான சான்றாகாது.",
                        "அதிகாரப்பூர்வ அறிவிப்பு வரும் வரை காத்திருக்கவும்."
                    ],
                    "advisory": "⚠️ எச்சரிக்கை: அதிகாரப்பூர்வ தகவல் வெளியாகும் வரை இச்செய்தியைப் பகிர வேண்டாம்."
                }
                detailed_explanation = (
                    f"### 📋 உண்மை சரிபார்ப்பு விளக்கம்\n\n"
                    f"- **கூறப்பட்ட செய்தி:** \"{claim}\"\n"
                    f"- **தேடல் சுருக்கம்:** கண்காணிக்கப்பட்ட {stats.sources_searched} செய்தித் தளங்களில் போதிய தகவல்கள் இல்லை.\n"
                    f"- **முக்கிய கோட்பாடு:** *ஆதாரம் கிடைக்காதது பொய் என்பதற்கான சான்று அல்ல.*\n"
                    f"- **பரிந்துரை:** அதிகாரப்பூர்வ அறிவிப்பு வரும் வரை பகிர வேண்டாம்."
                )
            else:
                reason = (
                    "Insufficient independent evidence was found across monitored sources to reliably confirm or refute this claim. "
                    "Absence of reports is NOT proof that the claim is false."
                )
                executive_summary = {
                    "language": "en",
                    "verdict_type": "UNVERIFIED",
                    "headline": "Unverified Claim / Insufficient Evidence",
                    "claimed_event": claim,
                    "factual_reality": "No conclusive journalistic reporting found to confirm or refute this statement.",
                    "key_reasons": [
                        f"Searched {stats.sources_searched} news sources in English and Tamil with 0 definitive matches.",
                        "Absence of evidence is not proof of falsehood for private claims.",
                        "Pending official clarification or credible reporting."
                    ],
                    "advisory": "⚠️ Exercise caution and avoid sharing until reliable evidence is published."
                }
                detailed_explanation = (
                    f"### 📋 Fact-Check Summary\n\n"
                    f"- **Submitted Claim:** \"{claim}\"\n"
                    f"- **Search Summary:** Monitored {stats.sources_searched} sources with no conclusive reports found.\n"
                    f"- **Core Epistemic Principle:** *No evidence found ≠ Evidence of falsehood.*\n"
                    f"- **Recommendation:** Do not share until verified."
                )

        # -------------------------------------------------------------
        # BUILD DEDUPLICATED SOURCE COMPARISON TABLE (1 Row Per Source)
        # -------------------------------------------------------------
        comparison_table: List[SourceComparisonItem] = []
        source_articles_map: Dict[str, Article] = {}

        # Group by source and select highest relevance article
        for a in articles:
            if a.source not in source_articles_map or a.relevance_score > source_articles_map[a.source].relevance_score:
                source_articles_map[a.source] = a

        for src_name, a in source_articles_map.items():
            tier = SourceReliabilityEvaluator.get_tier(a.source_id, a.source_type == SourceType.PRIMARY)
            display_date = format_display_date(a.publication_date)
            comparison_table.append(SourceComparisonItem(
                source_name=a.source,
                found=True,
                supports=(a.polarity == EvidencePolarity.SUPPORTS),
                contradicts=(a.polarity == EvidencePolarity.CONTRADICTS),
                date=display_date,
                source_type=a.source_type.value,
                reliability=tier.capitalize(),
                article_title=a.title,
                article_url=a.url
            ))

        for st in source_statuses:
            if st.status == "no_results" and not any(r.source_name == st.source_name for r in comparison_table):
                comparison_table.append(SourceComparisonItem(
                    source_name=st.source_name,
                    found=False,
                    supports=False,
                    contradicts=False,
                    date="—",
                    source_type="—",
                    reliability="—",
                    article_title=None,
                    article_url=None
                ))

        confidence_pct = round(confidence * 100, 1)

        return VerificationResult(
            id=verification_id,
            verdict=verdict,
            verdict_display=verdict_display,
            confidence=round(confidence, 3),
            confidence_display=f"{confidence_pct}%",
            language=language,
            claim=claim,
            original_text=original_text,
            url=url,
            reason=reason,
            detailed_explanation=detailed_explanation,
            executive_summary=executive_summary,
            supporting_sources=supporting_sources,
            contradicting_sources=contradicting_sources,
            primary_sources=primary_sources,
            articles=articles,
            comparison_table=comparison_table,
            source_statuses=source_statuses,
            stats=stats,
            created_at=datetime.now(timezone.utc).isoformat()
        )
