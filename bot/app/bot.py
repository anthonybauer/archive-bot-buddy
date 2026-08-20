"""Telegram bot: listens to channel posts and archives shared videos."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile, Message

from .config import Settings
from .database import Database
from .downloader import DownloadFailed, DownloadResult, MediaItem, download
from .queue import DownloadQueue, Job
from .state import state
from .urls import extract_urls, normalize_url, source_name

log = logging.getLogger("bot")


class ArchiveBot:
    def __init__(self, settings: Settings, db: Database) -> None:
        self.settings = settings
        self.db = db
        self.bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=None),
        )
        self.dp = Dispatcher()
        self.queue = DownloadQueue(self._process_job, settings.max_concurrent_downloads)
        self._register()

    # ------------------------------------------------------------------ setup
    def _register(self) -> None:
        self.dp.channel_post.register(self._on_channel_post, F.text | F.caption)
        self.dp.edited_channel_post.register(self._on_channel_post, F.text | F.caption)

    async def run(self) -> None:
        me = await self.bot.get_me()
        state.bot_username = me.username or ""
        state.bot_online = True
        state.telegram_ok = True
        state.telegram_error = ""
        log.info("Bot started as @%s", state.bot_username)
        await self.queue.start()
        try:
            await self.dp.start_polling(
                self.bot,
                allowed_updates=["channel_post", "edited_channel_post", "message"],
                handle_signals=False,
            )
        finally:
            state.bot_online = False
            await self.queue.stop()
            await self.bot.session.close()

    # --------------------------------------------------------------- handlers
    async def _on_channel_post(self, message: Message) -> None:
        chat = message.chat
        await self.db.remember_channel(chat.id, chat.title)
        # Auto-discovery: unknown channels are stored as "pending" (never downloaded).
        created = await self.db.touch_channel(chat.id, chat.title, getattr(chat, "username", None))
        if created:
            log.info("New channel detected and marked pending: %s (%s)", chat.title, chat.id)
        log.info("Channel post received from %s (%s)", chat.title, chat.id)

        # Loop protection: never react to our own uploads (they carry no URLs anyway).
        if message.from_user and message.from_user.is_bot:
            return

        text = message.text or message.caption or ""
        urls = extract_urls(text)
        if not urls:
            return

        status = await self.db.channel_status(chat.id)
        if status != "active":
            log.info(
                "Channel %s is '%s' — ignoring URLs. Approve it on the Channels page.",
                chat.id,
                status or "pending",
            )
            return

        if not await self.db.claim_message(chat.id, message.message_id):
            log.info("Message %s already processed, skipping", message.message_id)
            return

        log.info("Detected %s URL(s): %s", len(urls), ", ".join(source_name(u) for u in urls))
        state.queue_size = self.queue.size + 1
        await self.queue.put(Job(chat_id=chat.id, message_id=message.message_id, urls=urls))

    # ----------------------------------------------------------------- worker
    async def _process_job(self, job: Job) -> None:
        state.active_downloads += 1
        state.queue_size = self.queue.size
        failures: list[str] = []
        try:
            for url in job.urls:
                ok, reason = await self._process_url(job, url)
                if not ok:
                    failures.append(f"{source_name(url)}: {reason}")
        finally:
            state.active_downloads -= 1
            state.queue_size = self.queue.size

        if failures:
            await self._notify(
                job.chat_id,
                "⚠️ Could not download this video.\n" + "\n".join(f"• {f}" for f in failures),
            )
            return

        if self.settings.delete_original:
            try:
                await self.bot.delete_message(job.chat_id, job.message_id)
                log.info("Original URL post deleted")
            except TelegramAPIError as exc:
                log.warning("Could not delete original post: %s", exc)
                await self._notify(
                    job.chat_id,
                    "ℹ️ Video saved, but I could not delete the original link. "
                    "Please give me the 'Delete Messages' permission.",
                )

    async def _process_url(self, job: Job, url: str) -> tuple[bool, str]:
        normalized = normalize_url(url)
        if self.settings.skip_duplicates:
            existing = await self.db.find_successful(normalized, job.chat_id)
            if existing:
                log.info("Duplicate URL, already saved: %s", normalized)
                await self._notify(job.chat_id, "Already saved ✅")
                return True, ""

        log.info("Starting download from %s", source_name(url))
        result: DownloadResult | None = None
        try:
            result = await download(url, self.settings)
            log.info("Download complete (%s file(s))", len(result.items))

            too_big = [i for i in result.items if i.size_mb > self.settings.max_upload_mb]
            if too_big:
                raise DownloadFailed(
                    f"The video is too large to upload ({too_big[0].size_mb:.0f} MB, "
                    f"limit {self.settings.max_upload_mb} MB)."
                )

            log.info("Uploading to Telegram")
            for item in result.items:
                await self._upload(job.chat_id, item, result, url)
            log.info("Upload successful")

            await self.db.record_download(
                source_url=url,
                normalized_url=normalized,
                telegram_channel_id=job.chat_id,
                telegram_message_id=job.message_id,
                source=source_name(url),
                media_title=result.title[:200],
                status="success",
            )
            return True, ""
        except DownloadFailed as exc:
            await self._record_failure(job, url, normalized, str(exc))
            return False, str(exc)
        except TelegramAPIError as exc:
            reason = "Telegram refused the upload (file too large or missing permission)."
            log.warning("Telegram upload failed: %s", exc)
            await self._record_failure(job, url, normalized, reason)
            return False, reason
        except Exception:  # pragma: no cover - defensive
            log.exception("unexpected error while processing url")
            await self._record_failure(job, url, normalized, "Unexpected error.")
            return False, "Unexpected error."
        finally:
            if result:
                result.cleanup()
                log.info("Temporary files cleaned")

    async def _record_failure(self, job: Job, url: str, normalized: str, reason: str) -> None:
        await self.db.record_download(
            source_url=url,
            normalized_url=normalized,
            telegram_channel_id=job.chat_id,
            telegram_message_id=job.message_id,
            source=source_name(url),
            media_title=None,
            status="failed",
            error=reason[:300],
        )

    def _caption(self, result: DownloadResult, url: str) -> str:
        lines: list[str] = []
        if result.title:
            lines.append(result.title[:180])
        lines.append(f"Source: {source_name(url)}")
        if self.settings.include_source_url:
            lines.append(url)
        return "\n".join(lines)

    async def _upload(self, chat_id: int, item: MediaItem, result: DownloadResult, url: str) -> None:
        file = FSInputFile(str(item.path), filename=item.path.name)
        caption = self._caption(result, url)
        if item.is_video:
            await self.bot.send_video(
                chat_id,
                video=file,
                caption=caption,
                supports_streaming=True,
                duration=item.duration or None,
                width=item.width or None,
                height=item.height or None,
            )
        else:
            await self.bot.send_photo(chat_id, photo=file, caption=caption)

    async def _notify(self, chat_id: int, text: str) -> None:
        try:
            await self.bot.send_message(chat_id, text, disable_web_page_preview=True)
        except TelegramAPIError as exc:
            log.warning("Could not post status message: %s", exc)


async def run_bot(settings: Settings, db: Database) -> None:
    while True:
        try:
            await ArchiveBot(settings, db).run()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - keeps the bot alive
            state.bot_online = False
            state.telegram_ok = False
            state.telegram_error = type(exc).__name__
            log.exception("Bot crashed, restarting in 15s")
            await asyncio.sleep(15)
