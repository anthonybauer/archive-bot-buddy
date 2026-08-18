"""Tiny password-protected FastAPI dashboard."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import Database
from .downloader import ffmpeg_available, ffmpeg_version
from .state import state

try:
    from yt_dlp.version import __version__ as YTDLP_VERSION
except Exception:  # pragma: no cover
    YTDLP_VERSION = "unknown"

security = HTTPBasic()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    user_ok = secrets.compare_digest(credentials.username, settings.admin_username or "admin")
    pass_ok = bool(settings.admin_password) and secrets.compare_digest(
        credentials.password, settings.admin_password
    )
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorised",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def create_app(db: Database) -> FastAPI:
    app = FastAPI(title="Telegram Video Archive", docs_url=None, redoc_url=None)

    def base_context(request: Request, page: str) -> dict:
        return {
            "request": request,
            "page": page,
            "channel_id": settings.allowed_channel_id,
            "bot_username": state.bot_username,
        }

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "bot_online": state.bot_online})

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, _: str = Depends(require_admin)) -> HTMLResponse:
        stats = await db.stats()
        uptime = datetime.now(timezone.utc) - state.started_at
        ctx = base_context(request, "dashboard")
        ctx.update(
            stats=stats,
            recent=await db.recent(10),
            seen_channels=await db.seen_channels(),
            ffmpeg_ok=ffmpeg_available(),
            ffmpeg_version=ffmpeg_version(),
            ytdlp_version=YTDLP_VERSION,
            state=state,
            uptime=str(uptime).split(".")[0],
        )
        return templates.TemplateResponse("dashboard.html", ctx)

    @app.get("/downloads", response_class=HTMLResponse)
    async def downloads(request: Request, _: str = Depends(require_admin)) -> HTMLResponse:
        ctx = base_context(request, "downloads")
        ctx.update(rows=await db.recent(100))
        return templates.TemplateResponse("downloads.html", ctx)

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request, _: str = Depends(require_admin)) -> HTMLResponse:
        ctx = base_context(request, "settings")
        ctx.update(
            values=[
                ("BOT_TOKEN", "configured ✅" if settings.bot_token else "missing ❌",
                 "Your token from BotFather. Never shown here."),
                ("ALLOWED_CHANNEL_ID", settings.allowed_channel_id or "not set ❌",
                 "The only channel the bot will listen to."),
                ("DELETE_ORIGINAL", settings.delete_original,
                 "Delete the link post after the video is uploaded."),
                ("SKIP_DUPLICATES", settings.skip_duplicates,
                 "Reply 'Already saved ✅' instead of downloading twice."),
                ("INCLUDE_SOURCE_URL", settings.include_source_url,
                 "Add the original link to the video caption."),
                ("MAX_CONCURRENT_DOWNLOADS", settings.max_concurrent_downloads,
                 "How many videos download at the same time."),
                ("DOWNLOAD_RETRIES", settings.download_retries,
                 "Retries after a temporary network error."),
                ("DOWNLOAD_TIMEOUT", f"{settings.download_timeout}s",
                 "Give up on a download after this time."),
                ("MAX_UPLOAD_MB", settings.max_upload_mb,
                 "Telegram bot upload limit (50 MB unless you run a local Bot API server)."),
                ("COOKIES_FILE", settings.cookies_file or "not set (optional)",
                 "Optional cookies.txt for private/logged-in content."),
                ("ADMIN_USERNAME", settings.admin_username, "Login for this dashboard."),
                ("ADMIN_PASSWORD", "configured ✅" if settings.admin_password else "missing ❌",
                 "Login for this dashboard. Never shown here."),
                ("PORT", settings.port, "Dashboard port."),
            ]
        )
        return templates.TemplateResponse("settings.html", ctx)

    @app.get("/setup", response_class=HTMLResponse)
    async def setup(request: Request, _: str = Depends(require_admin)) -> HTMLResponse:
        ctx = base_context(request, "setup")
        ctx.update(seen_channels=await db.seen_channels())
        return templates.TemplateResponse("setup.html", ctx)

    return app
