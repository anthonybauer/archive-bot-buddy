# Channel Video Archive

I want you to build a complete, production-ready Telegram bot application for me.

IMPORTANT:
I am NOT a developer. I have already created the Telegram bot using BotFather and I have the BOT TOKEN.

I do not understand Python, servers, Docker, webhooks, environment variables, VPS configuration, databases, or deployment very well.

Therefore, you must build this project so that I can operate it with minimal technical knowledge.

Do NOT just give me code snippets or explanations. Build the actual complete application, all files, configuration, deployment setup, and a very clear step-by-step setup guide.

# GOAL

I have a private Telegram channel.

I have already created a Telegram bot using BotFather.

I will add the bot to my Telegram channel as an administrator.

The workflow must be:

1. I see a video/Reel/Short on Instagram, TikTok, YouTube, X/Twitter, Facebook, etc.
2. On my phone I tap Share.
3. I choose Telegram.
4. I send/share the URL into my private Telegram channel.
5. The Telegram bot detects the URL posted in the channel.
6. The bot downloads the actual video from the URL.
7. The bot uploads the actual video file back into the SAME Telegram channel.
8. After successful upload, the original Telegram post containing only the URL should be deleted.
9. The downloaded temporary file should also be deleted from the server after the upload is complete.

The end result should be that my Telegram channel becomes my personal video archive.

I should see the actual videos inside Telegram, not just external links.

# IMPORTANT USER EXPERIENCE

There should be NO need for commands such as:

/start
/download
/save

I do not want to interact with the bot directly.

The bot should silently monitor the Telegram channel and automatically react whenever I share a supported URL into that channel.

Example:

I share:

https://www.instagram.com/reel/ABC123/

The bot downloads the Reel.

Then the bot posts the actual MP4 video into the same Telegram channel.

Then it deletes:

https://www.instagram.com/reel/ABC123/

So only the downloaded video remains.

# SUPPORTED SOURCES

Use yt-dlp as the primary downloading engine.

Support, where technically possible:

* Instagram posts
* Instagram Reels
* TikTok
* YouTube
* YouTube Shorts
* X / Twitter
* Facebook
* Vimeo
* Reddit videos
* other websites supported by yt-dlp

Do NOT hard-code the downloader specifically for Instagram.

Create a general URL downloader architecture using yt-dlp.

# TELEGRAM

Use the Telegram Bot API.

The bot must listen for Telegram channel posts, including the `channel_post` update type.

It must work when the bot is an administrator of my private Telegram channel.

Use a modern, maintained Telegram framework if appropriate.

Python + aiogram is acceptable.

If another architecture is materially better for deployment, you may use it, but explain why.

# BOT TOKEN

I already have the token from BotFather.

NEVER hard-code the token into source code.

Use an environment variable:

BOT_TOKEN

Create a simple Settings / Environment Variables section in the project where I can paste the token.

Also create:

ALLOWED_CHANNEL_ID

The bot must ONLY process messages from my Telegram channel.

It must ignore all other channels/chats/users.

# SECURITY

Security is important.

Implement:

* BOT_TOKEN stored only as a secret/environment variable
* ALLOWED_CHANNEL_ID restriction
* URL validation
* safe filenames
* temporary download directories
* automatic temporary-file cleanup
* protection against duplicate processing
* reasonable file-size limits
* download timeout
* error handling
* no arbitrary shell execution from user-controlled input
* no unrestricted file path handling

Never expose BOT_TOKEN in logs.

# DOWNLOAD LOGIC

When a new channel post arrives:

1. Check whether it contains one or more URLs.
2. Validate the URL.
3. Check that the message originated from ALLOWED_CHANNEL_ID.
4. Download the media.
5. Prefer the highest practical video quality that can be uploaded to Telegram.
6. Prefer MP4 with H.264/AAC where practical.
7. Use FFmpeg when remuxing or conversion is required.
8. Upload the result into the same Telegram channel.
9. Use Telegram video upload so it appears as a playable streaming video whenever possible.
10. Only after successful upload, delete the original link message.
11. Delete all local temporary files.

If download/upload fails:

DO NOT delete the original URL.

Instead, post a small error message in the Telegram channel such as:

⚠️ Could not download this video.

Include a short, human-readable reason, but never include secrets or huge technical stack traces.

# MULTIPLE URLs

Support multiple URLs in one Telegram message.

If I send:

Instagram URL
TikTok URL
YouTube URL

the bot should process all three.

Only delete the original post after all URLs have been successfully processed.

If some downloads fail, preserve the original message and report which links failed.

# MULTIPLE MEDIA ITEMS / CAROUSELS

If a source URL contains multiple media items, such as an Instagram carousel containing several videos/images, attempt to save all available downloadable media.

If there are multiple videos, upload them individually or as a Telegram media group when practical.

# DUPLICATES

Prevent accidental duplicate saves.

Store enough information to determine whether the exact same source URL has already been successfully downloaded.

SQLite is sufficient.

Database table could contain:

* id
* source_url
* normalized_url
* telegram_channel_id
* telegram_message_id
* downloaded_at
* source
* media_title
* status

If the exact URL was already successfully saved, do not download it again.

Instead, optionally reply:

Already saved ✅

Make this behavior configurable.

# DATABASE

Use SQLite because I want the setup to remain simple.

Store database data persistently.

Do NOT require PostgreSQL for the first version.

# INSTAGRAM AUTHENTICATION / COOKIES

Some Instagram videos may require login/cookies.

Design the application so cookies can optionally be supplied later.

Support an optional environment variable or mounted file:

COOKIES_FILE

If it is not configured, public videos should still be attempted normally.

Do NOT require Instagram username/password directly inside the code.

Use a Netscape-format cookies.txt compatible with yt-dlp.

Explain in the README how cookies could be added later, but keep this optional.

# VIDEO PROCESSING

Install and use FFmpeg.

Prefer downloading formats that do not require unnecessary transcoding.

If Telegram-compatible MP4 is available, use it directly.

Do not waste CPU re-encoding videos unless necessary.

If remuxing is sufficient, remux instead of re-encoding.

# LARGE FILES

Handle large files gracefully.

Before downloading/uploading, inspect metadata when possible.

If a file exceeds the practical upload limit of the chosen Telegram Bot API setup:

* do not crash
* preserve the original URL
* show a clear error message

Structure the code so support for a local Telegram Bot API server could be added later if I need larger uploads.

# DOWNLOAD QUEUE

Do not start unlimited parallel downloads.

Implement a simple async queue.

For the first version, process approximately 1-2 downloads at the same time.

Make concurrency configurable:

MAX_CONCURRENT_DOWNLOADS=2

This prevents Instagram/TikTok from blocking me because of too many simultaneous requests.

# RETRIES

Implement sensible retries:

DOWNLOAD_RETRIES=2

If a temporary network error occurs, retry before giving up.

Do not retry indefinitely.

# LOGGING

Create clear logs.

Example:

Bot started
Channel post received
Detected Instagram URL
Starting download
Download complete
Uploading to Telegram
Upload successful
Original URL post deleted
Temporary files cleaned

Do NOT expose sensitive information.

# ADMIN / HEALTH PAGE

Create a very simple web dashboard because I am not technical.

It does NOT need to be fancy.

It should show:

Bot status: Online / Offline

Telegram connection: OK / Error

Configured channel ID

yt-dlp version

FFmpeg available: Yes / No

Downloads today

Successful downloads

Failed downloads

Last 10 downloads

Source

Time

Status

Error if any

Also add a button or clear instruction to copy/view the Telegram Channel ID once it has been detected.

Do NOT expose the Telegram BOT_TOKEN anywhere in the interface.

# FIRST-TIME SETUP

Because I do not know my Telegram Channel ID yet, make first-time setup easy.

If ALLOWED_CHANNEL_ID is not configured yet:

Create a safe setup mode.

When the bot receives a channel post, log/display the channel:

Channel name
Channel ID

in the admin dashboard.

Then clearly tell me:

"Copy this Channel ID into ALLOWED_CHANNEL_ID."

Do not download media until ALLOWED_CHANNEL_ID has been configured.

If you can safely automate this configuration through the dashboard, do that.

# SIMPLE ADMIN PAGE

Create a minimalist interface with pages such as:

Dashboard

Settings

Downloads

Setup Guide

Settings should explain which values are configured through secrets/environment variables.

Do not display secret values.

# DEPLOYMENT

This is extremely important.

I do NOT know how to deploy applications.

Make deployment as easy as possible.

The final project must include:

Dockerfile

docker-compose.yml

.env.example

.gitignore

README.md

persistent storage configuration

FFmpeg

yt-dlp

SQLite persistence

automatic restart configuration

health check

If the environment supports deployment directly from Lovable, configure it appropriately.

If Lovable's own hosting cannot run this type of long-running Telegram + yt-dlp + FFmpeg worker reliably, DO NOT fake it.

Instead:

Build the full project and provide the easiest possible deployment option for a beginner.

Ideally support deployment using Docker on a small VPS.

The deployment instructions should assume Ubuntu.

# DOCKER

I want to ultimately be able to run:

docker compose up -d

and have the entire bot start.

Docker Compose should include:

restart: unless-stopped

persistent volumes for:

database
downloads/temp if needed
cookies if configured

The application should automatically start when the server restarts.

# ENVIRONMENT VARIABLES

Create `.env.example` containing at least:

BOT_TOKEN=
ALLOWED_CHANNEL_ID=
DELETE_ORIGINAL=true
MAX_CONCURRENT_DOWNLOADS=2
DOWNLOAD_RETRIES=2
COOKIES_FILE=
ADMIN_USERNAME=
ADMIN_PASSWORD=
PORT=8080

Add any other variables that are genuinely necessary.

Explain every variable in README.

# ADMIN SECURITY

Protect the admin dashboard with authentication.

A simple username/password for this private personal project is enough.

Do not expose the dashboard publicly without authentication.

Store ADMIN_USERNAME and ADMIN_PASSWORD as environment variables.

# PROJECT STRUCTURE

Use a clean maintainable architecture, for example:

app/
main.py
bot/
handlers.py
telegram.py
downloader/
downloader.py
yt_dlp_service.py
database/
models.py
repository.py
web/
routes.py
templates/
services/
utils/
downloads/
data/
Dockerfile
docker-compose.yml
requirements.txt
.env.example
README.md

You can modify the structure if there is a better approach.

# CODE QUALITY

Use:

Python 3.12+

asyncio

aiogram 3.x

yt-dlp

FastAPI for the small dashboard/API if useful

SQLite

SQLAlchemy or a lightweight equivalent if useful

FFmpeg

Docker

Make the code easy to maintain.

Use type hints.

Use structured error handling.

Avoid unnecessary complexity.

# TELEGRAM LOOP PROTECTION

Very important:

The bot uploads videos into the same channel it listens to.

Make absolutely sure that the bot does NOT try to process its own uploaded video messages again.

Only messages containing supported HTTP/HTTPS URLs should trigger downloads.

Avoid infinite loops.

# URL NORMALIZATION

Normalize common tracking parameters when practical so duplicate detection works.

For example remove unnecessary tracking parameters such as:

utm_source
utm_medium
utm_campaign
fbclid

But do not modify URLs in a way that breaks media extraction.

# VIDEO CAPTION

When uploading, create a simple caption where metadata is available.

Example:

Title of video

Source: Instagram

Do NOT include huge descriptions.

Do not expose the original URL unless configured.

Add environment option:

INCLUDE_SOURCE_URL=false

# ORIGINAL POST DELETION

Make:

DELETE_ORIGINAL=true

configurable.

If true:

Delete original Telegram URL post ONLY after media was uploaded successfully.

If false:

Keep the original post.

# ERROR HANDLING

Handle at least:

Unsupported URL
No video found
Private content
Login required
Instagram rate limit
TikTok restriction
YouTube extraction error
Network timeout
FFmpeg failure
Telegram upload failure
File too large
Disk full
Invalid channel
Bot permission error

Show user-friendly errors.

Technical details should go into logs.

# BOT PERMISSIONS

Create a Setup Guide page explaining EXACTLY which Telegram channel administrator permissions I need to give the bot.

I already created the bot with BotFather.

Explain visually/textually:

Telegram
→ My Channel
→ Channel Settings
→ Administrators
→ Add Administrator
→ select my bot

Required permissions:

Post Messages
Delete Messages

If additional Telegram permissions are actually required, explain them.

# README FOR A NON-DEVELOPER

This is extremely important.

Create a README called:

"SETUP — START HERE"

Assume I only know how to:

* use Telegram
* copy and paste text
* log into a website

Do not assume I know Linux.

Explain everything step-by-step.

For every terminal command, give me the exact command to copy/paste.

The guide should cover:

STEP 1
I already created the BotFather bot.

STEP 2
Add bot to Telegram channel.

STEP 3
Give bot required admin permissions.

STEP 4
Deploy application.

STEP 5
Paste BOT_TOKEN.

STEP 6
Find/configure ALLOWED_CHANNEL_ID.

STEP 7
Restart/start bot.

STEP 8
Test using an Instagram Reel.

STEP 9
Confirm that the video appears in Telegram.

STEP 10
Troubleshooting.

# IMPORTANT DEPLOYMENT DECISION

Before finalizing the project, evaluate whether the current Lovable environment can reliably run:

* a persistent Telegram bot process
* yt-dlp
* FFmpeg
* temporary video downloads
* SQLite persistent storage

If YES, configure it directly.

If NO, still build the entire application but make Docker/VPS deployment the primary method.

Do not replace the actual media downloader with a fake frontend demo.

The Telegram bot/downloader is the core product.

# TESTING

Add basic automated tests for:

URL extraction
URL normalization
duplicate checking
allowed channel validation
unsupported URL handling

Also ensure the application can start even if no media has been downloaded yet.

# FINAL RESULT

When you finish building, do NOT simply tell me:

"Here is the code."

I want you to give me a short, beginner-friendly final checklist telling me exactly what I personally need to do next.

Something like:

1. Open Telegram.
2. Open your channel.
3. Add @YOURBOT as administrator.
4. Enable Post Messages and Delete Messages.
5. Go to [deployment location].
6. Open Secrets.
7. Paste BOT_TOKEN.
8. Start application.
9. Send one test Instagram Reel link to the channel.

Whenever you need a technical decision, choose the simplest reliable solution for a non-developer.

Do not ask me to choose between technical frameworks unless absolutely necessary.

Build the solution end-to-end.

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://archive-bot-buddy.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/8e2198cf-d7dd-40e7-a81f-55091742cbe7).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
