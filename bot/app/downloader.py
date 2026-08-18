"""yt-dlp powered generic media downloader (no shell execution)."""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

from .config import Settings
from .urls import safe_filename, source_name

log = logging.getLogger("downloader")

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


class DownloadFailed(Exception):
    """Raised with a short, human-readable reason."""


@dataclass
class MediaItem:
    path: Path
    title: str
    is_video: bool
    duration: int | None = None
    width: int | None = None
    height: int | None = None

    @property
    def size_mb(self) -> float:
        return self.path.stat().st_size / (1024 * 1024)


@dataclass
class DownloadResult:
    items: list[MediaItem] = field(default_factory=list)
    title: str = ""
    source: str = ""
    workdir: Path | None = None

    def cleanup(self) -> None:
        if self.workdir and self.workdir.exists():
            shutil.rmtree(self.workdir, ignore_errors=True)


FRIENDLY_ERRORS: list[tuple[str, str]] = [
    ("login required", "This content is private and needs a login (cookies)."),
    ("cookies", "This content needs a login (cookies)."),
    ("rate-limit", "The website is rate-limiting us, try again later."),
    ("rate limit", "The website is rate-limiting us, try again later."),
    ("429", "The website is rate-limiting us, try again later."),
    ("private", "This content is private."),
    ("unavailable", "This content is unavailable or was removed."),
    ("not found", "This content was not found."),
    ("age", "This content is age-restricted and needs a login."),
    ("unsupported url", "This link is not supported."),
    ("no video", "No video was found at this link."),
    ("timed out", "The download timed out."),
    ("timeout", "The download timed out."),
    ("no space", "The server has run out of disk space."),
]


def humanize(error: str) -> str:
    low = error.lower()
    for needle, message in FRIENDLY_ERRORS:
        if needle in low:
            return message
    return "The video could not be downloaded."


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def ffmpeg_version() -> str | None:
    exe = shutil.which("ffmpeg")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=10)
        return out.stdout.splitlines()[0] if out.stdout else "unknown"
    except Exception:  # pragma: no cover - defensive
        return "unknown"


def _ydl_options(settings: Settings, workdir: Path) -> dict:
    opts: dict = {
        "outtmpl": str(workdir / "%(autonumber)03d-%(id).40s.%(ext)s"),
        "format": (
            f"bestvideo[filesize_approx<{settings.max_upload_mb}M]+bestaudio/"
            "best[ext=mp4]/best"
        ),
        "merge_output_format": "mp4",
        "noplaylist": False,
        "playlistend": 10,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "restrictfilenames": True,
        "socket_timeout": 30,
        "retries": settings.download_retries,
        "concurrent_fragment_downloads": 2,
        "writethumbnail": False,
        "ignoreerrors": "only_download",
        "max_filesize": settings.max_upload_mb * 1024 * 1024 * 4,
    }
    cookies = settings.cookies_path
    if cookies:
        opts["cookiefile"] = str(cookies)
    return opts


def _collect(workdir: Path, info: dict, source: str) -> list[MediaItem]:
    items: list[MediaItem] = []
    title = safe_filename(info.get("title") or "", "video")
    for path in sorted(workdir.iterdir()):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext in VIDEO_EXT:
            items.append(MediaItem(path=path, title=title, is_video=True,
                                   duration=info.get("duration"),
                                   width=info.get("width"), height=info.get("height")))
        elif ext in IMAGE_EXT:
            items.append(MediaItem(path=path, title=title, is_video=False))
    return items


def _download_sync(url: str, settings: Settings) -> DownloadResult:
    workdir = Path(tempfile.mkdtemp(prefix="dl-", dir=str(settings.downloads_dir)))
    try:
        with YoutubeDL(_ydl_options(settings, workdir)) as ydl:
            info = ydl.extract_info(url, download=True)
        if info is None:
            raise DownloadFailed("No video was found at this link.")
        if "entries" in info and info.get("entries"):
            entries = [e for e in info["entries"] if e]
            info = {**(entries[0] or {}), "title": info.get("title") or (entries[0] or {}).get("title")}
        items = _collect(workdir, info or {}, url)
        if not items:
            raise DownloadFailed("No downloadable media was found at this link.")
        return DownloadResult(
            items=items,
            title=(info or {}).get("title") or "",
            source=source_name(url),
            workdir=workdir,
        )
    except DownloadFailed:
        shutil.rmtree(workdir, ignore_errors=True)
        raise
    except (DownloadError, ExtractorError) as exc:
        shutil.rmtree(workdir, ignore_errors=True)
        log.warning("yt-dlp failed for %s: %s", url, exc)
        raise DownloadFailed(humanize(str(exc))) from exc
    except OSError as exc:
        shutil.rmtree(workdir, ignore_errors=True)
        log.exception("filesystem error while downloading")
        raise DownloadFailed(humanize(str(exc))) from exc
    except Exception as exc:  # pragma: no cover - defensive
        shutil.rmtree(workdir, ignore_errors=True)
        log.exception("unexpected download error")
        raise DownloadFailed("Unexpected error while downloading.") from exc


async def download(url: str, settings: Settings) -> DownloadResult:
    """Download a URL with retries and a hard timeout."""
    last: Exception | None = None
    for attempt in range(settings.download_retries + 1):
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_download_sync, url, settings),
                timeout=settings.download_timeout,
            )
        except asyncio.TimeoutError as exc:
            last = DownloadFailed("The download timed out.")
            log.warning("download timeout (attempt %s) for %s", attempt + 1, url)
            _ = exc
        except DownloadFailed as exc:
            last = exc
            recoverable = "rate-limit" in str(exc).lower() or "timed out" in str(exc).lower()
            if not recoverable:
                break
            log.info("retrying download (attempt %s)", attempt + 2)
        await asyncio.sleep(2 * (attempt + 1))
    raise last or DownloadFailed("The video could not be downloaded.")
