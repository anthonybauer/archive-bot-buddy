"""Shared runtime state exposed to the dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RuntimeState:
    bot_online: bool = False
    telegram_ok: bool = False
    telegram_error: str = ""
    bot_username: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    queue_size: int = 0
    active_downloads: int = 0


state = RuntimeState()
