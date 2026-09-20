"""
Claim and Named Entity Extractor.
Extracts entities (Person, Org, Location, Date, Numbers, Keywords), assertion polarity,
and detects high-profile viral celebrity/political claims across Tamil and English.
"""

import re
from typing import List, Dict, Any, Tuple
from backend.app.models.models import ExtractedEntities
from backend.app.utils.text_cleaner import clean_text


# Predefined Tamil & English Entity dictionaries for news and Tamil Nadu domain
LOCATIONS_MAP = {
    # Tamil Nadu Cities & Districts
    "chennai": ["chennai", "madras", "சென்னை", "சென்னையில்", "சென்னைக்கு"],
    "coimbatore": ["coimbatore", "kovai", "கோயம்புத்தூர்", "கோவை"],
    "madurai": ["madurai", "மதுரை", "மதுரையில்"],
    "tiruchirappalli": ["trichy", "tiruchirappalli", "திருச்சி", "திருச்சிராப்பள்ளி"],
    "salem": ["salem", "சேலம்", "சேலத்தில்"],
    "tirunelveli": ["tirunelveli", "nellai", "திருநெல்வேலி", "நெல்லை"],
    "kancheepuram": ["kancheepuram", "kanchipuram", "காஞ்சிபுரம்"],
    "chengalpattu": ["chengalpattu", "செங்கல்பட்டு"],
    "tiruvallur": ["tiruvallur", "thiruvallur", "திருவள்ளூர்"],
    "thanjavur": ["thanjavur", "தஞ்சாவூர்", "தஞ்சை"],
    "tamil nadu": ["tamil nadu", "tamilnadu", "தமிழ்நாடு", "தமிழகம்", "தமிழக"],
    "delhi": ["delhi", "new delhi", "டெல்லி"],
    "india": ["india", "இந்தியா"],
    # International & Other Indian States
    "nepal": ["nepal", "நேபாள", "நேபாளம்", "நேபாளத்தில்", "காத்மாண்டு", "kathmandu"],
    "kerala": ["kerala", "கேரளா", "கேரளம்", "வயநாடு", "wayanad"],
    "karnataka": ["karnataka", "கர்நாடகா", "பெங்களூரு", "bangalore", "bengaluru"],
    "andhra": ["andhra", "ஆந்திரா", "விஜயவாடா", "vijayawada", "திருப்பதி", "tirupati"],
    "sri lanka": ["sri lanka", "இலங்கை"],
}

ORGANIZATIONS_MAP = {
    "tamil nadu government": ["tn government", "tamil nadu government", "tn govt", "தமிழக அரசு", "தமிழ்நாடு அரசு"],
    "school education department": ["school education department", "education department", "பள்ளிக்கல்வித்துறை", "பள்ளிக் கல்வித்துறை"],
    "police": ["police", "tamil nadu police", "காவல்துறை", "போலீஸ்"],
    "meteorological department": ["imd", "met department", "weather department", "வானிலை ஆய்வு மையம்", "வானிலை மையம்"],
    "election commission": ["election commission", "eci", "தேர்தல் ஆணையம்"],
    "high court": ["high court", "madras high court", "சென்னை உயர்நீதிமன்றம்", "உயர்நீதிமன்றம்"],
    "supreme court": ["supreme court", "உச்சநீதிமன்றம்"],
    "railways": ["railways", "southern railway", "ரயில்வே", "தெற்கு ரயில்வே"],
    "tvk": ["tvk", "tamizhaga vettri kazhagam", "தமிழக வெற்றிக் கழகம்", "தவெக"],
    "dmk": ["dmk", "திமுக"],
    "aiadmk": ["aiadmk", "அதிமுக"],
    "bjp": ["bjp", "பாஜக"],
}

PERSONS_MAP = {
    "Actor / Politician Vijay": ["vijay", "actor vijay", "thalapathy vijay", "tvk vijay", "cm vijay", "விஜய்", "தளபதி விஜய்"],
    "Actress Trisha": ["trisha", "actress trisha", "trish", "திரிஷா", "நடிகை திரிஷா"],
    "M K Stalin": ["mk stalin", "m.k. stalin", "stalin", "cm stalin", "மு.க.ஸ்டாலின்", "ஸ்டாலின்", "முதலமைச்சர் ஸ்டாலின்"],
    "Narendra Modi": ["modi", "narendra modi", "pm modi", "நரேந்திர மோடி", "மோடி", "பிரதமர் மோடி"],
    "Edappadi Palaniswami": ["edappadi palaniswami", "eps", "எடப்பாடி பழனிசாமி", "எடப்பாடி"],
    "K Annamalai": ["annamalai", "k annamalai", "அண்ணாமலை"],
    "Rajinikanth": ["rajinikanth", "rajini", "superstar rajinikanth", "ரஜினிகாந்த்", "ரஜினி"],
    "Kamal Haasan": ["kamal haasan", "kamal", "கமல்ஹாசன்", "கமல்"],
    "Ajith Kumar": ["ajith", "ajith kumar", "தல அஜித்", "அஜித்"],
    "Udhayanidhi Stalin": ["udhayanidhi", "udhayanidhi stalin", "துணை முதல்வர் உதயநிதி", "உதயநிதி ஸ்டாலின்"],
    "District Collector": ["collector", "district collector", "மாவட்ட ஆட்சியர்", "ஆட்சியர்"],
    "Governor": ["governor", "r.n. ravi", "ஆளுநர்"],
}

EVENT_KEYWORDS = [
    # School / Holiday
    "holiday", "schools closed", "colleges closed", "school holiday", "college holiday", "closure", "closed",
    "விடுமுறை", "பள்ளிகள் விடுமுறை", "பள்ளிகளுக்கு விடுமுறை", "கல்லூரிகள் விடுமுறை",
    # Weather & Disasters
    "heavy rain", "cyclone", "flood", "floods", "red alert", "orange alert", "rainfall", "rain", "landslide",
    "கனமழை", "மழை", "புயல்", "வெள்ளம்", "வெள்ளத்தில்", "நிலச்சரிவு", "ரெட் அலர்ட்",
    # Rescue & Human interest
    "rescue", "rescued", "safe", "safety", "stranded", "trapped", "tamils", "pilgrims",
    "மீட்பு", "மீட்கப்பட்டு", "பாதுகாப்பாக", "பத்திரமாக", "சிக்கிய", "தவித்த", "தமிழர்கள்",
    # Government policy & announcements
    "free bus", "allowance", "scheme", "announcement", "ban", "arrest", "subsidy", "exam cancelled", "strike",
    "இலவச பேருந்து", "திட்டம்", "அறிவிப்பு", "தடை", "கைது", "தேர்வு ரத்து", "வேலைநிறுத்தம்",
    # Cultural, Festivals & Public Events
    "vinayagar", "ganesh", "ganesha", "ganesh chaturthi", "vinayagar chaturthi", "idol immersion", "visarjan", "procession",
    "விநாயகர்", "விநாயகர் சிலை", "சிலை கரைப்பு", "சிலைகள் கரைப்பு", "விநாயகர் சதுர்த்தி", "கரைப்பு", "ஊர்வலம்", "சிலை",
    "diwali", "deepavali", "diwali bonus", "pongal", "pongal gift", "bonus", "gift", "special buses",
    "தீபாவளி", "தீபாவளி போனஸ்", "போனஸ்", "பொங்கல்", "பொங்கல் பரிசு", "சிறப்பு பேருந்து", "சிறப்பு பேருந்துகள்",
    # Sensational / Celebrity Life Events
    "married", "marriage", "wedding", "divorced", "divorce", "affair", "relationship",
    "died", "death", "passed away", "hospitalized", "accident", "secret meeting", "resigned",
    "திருமணம்", "கல்யாணம்", "மறைவு", "மரணம்", "காலமானார்", "மருத்துவமனையில் அனுமதி", "ரகசிய சந்திப்பு"
]

SENSATIONAL_EVENT_TERMS = [
    "married", "marriage", "wedding", "divorce", "divorced", "secret marriage",
    "died", "death", "passed away", "killed", "secret meeting", "resigned",
    "திருமணம்", "கல்யாணம்", "இரண்டாவது திருமணம்", "மரணம்", "மறைவு", "காலமானார்"
]

DATE_PATTERNS = [
    re.compile(r'\b(tomorrow|today|yesterday|tonight)\b', re.I),
    re.compile(r'(நாளை|இன்று|நேற்று|இரவு)'),
    re.compile(r'\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{1,2}(?:st|nd|rd|th)?)\b', re.I),
    re.compile(r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(?:\d{2,4})?)\b', re.I),
    re.compile(r'\b((?:201\d|202\d))\b'),
]

NUMBER_PATTERN = re.compile(r'\b(\d+(?:\.\d+)?(?:\s*(?:crore|lakh|percent|%|ரூபாய்|கோடி|இலட்சம்|பேர்|நபர்கள்))?)\b', re.I)

NEGATION_PATTERNS = [
    re.compile(r'\b(no|not|denies|denied|fake|false|hoax|rumour|rumor|clarifies|rejected)\b', re.I),
    re.compile(r'(போலி|வதந்தி|உண்மையல்ல|செய்தி தவறு|மறுப்பு|ரத்து செய்யப்படவில்லை|இல்லை)'),
]


class ClaimExtractor:
    """Extracts structured entities and factual intent from claim text."""

    @classmethod
    def extract(cls, text: str) -> ExtractedEntities:
        cleaned = clean_text(text)
        lower = cleaned.lower()

        # Extract locations
        locations = []
        for canonical, variants in LOCATIONS_MAP.items():
            if any(v in lower for v in variants):
                locations.append(canonical.title())

        # Extract organizations
        organizations = []
        for canonical, variants in ORGANIZATIONS_MAP.items():
            if any(v in lower for v in variants):
                organizations.append(canonical.title())

        # Extract persons
        persons = []
        for canonical, variants in PERSONS_MAP.items():
            if any(v in lower for v in variants):
                persons.append(canonical.title())

        # Extract event keywords
        event_keywords = []
        for kw in EVENT_KEYWORDS:
            if kw in lower:
                event_keywords.append(kw)

        # Extract dates
        dates = []
        for dp in DATE_PATTERNS:
            matches = dp.findall(cleaned)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                if m and str(m) not in dates:
                    dates.append(str(m))

        # Extract numbers (e.g. 148, 100, 50%)
        numbers = []
        for num_match in NUMBER_PATTERN.findall(cleaned):
            digits_only = re.sub(r'[^\d.]', '', num_match)
            if digits_only and digits_only not in numbers:
                numbers.append(digits_only)

        # Check negation / contradiction words in claim
        is_negated = any(p.search(cleaned) for p in NEGATION_PATTERNS)

        # Check if this is a sensational public figure / celebrity claim
        is_public_fig = len(persons) > 0 or "actor" in lower or "actress" in lower or "cm" in lower or "pm" in lower or "minister" in lower
        has_sensational_action = any(st in lower for st in SENSATIONAL_EVENT_TERMS)
        is_sensational = bool(is_public_fig and has_sensational_action)

        # Clean main statement
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', cleaned) if len(s.strip()) > 10]
        main_statement = sentences[0] if sentences else cleaned

        return ExtractedEntities(
            persons=persons,
            organizations=organizations,
            locations=locations,
            dates=dates,
            numbers=numbers,
            event_keywords=event_keywords,
            main_statement=main_statement,
            polarity_negated=is_negated,
            is_public_figure=is_public_fig,
            is_sensational_claim=is_sensational
        )
