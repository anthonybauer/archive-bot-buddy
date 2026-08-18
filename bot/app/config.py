"""Application configuration, loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _str(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    allowed_channel_id: int | None
    delete_original: bool
    skip_duplicates: bool
    include_source_url: bool
    max_concurrent_downloads: int
    download_retries: int
    download_timeout: int
    max_upload_mb: int
    cookies_file: str
    admin_username: str
    admin_password: str
    port: int
    data_dir: Path
    downloads_dir: Path
    log_level: str

    @property
    def db_path(self) -> Path:
        return self.data_dir / "bot.db"

    @property
    def configured(self) -> bool:
        return bool(self.bot_token)

    @property
    def cookies_path(self) -> Path | None:
        if not self.cookies_file:
            return None
        path = Path(self.cookies_file)
        return path if path.is_file() else None


def load_settings() -> Settings:
    channel_raw = _str("ALLOWED_CHANNEL_ID")
    channel_id: int | None
    try:
        channel_id = int(channel_raw) if channel_raw else None
    except ValueError:
        channel_id = None

    data_dir = Path(_str("DATA_DIR", "/data"))
    downloads_dir = Path(_str("DOWNLOADS_DIR", "/downloads"))
    data_dir.mkdir(parents=True, exist_ok=True)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot_token=_str("BOT_TOKEN"),
        allowed_channel_id=channel_id,
        delete_original=_bool("DELETE_ORIGINAL", True),
        skip_duplicates=_bool("SKIP_DUPLICATES", True),
        include_source_url=_bool("INCLUDE_SOURCE_URL", False),
        max_concurrent_downloads=max(1, min(_int("MAX_CONCURRENT_DOWNLOADS", 2), 5)),
        download_retries=max(0, min(_int("DOWNLOAD_RETRIES", 2), 5)),
        download_timeout=max(30, _int("DOWNLOAD_TIMEOUT", 600)),
        max_upload_mb=max(1, _int("MAX_UPLOAD_MB", 50)),
        cookies_file=_str("COOKIES_FILE"),
        admin_username=_str("ADMIN_USERNAME", "admin"),
        admin_password=_str("ADMIN_PASSWORD"),
        port=_int("PORT", 8080),
        data_dir=data_dir,
        downloads_dir=downloads_dir,
        log_level=_str("LOG_LEVEL", "INFO").upper(),
    )


settings = load_settings()
