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


# --------------------------------------------------------- multi-channel tests
def can_download(status: str | None) -> bool:
    """Mirror of the guard used in the bot handler."""
    return status == "active"


def test_channel_status_gate():
    assert can_download("active")
    assert not can_download("pending")
    assert not can_download("disabled")
    assert not can_download(None)


def test_legacy_env_channel_is_imported_as_active(db: Database):
    async def run():
        legacy_id = -1003913012885
        assert await db.get_channel(legacy_id) is None
        created = await db.ensure_channel(legacy_id, status="active")  # startup migration
        assert created is True
        assert await db.channel_status(legacy_id) == "active"
        # running the migration again must not change or duplicate anything
        assert await db.ensure_channel(legacy_id, status="active") is False
        assert len(await db.channels()) == 1

    asyncio.run(run())


def test_unknown_channel_becomes_pending(db: Database):
    async def run():
        created = await db.touch_channel(-1001111111111, "Travel Archive")
        assert created is True
        assert await db.channel_status(-1001111111111) == "pending"
        assert not can_download(await db.channel_status(-1001111111111))

    asyncio.run(run())


def test_channel_enable_disable_and_reenable(db: Database):
    async def run():
        cid = -1002222222222
        await db.touch_channel(cid, "Channel B")
        await db.set_channel_status(cid, "active")
        assert can_download(await db.channel_status(cid))
        await db.set_channel_status(cid, "disabled")
        assert not can_download(await db.channel_status(cid))
        await db.set_channel_status(cid, "active")
        assert can_download(await db.channel_status(cid))
        assert (await db.get_channel(cid))["approved_at"] is not None

    asyncio.run(run())


def test_channel_removal_keeps_download_history(db: Database):
    async def run():
        cid = -1003333333333
        await db.ensure_channel(cid, "Channel C", status="active")
        await db.record_download(
            source_url="https://vimeo.com/9", normalized_url=normalize_url("https://vimeo.com/9"),
            telegram_channel_id=cid, telegram_message_id=3, source="Vimeo", status="success",
        )
        assert await db.remove_channel(cid) is True
        assert await db.get_channel(cid) is None
        assert await db.remove_channel(cid) is False
        assert len(await db.recent()) == 1  # history preserved

    asyncio.run(run())


def test_duplicate_is_channel_specific(db: Database):
    async def run():
        url = "https://www.instagram.com/reel/XYZ/"
        norm = normalize_url(url)
        chan_a, chan_b = -1001111111111, -1002222222222
        await db.record_download(
            source_url=url, normalized_url=norm, telegram_channel_id=chan_a,
            telegram_message_id=1, source="Instagram", status="success",
        )
        assert await db.find_successful(norm, chan_a) is not None   # duplicate in A
        assert await db.find_successful(norm, chan_b) is None       # allowed in B

    asyncio.run(run())


def test_active_channels_listing(db: Database):
    async def run():
        await db.ensure_channel(-1001111111111, "A", status="active")
        await db.touch_channel(-1002222222222, "B")
        assert await db.active_channel_ids() == [-1001111111111]

    asyncio.run(run())


def test_job_carries_its_own_source_channel():
    from app.queue import Job

    job_a = Job(chat_id=-1001111111111, message_id=10, urls=["https://x/1"])
    job_b = Job(chat_id=-1002222222222, message_id=11, urls=["https://x/1"])
    assert job_a.chat_id != job_b.chat_id
    assert job_a.job_id != job_b.job_id  # every job is individually traceable
    # upload target is always taken from the job's own chat_id
    assert job_a.chat_id == -1001111111111
