import asyncio
from pathlib import Path

import pytest

from app.database import Database
from app.downloader import humanize
from app.urls import normalize_url


def allowed(chat_id: int, configured: int | None) -> bool:
    """Mirror of the guard used in the bot handler."""
    return configured is not None and chat_id == configured


def test_allowed_channel_validation():
    assert allowed(-1001234567890, -1001234567890)
    assert not allowed(-1009999999999, -1001234567890)
    assert not allowed(-1001234567890, None)  # safe setup mode: nothing runs


@pytest.fixture()
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test.db")


def test_duplicate_detection(db: Database):
    async def run():
        url = "https://www.instagram.com/reel/ABC/?utm_source=x"
        norm = normalize_url(url)
        assert await db.find_successful(norm) is None
        await db.record_download(
            source_url=url, normalized_url=norm, telegram_channel_id=-100,
            telegram_message_id=1, source="Instagram", media_title="t", status="success",
        )
        assert await db.find_successful(norm) is not None
        # same video shared again with different tracking params
        assert await db.find_successful(normalize_url("https://instagram.com/reel/ABC/")) is not None

    asyncio.run(run())


def test_failed_download_is_not_a_duplicate(db: Database):
    async def run():
        norm = normalize_url("https://vimeo.com/1")
        await db.record_download(
            source_url="https://vimeo.com/1", normalized_url=norm,
            telegram_channel_id=-100, telegram_message_id=2, status="failed", error="nope",
        )
        assert await db.find_successful(norm) is None

    asyncio.run(run())


def test_message_claim_prevents_double_processing(db: Database):
    async def run():
        assert await db.claim_message(-100, 5) is True
        assert await db.claim_message(-100, 5) is False

    asyncio.run(run())


def test_stats_and_recent_work_on_empty_database(db: Database):
    async def run():
        assert await db.stats() == {"today": 0, "success": 0, "failed": 0}
        assert await db.recent() == []
        assert await db.seen_channels() == []

    asyncio.run(run())


def test_error_messages_are_human_readable():
    assert "login" in humanize("ERROR: Requested content is not available, login required").lower()
    assert "not supported" in humanize("Unsupported URL: https://example.com/x").lower()
    assert humanize("weird internal thing") == "The video could not be downloaded."
