# Telegram Video Archive Bot

Share a video link into your private Telegram channel — the bot downloads the video
with yt-dlp + FFmpeg, uploads it back as a playable video, and deletes the link post.

**Non-technical setup instructions: see [`SETUP - START HERE.md`](./SETUP%20-%20START%20HERE.md).**

Quick start on an Ubuntu server with Docker installed:

```bash
cp .env.example .env   # paste BOT_TOKEN + admin password
docker compose up -d
```

Dashboard: `http://YOUR_SERVER_IP:8080` (Basic auth with `ADMIN_USERNAME` / `ADMIN_PASSWORD`).

Stack: Python 3.12 · aiogram 3 · yt-dlp · FFmpeg · FastAPI · SQLite · Docker.
