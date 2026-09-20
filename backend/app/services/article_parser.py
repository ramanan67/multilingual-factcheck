"""
Article Parser and Metadata Extractor.
Extracts title, dates, authors, and text snippets from news web pages and feeds.
"""

import json
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from datetime import datetime, timezone

from backend.app.utils.text_cleaner import clean_html, clean_text, remove_boilerplate, truncate_snippet
from backend.app.utils.logger import logger


class ArticleParser:
    """Extracts structured metadata and clean content from raw HTML."""

    @staticmethod
    def parse_article_html(html: str, url: str) -> Dict[str, Any]:
        if not html:
            return {
                "title": "",
                "publication_date": None,
                "author": None,
                "snippet": "",
                "full_text": "",
                "is_parsed": False
            }

        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 1. Title Extraction
            title = ""
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = clean_text(og_title["content"])
            elif soup.title and soup.title.string:
                title = clean_text(soup.title.string)
            elif soup.find("h1"):
                title = clean_text(soup.find("h1").get_text())

            # 2. JSON-LD Schema Metadata
            pub_date = None
            author = None
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            for script in json_ld_scripts:
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = data[0]
                    if isinstance(data, dict):
                        if "@type" in data and ("NewsArticle" in data["@type"] or "Article" in data["@type"]):
                            pub_date = data.get("datePublished") or data.get("dateModified")
                            if "author" in data:
                                if isinstance(data["author"], dict):
                                    author = data["author"].get("name")
                                elif isinstance(data["author"], list) and data["author"]:
                                    author = data["author"][0].get("name")
                                elif isinstance(data["author"], str):
                                    author = data["author"]
                            break
                except Exception:
                    pass

            # 3. Meta tag fallbacks for date
            if not pub_date:
                meta_date = soup.find("meta", property="article:published_time") or \
                            soup.find("meta", attrs={"name": "publish-date"}) or \
                            soup.find("meta", attrs={"name": "pubdate"}) or \
                            soup.find("time")
                if meta_date:
                    pub_date = meta_date.get("content") or meta_date.get("datetime") or meta_date.get_text()

            # 4. Meta tag fallbacks for author
            if not author:
                meta_auth = soup.find("meta", attrs={"name": "author"}) or \
                            soup.find("meta", property="article:author")
                if meta_auth and meta_auth.get("content"):
                    author = clean_text(meta_auth["content"])

            # 5. Extract Content Body
            for elem in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                elem.decompose()

            article_container = soup.find("article") or \
                                soup.find("div", class_=re.compile(r'article[-_]?body|story[-_]?content|entry[-_]?content', re.I))
            if article_container:
                paras = article_container.find_all("p")
            else:
                paras = soup.find_all("p")

            text_paragraphs = [clean_text(p.get_text()) for p in paras if len(clean_text(p.get_text())) > 25]
            full_text = "\n".join(text_paragraphs)
            cleaned_body = remove_boilerplate(full_text)
            snippet = truncate_snippet(cleaned_body, max_length=280) if cleaned_body else truncate_snippet(title, max_length=280)

            # Standardize date format if parseable
            std_date = ArticleParser.normalize_date_str(pub_date)

            return {
                "title": title,
                "publication_date": std_date or pub_date,
                "author": author,
                "snippet": snippet,
                "full_text": cleaned_body,
                "is_parsed": True
            }
        except Exception as e:
            logger.error(f"Error parsing article HTML: {str(e)}")
            return {
                "title": "",
                "publication_date": None,
                "author": None,
                "snippet": "",
                "full_text": "",
                "is_parsed": False
            }

    @staticmethod
    def normalize_date_str(date_str: Optional[str]) -> Optional[str]:
        """Converts arbitrary date strings into standard ISO 8601 YYYY-MM-DD format."""
        if not date_str:
            return None
        try:
            parsed = date_parser.parse(str(date_str), fuzzy=True)
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            return str(date_str).strip()[:10]
