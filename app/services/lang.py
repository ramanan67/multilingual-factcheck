import re

TAMIL_RANGE = re.compile(r"[\u0B80-\u0BFF]")


def detect_language(text: str) -> str:
    """Cheap script-based detector: Tamil unicode block vs everything else.
    Good enough for routing; swap for langdetect/fasttext if you need
    more languages later."""
    return "ta" if TAMIL_RANGE.search(text) else "en"
