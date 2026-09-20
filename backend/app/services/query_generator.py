"""
Multilingual Query Generator.
Translates, extracts salient search keywords, and generates targeted search phrases for English and Tamil news sources.
"""

import re
from typing import List, Dict, Tuple
from backend.app.models.models import ExtractedEntities, LanguageType
from backend.app.services.language_detector import LanguageDetector
from backend.app.utils.text_cleaner import clean_text


# Stop words to filter from query terms to prevent overly restrictive search
TAMIL_QUERY_STOP_WORDS = {
    "ஏற்பட்ட", "வருவதாகவும்", "உள்ளதாகவும்", "தகவல்", "வெளியிடப்பட்டுள்ளது",
    "என", "என்று", "ஆகிய", "குறித்து", "பற்றி", "செய்தி", "உள்ள", "உள்ளது",
    "உள்ளனர்", "இருந்து", "செய்து", "செய்யப்பட்டு", "மற்றும்", "ஆனால்",
    "காரணமாக", "காரணம்", "அறிவிக்கப்பட்டுள்ளது", "தெரிவிக்கப்பட்டுள்ளது"
}

ENGLISH_QUERY_STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "with", "by", "from",
    "is", "was", "are", "were", "be", "been", "being", "have", "has", "had",
    "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "this", "that", "these", "those", "due", "because", "information", "released",
    "report", "reported", "statement", "said", "says", "according"
}

# Keyword dictionary for cross-lingual query mapping
EN_TO_TA_KEYWORDS = {
    "school": "பள்ளி",
    "schools": "பள்ளிகள்",
    "college": "கல்லூரி",
    "colleges": "கல்லூரிகள்",
    "holiday": "விடுமுறை",
    "closed": "விடுமுறை",
    "heavy rain": "கனமழை",
    "rain": "மழை",
    "cyclone": "புயல்",
    "flood": "வெள்ளம்",
    "floods": "வெள்ளம்",
    "chennai": "சென்னை",
    "coimbatore": "கோவை",
    "madurai": "மதுரை",
    "salem": "சேலம்",
    "tamil nadu": "தமிழ்நாடு",
    "nepal": "நேபாள",
    "tamils": "தமிழர்கள்",
    "pilgrims": "பயணிகள்",
    "rescue": "மீட்பு",
    "rescued": "மீட்கப்பட்டு",
    "safe": "பாதுகாப்பாக",
    "government": "அரசு",
    "announcement": "அறிவிப்பு",
    "collector": "ஆட்சியர்",
    "tomorrow": "நாளை",
    "today": "இன்று",
    "stalin": "ஸ்டாலின்",
    "exam": "தேர்வு",
    "cancelled": "ரத்து",
    "married": "திருமணம்",
    "marriage": "திருமணம்",
    "died": "மறைவு",
    "death": "மரணம்",
    "arrested": "கைது",
    # Cultural, Festival & Event Terms
    "ganesh": "விநாயகர்",
    "ganesha": "விநாயகர்",
    "vinayagar": "விநாயகர்",
    "vinayaka": "விநாயகர்",
    "idol": "சிலை",
    "idols": "சிலைகள்",
    "immersion": "கரைப்பு",
    "visarjan": "கரைப்பு",
    "procession": "ஊர்வலம்",
    "chaturthi": "சதுர்த்தி",
    "diwali": "தீபாவளி",
    "deepavali": "தீபாவளி",
    "bonus": "போனஸ்",
    "pongal": "பொங்கல்",
    "gift": "பரிசு",
    "bus": "பேருந்து",
    "buses": "பேருந்துகள்",
    "special": "சிறப்பு",
    "minister": "அமைச்சர்",
    "cm": "முதல்வர்",
    "pm": "பிரதமர்",
}

TA_TO_EN_KEYWORDS = {
    "பள்ளி": "school",
    "பள்ளிகள்": "schools",
    "பள்ளிகளுக்கு": "schools",
    "கல்லூரி": "college",
    "கல்லூரிகள்": "colleges",
    "விடுமுறை": "holiday",
    "கனமழை": "heavy rain",
    "மழை": "rain",
    "புயல்": "cyclone",
    "வெள்ளம்": "flood",
    "வெள்ளத்தில்": "flood",
    "நேபாள": "Nepal",
    "நேபாளம்": "Nepal",
    "நேபாளத்தில்": "Nepal",
    "தமிழர்கள்": "Tamils",
    "பயணிகள்": "pilgrims",
    "மீட்பு": "rescue",
    "மீட்கப்பட்டு": "rescued",
    "பாதுகாப்பாக": "safe",
    "பத்திரமாக": "safe",
    "சிக்கிய": "stranded",
    "சென்னை": "Chennai",
    "சென்னையில்": "Chennai",
    "கோவை": "Coimbatore",
    "மதுரை": "Madurai",
    "சேலம்": "Salem",
    "திருச்சி": "Trichy",
    "திருநெல்வேலி": "Tirunelveli",
    "தமிழ்நாடு": "Tamil Nadu",
    "தமிழக": "Tamil Nadu",
    "அரசு": "Government",
    "அறிவிப்பு": "announcement",
    "ஆட்சியர்": "collector",
    "நாளை": "tomorrow",
    "இன்று": "today",
    "ஸ்டாலின்": "Stalin",
    "தேர்வு": "exam",
    "ரத்து": "cancelled",
    "திருமணம்": "marriage",
    "கல்யாணம்": "marriage",
    "மரணம்": "death",
    "மறைவு": "death",
    "கைது": "arrested",
    # Cultural, Festival & Event Terms
    "விநாயகர்": "Vinayagar Ganesh",
    "விநாயக": "Vinayagar Ganesh",
    "சிலை": "idol",
    "சிலைகள்": "idols",
    "கரைப்பு": "immersion",
    "கரைக்க": "immersion",
    "விசர்ஜனம்": "visarjan immersion",
    "ஊர்வலம்": "procession",
    "சதுர்த்தி": "Chaturthi",
    "தீபாவளி": "Diwali Deepavali",
    "போனஸ்": "bonus",
    "பொங்கல்": "Pongal",
    "பரிசு": "gift",
    "பேருந்து": "bus",
    "பேருந்துகள்": "buses",
    "சிறப்பு": "special",
    "அமைச்சர்": "minister",
    "முதல்வர்": "Chief Minister",
    "முதலமைச்சர்": "Chief Minister",
    "பிரதமர்": "Prime Minister",
}


class QueryGenerator:
    """Generates targeted, high-precision search query variations across Tamil and English."""

    @classmethod
    def generate_queries(cls, text: str, entities: ExtractedEntities, detected_lang: str) -> Dict[str, List[str]]:
        cleaned = clean_text(text)
        ta_queries: List[str] = []
        en_queries: List[str] = []

        # 1. Extract salient non-stop words from raw text
        raw_words = re.findall(r'[\u0B80-\u0BFF]+|[a-zA-Z0-9]+', cleaned)
        salient_words = [
            w for w in raw_words 
            if len(w) > 1 and w.lower() not in ENGLISH_QUERY_STOP_WORDS and w not in TAMIL_QUERY_STOP_WORDS
        ]

        # 2. Add concise 3-4 word core query from salient words
        if salient_words:
            core_query = " ".join(salient_words[:5])
            if detected_lang in (LanguageType.TA.value, LanguageType.MIXED.value):
                ta_queries.append(core_query)
            else:
                en_queries.append(core_query)

        # 3. Add Entity & keyword combined queries
        parts = []
        if entities.locations:
            parts.append(entities.locations[0])
        if entities.persons:
            parts.append(entities.persons[0])
        if entities.event_keywords:
            parts.extend(entities.event_keywords[:2])
        if entities.numbers:
            parts.append(entities.numbers[0])

        if parts:
            comb = " ".join(parts)
            if detected_lang == "ta":
                ta_queries.append(comb)
            else:
                en_queries.append(comb)

        # 4. Add Fact-Check & Debunk queries if viral/sensational claim
        if entities.is_sensational_claim or entities.is_public_figure:
            persons_str = " ".join(entities.persons) if entities.persons else ""
            if persons_str:
                en_queries.append(f"{persons_str} fact check")
                en_queries.append(f"{persons_str} rumor fake")
                ta_queries.append(f"{persons_str} உண்மை வதந்தி")
            else:
                en_queries.append(f"{cleaned[:50]} fact check")
                ta_queries.append(f"{cleaned[:50]} உண்மை பின்னணி")

        # 5. Cross-lingual translation using domain dictionary
        translated_en_words = []
        for w in raw_words:
            for ta_k, en_v in TA_TO_EN_KEYWORDS.items():
                if ta_k in w and en_v not in translated_en_words:
                    translated_en_words.append(en_v)
            if w.isdigit() and w not in translated_en_words:
                translated_en_words.append(w)

        if translated_en_words:
            trans_en_q = " ".join(translated_en_words[:6])
            if trans_en_q not in en_queries and len(trans_en_q) > 3:
                en_queries.append(trans_en_q)

        translated_ta_words = []
        for w in raw_words:
            for en_k, ta_v in EN_TO_TA_KEYWORDS.items():
                if en_k in w.lower() and ta_v not in translated_ta_words:
                    translated_ta_words.append(ta_v)
            if w.isdigit() and w not in translated_ta_words:
                translated_ta_words.append(w)

        if translated_ta_words:
            trans_ta_q = " ".join(translated_ta_words[:6])
            if trans_ta_q not in ta_queries and len(trans_ta_q) > 3:
                ta_queries.append(trans_ta_q)

        # 6. Fallback short query
        if not ta_queries:
            ta_queries.append(cleaned[:60])
        if not en_queries:
            en_queries.append(cleaned[:60])

        # Primary portal queries
        primary_queries = []
        if entities.organizations:
            primary_queries.append(f"{entities.organizations[0]} announcement")
        if entities.locations:
            primary_queries.append(f"{entities.locations[0]} official order")
        if not primary_queries:
            primary_queries = [cleaned[:60]]

        return {
            "ta": list(dict.fromkeys(ta_queries))[:5],
            "en": list(dict.fromkeys(en_queries))[:5],
            "primary": list(dict.fromkeys(primary_queries))[:3],
        }
