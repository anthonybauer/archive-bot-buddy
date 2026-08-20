"""Entry point: runs the Telegram bot and the dashboard in one process."""

from __future__ import annotations

import asyncio
import logging

import uvicorn

from .bot import run_bot
from .config import settings
from .database import Database
from .logging_setup import setup_logging
from .web import create_app

log = logging.getLogger("main")


async def main() -> None:
    setup_logging()
    log.info("Bot starting")

    db = Database(settings.db_path)
    app = create_app(db)

    server = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=settings.port, log_level="warning")
    )
    tasks = [asyncio.create_task(server.serve())]

    if settings.bot_token:
        tasks.append(asyncio.create_task(run_bot(settings, db)))
    else:
        log.error("BOT_TOKEN is not set. Dashboard only — paste your token into .env and restart.")

    # One-time, non-destructive migration: legacy .env channels become active in SQLite.
    for chat_id in settings.bootstrap_channel_ids:
        created = await db.ensure_channel(chat_id, status="active")
        if created:
            log.info("Imported channel %s from environment as ACTIVE", chat_id)

    if not await db.active_channel_ids():
        log.warning(
            "No active channels yet. Safe setup mode: post in your channel, then approve it "
            "on the dashboard Channels page."
        )

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
