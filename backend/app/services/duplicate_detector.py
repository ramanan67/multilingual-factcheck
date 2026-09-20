"""
Duplicate and News Syndication Detector.
Identifies wire agency reports (ANI, PTI, IANS, Reuters) and duplicate articles to avoid false confirmation bias.
"""

import re
from typing import List, Tuple, Dict, Any
from backend.app.models.models import Article, SourceType, VerificationStats
from backend.app.services.article_matcher import compute_jaccard_similarity, compute_ngram_similarity
from backend.app.utils.text_cleaner import tokenize_words, clean_text


WIRE_AGENCIES = [
    (re.compile(r'\b(ANI|Asian News International)\b', re.I), "ANI"),
    (re.compile(r'\b(PTI|Press Trust of India)\b', re.I), "PTI"),
    (re.compile(r'\b(IANS|Indo-Asian News Service)\b', re.I), "IANS"),
    (re.compile(r'\b(UNI|United News of India)\b', re.I), "UNI"),
    (re.compile(r'\b(Reuters)\b', re.I), "Reuters"),
]


class DuplicateDetector:
    """Detects syndicated wire articles and near-duplicate reports."""

    @classmethod
    def analyze_articles(cls, articles: List[Article]) -> Tuple[List[Article], VerificationStats]:
        """
        Analyzes a list of collected articles, tags syndicated/wire articles,
        and computes accurate independent vs syndicated stats.
        """
        if not articles:
            return [], VerificationStats()

        processed_articles: List[Article] = []
        seen_content_hashes: List[Tuple[str, List[str]]] = []  # (source_id, tokens)
        
        independent_count = 0
        syndicated_count = 0
        primary_count = 0

        for article in articles:
            # 1. Primary sources are always preserved as Primary
            if article.source_type == SourceType.PRIMARY:
                article.is_syndicated = False
                processed_articles.append(article)
                primary_count += 1
                continue

            # 2. Check for Wire Agency mentions in text or title
            wire_found = None
            combined_text = f"{article.title} {article.snippet} {article.author or ''}"
            for pattern, agency_name in WIRE_AGENCIES:
                if pattern.search(combined_text):
                    wire_found = agency_name
                    break

            # 3. Check for near-identical duplicate text against already seen articles
            article_tokens = tokenize_words(f"{article.title} {article.snippet}")
            is_near_duplicate = False
            for seen_src, seen_tokens in seen_content_hashes:
                similarity = compute_jaccard_similarity(article_tokens, seen_tokens)
                if similarity > 0.65:
                    is_near_duplicate = True
                    break

            if wire_found:
                article.is_syndicated = True
                article.wire_agency = wire_found
                article.source_type = SourceType.SYNDICATED
                syndicated_count += 1
            elif is_near_duplicate:
                article.is_syndicated = True
                article.source_type = SourceType.SYNDICATED
                syndicated_count += 1
            else:
                article.is_syndicated = False
                article.source_type = SourceType.INDEPENDENT
                independent_count += 1
                seen_content_hashes.append((article.source_id, article_tokens))

            processed_articles.append(article)

        stats = VerificationStats(
            total_articles=len(processed_articles),
            independent_reports=independent_count,
            syndicated_reports=syndicated_count,
            primary_sources=primary_count,
            sources_searched=len(set(a.source_id for a in processed_articles)),
            sources_successful=len(set(a.source_id for a in processed_articles if a.relevance_score > 0.3))
        )

        return processed_articles, stats
