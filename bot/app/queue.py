"""Bounded async download queue: 1-2 jobs at a time by default."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

log = logging.getLogger("queue")


@dataclass
class Job:
    chat_id: int
    message_id: int
    urls: list[str]


class DownloadQueue:
    def __init__(self, worker: Callable[[Job], Awaitable[None]], concurrency: int) -> None:
        self._queue: asyncio.Queue[Job] = asyncio.Queue()
        self._worker = worker
        self._concurrency = concurrency
        self._tasks: list[asyncio.Task] = []

    @property
    def size(self) -> int:
        return self._queue.qsize()

    async def start(self) -> None:
        for index in range(self._concurrency):
            self._tasks.append(asyncio.create_task(self._run(index)))
        log.info("Download queue started with %s worker(s)", self._concurrency)

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

    async def put(self, job: Job) -> None:
        await self._queue.put(job)
        log.info("Queued %s URL(s) from message %s", len(job.urls), job.message_id)

    async def _run(self, index: int) -> None:
        while True:
            job = await self._queue.get()
            try:
                await self._worker(job)
            except asyncio.CancelledError:
                raise
            except Exception:  # pragma: no cover - worker must never die
                log.exception("worker %s crashed while handling a job", index)
            finally:
                self._queue.task_done()
