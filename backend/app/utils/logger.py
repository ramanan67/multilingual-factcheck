"""
Structured logging module for News Truth Checker.
"""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Formats logs as clean readable console output with timestamps."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        msg = record.getMessage()
        extra = ""
        if hasattr(record, "extra_data") and record.extra_data:
            try:
                extra = f" | {json.dumps(record.extra_data, ensure_ascii=False)}"
            except Exception:
                extra = f" | {record.extra_data}"
        return f"[{timestamp}] [{level:<7}] [{record.name}] {msg}{extra}"


def setup_logger(name: str = "truth_checker", level: int = logging.INFO) -> logging.Logger:
    """Creates or retrieves a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger()
