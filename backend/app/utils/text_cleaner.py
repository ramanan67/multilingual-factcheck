"""
Text normalization and cleaning utility.
Handles English and Tamil text normalization, HTML stripping, and boilerplate removal.
"""

import re
import unicodedata
from typing import List
from bs4 import BeautifulSoup


# Tamil Unicode range: U+0B80 to U+0BFF
TAMIL_CHAR_PATTERN = re.compile(r'[\u0B80-\u0BFF]')
# English word pattern
ENGLISH_WORD_PATTERN = re.compile(r'[a-zA-Z]+')

# Common boilerplate phrases to discard in news scraping
BOILERPLATE_PATTERNS = [
    re.compile(r'Subscribe to our newsletter', re.IGNORECASE),
    re.compile(r'Sign up for free', re.IGNORECASE),
    re.compile(r'All rights reserved', re.IGNORECASE),
    re.compile(r'Follow us on Twitter|Facebook|Instagram|Telegram', re.IGNORECASE),
    re.compile(r'Read more\b', re.IGNORECASE),
    re.compile(r'Also Read:', re.IGNORECASE),
    re.compile(r'மேலும் படிக்க:', re.IGNORECASE),
    re.compile(r'செய்திகளை உடனுக்குடன் பெற', re.IGNORECASE),
    re.compile(r'கூகுள் செய்திகள் பக்கத்தில்', re.IGNORECASE),
    re.compile(r'பதிவிறக்கம் செய்க', re.IGNORECASE),
]


def clean_html(raw_html: str) -> str:
    """Strips HTML tags, script, and style blocks, returning clean text."""
    if not raw_html:
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return clean_text(text)
    except Exception:
        return clean_text(raw_html)


def clean_text(text: str) -> str:
    """Normalizes whitespace, removes control chars, and standardizes quotes and dashes."""
    if not text:
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Standardize quotation marks
    text = re.sub(r'[\u2018\u2019\u201A\u201B]', "'", text)
    text = re.sub(r'[\u201C\u201D\u201E\u201F]', '"', text)
    # Standardize dashes
    text = re.sub(r'[\u2013\u2014]', '-', text)
    # Remove excess whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def remove_boilerplate(text: str) -> str:
    """Removes common news site boilerplate and advertisement filler."""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        is_boilerplate = any(p.search(stripped) for p in BOILERPLATE_PATTERNS)
        if not is_boilerplate and len(stripped) > 10:
            cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines) if cleaned_lines else text


def tokenize_words(text: str) -> List[str]:
    """Tokenizes text into words preserving Tamil and English alphanumeric characters."""
    if not text:
        return []
    cleaned = clean_text(text).lower()
    # Matches Tamil words, English words, numbers
    tokens = re.findall(r'[\u0B80-\u0BFF]+|[a-z0-9]+', cleaned)
    return [t for t in tokens if len(t) > 1]


def truncate_snippet(text: str, max_length: int = 280) -> str:
    """Truncates text to a concise, readable snippet ending on word boundary."""
    if not text or len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:
        truncated = truncated[:last_space]
    return truncated.strip() + "..."
