"""
SQLite Database module for verification history, caching, and source settings.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path


DB_FILE = Path(__file__).resolve().parent.parent.parent / "truth_checker.db"


def get_db_connection() -> sqlite3.Connection:
    """Returns an initialized SQLite database connection."""
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes tables for verifications, cache, and source settings."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verifications (
                id TEXT PRIMARY KEY,
                claim TEXT NOT NULL,
                original_text TEXT,
                url TEXT,
                language TEXT NOT NULL,
                verdict TEXT NOT NULL,
                confidence REAL NOT NULL,
                reason TEXT NOT NULL,
                supporting_sources TEXT,
                contradicting_sources TEXT,
                primary_sources TEXT,
                articles_json TEXT,
                stats_json TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Search / Article cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                cache_key TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                ttl REAL NOT NULL
            )
        """)

        # Source settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_overrides (
                source_id TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1,
                priority TEXT,
                updated_at TEXT NOT NULL
            )
        """)

        conn.commit()
    finally:
        conn.close()


def save_verification(record: Dict[str, Any]) -> None:
    """Saves a completed verification result into SQLite."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO verifications (
                id, claim, original_text, url, language, verdict, confidence,
                reason, supporting_sources, contradicting_sources, primary_sources,
                articles_json, stats_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["id"],
            record["claim"],
            record.get("original_text", ""),
            record.get("url", ""),
            record["language"],
            record["verdict"],
            float(record["confidence"]),
            record["reason"],
            json.dumps(record.get("supporting_sources", []), ensure_ascii=False),
            json.dumps(record.get("contradicting_sources", []), ensure_ascii=False),
            json.dumps(record.get("primary_sources", []), ensure_ascii=False),
            json.dumps(record.get("articles", []), ensure_ascii=False),
            json.dumps(record.get("stats", {}), ensure_ascii=False),
            record.get("created_at", datetime.now(timezone.utc).isoformat())
        ))
        conn.commit()
    finally:
        conn.close()


def get_verifications(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves recent verification history."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, claim, original_text, url, language, verdict, confidence,
                   reason, supporting_sources, contradicting_sources, primary_sources,
                   articles_json, stats_json, created_at
            FROM verifications
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "claim": r["claim"],
                "original_text": r["original_text"],
                "url": r["url"],
                "language": r["language"],
                "verdict": r["verdict"],
                "confidence": r["confidence"],
                "reason": r["reason"],
                "supporting_sources": json.loads(r["supporting_sources"] or "[]"),
                "contradicting_sources": json.loads(r["contradicting_sources"] or "[]"),
                "primary_sources": json.loads(r["primary_sources"] or "[]"),
                "articles": json.loads(r["articles_json"] or "[]"),
                "stats": json.loads(r["stats_json"] or "{}"),
                "created_at": r["created_at"]
            })
        return results
    finally:
        conn.close()


def get_verification_by_id(verification_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single verification by its UUID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, claim, original_text, url, language, verdict, confidence,
                   reason, supporting_sources, contradicting_sources, primary_sources,
                   articles_json, stats_json, created_at
            FROM verifications
            WHERE id = ?
        """, (verification_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return {
            "id": r["id"],
            "claim": r["claim"],
            "original_text": r["original_text"],
            "url": r["url"],
            "language": r["language"],
            "verdict": r["verdict"],
            "confidence": r["confidence"],
            "reason": r["reason"],
            "supporting_sources": json.loads(r["supporting_sources"] or "[]"),
            "contradicting_sources": json.loads(r["contradicting_sources"] or "[]"),
            "primary_sources": json.loads(r["primary_sources"] or "[]"),
            "articles": json.loads(r["articles_json"] or "[]"),
            "stats": json.loads(r["stats_json"] or "{}"),
            "created_at": r["created_at"]
        }
    finally:
        conn.close()


def delete_verification(verification_id: str) -> bool:
    """Deletes a verification record by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM verifications WHERE id = ?", (verification_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def clear_all_history() -> None:
    """Clears all verification records."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM verifications")
        conn.commit()
    finally:
        conn.close()


# Initialize database on module import
init_db()
