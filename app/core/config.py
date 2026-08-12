import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Google Custom Search ---
    GOOGLE_CSE_API_KEY: str = os.getenv("GOOGLE_CSE_API_KEY", "")
    GOOGLE_CSE_ENGINE_ID: str = os.getenv("GOOGLE_CSE_ENGINE_ID", "")

    # --- Verdict thresholds ---
    CONSENSUS_THRESHOLD: int = int(os.getenv("CONSENSUS_THRESHOLD", "2"))

    # Minimum cosine similarity (with correct e5 query/passage prefixing)
    # for a retrieved article to even be considered a candidate. This is a
    # cheap first-pass filter only -- true relevance is decided by the NLI
    # step below, not by this score alone.
    SIMILARITY_FLOOR: float = float(os.getenv("SIMILARITY_FLOOR", "0.60"))

    # Minimum NLI softmax confidence required to accept an entailment/
    # contradiction label. Below this, the article is treated as neutral
    # (i.e. not related enough to count as evidence either way).
    NLI_CONFIDENCE_FLOOR: float = float(os.getenv("NLI_CONFIDENCE_FLOOR", "0.55"))

    # --- RSS worker ---
    RSS_POLL_INTERVAL_MINUTES: int = int(os.getenv("RSS_POLL_INTERVAL_MINUTES", "15"))

    # --- Vector DB ---
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

    # --- Models ---
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"
    NLI_MODEL: str = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

    # --- The trusted whitelist ---
    # domain: used for site: search + RSS ingestion
    # rss: feed URL (may be None if the outlet has no reliable feed;
    #      scraper fallback is used instead)
    # lang: "en" or "ta"
    WHITELIST = {
        "thehindu.com": {
            "name": "The Hindu",
            "lang": "en",
            "rss": "https://www.thehindu.com/news/national/feeder/default.rss",
        },
        "indianexpress.com": {
            "name": "The Indian Express",
            "lang": "en",
            "rss": "https://indianexpress.com/section/india/feed/",
        },
        "timesofindia.indiatimes.com": {
            "name": "Times of India",
            "lang": "en",
            "rss": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        },
        "hindustantimes.com": {
            "name": "Hindustan Times",
            "lang": "en",
            "rss": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        },
        "dailythanthi.com": {
            "name": "Daily Thanthi",
            "lang": "ta",
            "rss": None,  # no reliable public feed -> scraper fallback
        },
        "polimernews.com": {
            "name": "Polimer News",
            "lang": "ta",
            "rss": None,
        },
        "puthiyathalaimurai.com": {
            "name": "Puthiya Thalaimurai",
            "lang": "ta",
            "rss": "https://www.puthiyathalaimurai.com/feed/",
        },
    }


settings = Settings()
