"""Tiny SQLite persistence layer (no ORM needed)."""

from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    telegram_channel_id INTEGER,
    telegram_message_id INTEGER,
    downloaded_at TEXT NOT NULL,
    source TEXT,
    media_title TEXT,
    status TEXT NOT NULL,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_downloads_norm ON downloads (normalized_url);
CREATE INDEX IF NOT EXISTS idx_downloads_time ON downloads (downloaded_at);

CREATE TABLE IF NOT EXISTS seen_channels (
    chat_id INTEGER PRIMARY KEY,
    title TEXT,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processed_messages (
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (chat_id, message_id)
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_channel_id INTEGER NOT NULL UNIQUE,
    title TEXT,
    username TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    detected_at TEXT NOT NULL,
    approved_at TEXT,
    last_activity_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_channels_status ON channels (status);
"""

STATUSES = ("pending", "active", "disabled")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class DownloadRow:
    id: int
    source_url: str
    normalized_url: str
    telegram_channel_id: int | None
    telegram_message_id: int | None
    downloaded_at: str
    source: str | None
    media_title: str | None
    status: str
    error: str | None


class Database:
    """Thread-safe-enough SQLite wrapper; all calls go through a worker thread."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    async def _run(self, fn, *args: Any) -> Any:
        async with self._lock:
            return await asyncio.to_thread(fn, *args)

    # --- writes -----------------------------------------------------------
    def _record(self, **kw: Any) -> int:
        cur = self._conn.execute(
            """INSERT INTO downloads
               (source_url, normalized_url, telegram_channel_id, telegram_message_id,
                downloaded_at, source, media_title, status, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                kw["source_url"],
                kw["normalized_url"],
                kw.get("telegram_channel_id"),
                kw.get("telegram_message_id"),
                _now(),
                kw.get("source"),
                kw.get("media_title"),
                kw["status"],
                kw.get("error"),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid or 0)

    async def record_download(self, **kw: Any) -> int:
        return await self._run(lambda: self._record(**kw))

    def _remember_channel(self, chat_id: int, title: str | None) -> None:
        self._conn.execute(
            """INSERT INTO seen_channels (chat_id, title, last_seen_at) VALUES (?, ?, ?)
               ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title,
               last_seen_at=excluded.last_seen_at""",
            (chat_id, title, _now()),
        )
        self._conn.commit()

    async def remember_channel(self, chat_id: int, title: str | None) -> None:
        await self._run(self._remember_channel, chat_id, title)

    def _mark_message(self, chat_id: int, message_id: int) -> bool:
        try:
            self._conn.execute(
                "INSERT INTO processed_messages (chat_id, message_id, created_at) VALUES (?, ?, ?)",
                (chat_id, message_id, _now()),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    async def claim_message(self, chat_id: int, message_id: int) -> bool:
        """Returns True the first time a message is seen (loop/duplicate guard)."""
        return await self._run(self._mark_message, chat_id, message_id)

    # --- reads ------------------------------------------------------------
    def _find_success(self, normalized_url: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM downloads WHERE normalized_url = ? AND status = 'success' LIMIT 1",
            (normalized_url,),
        ).fetchone()

    async def find_successful(self, normalized_url: str) -> dict[str, Any] | None:
        row = await self._run(self._find_success, normalized_url)
        return dict(row) if row else None

    def _recent(self, limit: int) -> Iterable[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM downloads ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    async def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        return [dict(r) for r in await self._run(self._recent, limit)]

    def _stats(self) -> dict[str, int]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        row = self._conn.execute(
            """SELECT
                 COUNT(*) FILTER (WHERE downloaded_at LIKE ?) AS today,
                 COUNT(*) FILTER (WHERE status='success') AS ok,
                 COUNT(*) FILTER (WHERE status='failed') AS failed
               FROM downloads""",
            (f"{today}%",),
        ).fetchone()
        return {"today": row["today"] or 0, "success": row["ok"] or 0, "failed": row["failed"] or 0}

    async def stats(self) -> dict[str, int]:
        return await self._run(self._stats)

    def _channels(self) -> Iterable[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM seen_channels ORDER BY last_seen_at DESC LIMIT 10"
        ).fetchall()

    async def seen_channels(self) -> list[dict[str, Any]]:
        return [dict(r) for r in await self._run(self._channels)]
