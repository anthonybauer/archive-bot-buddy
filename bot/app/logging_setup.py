"""Logging that never prints the bot token."""

from __future__ import annotations

import logging
import re

from .config import settings


class SecretFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        token = settings.bot_token
        if token:
            try:
                record.msg = str(record.msg).replace(token, "***")
            except Exception:  # pragma: no cover
                pass
        record.msg = re.sub(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b", "***", str(record.msg))
        return True


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    )
    handler.addFilter(SecretFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, settings.log_level, logging.INFO))
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
