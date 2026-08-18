# SETUP — START HERE

This turns your private Telegram channel into a personal video archive.
You share a link (Instagram, TikTok, YouTube, X, Facebook, Reddit, Vimeo…) into your
channel, and the bot replaces it with the actual playable video.

You do **not** need to know Linux or programming. Just copy and paste.

---

## What you need

1. A Telegram bot token from BotFather (you already have this).
2. A private Telegram channel.
3. A small server ("VPS") running **Ubuntu 22.04 or 24.04**.
   Any cheap one works (Hetzner, DigitalOcean, Contabo — about 5 €/month).
   When you create it, the provider gives you an **IP address**, a **username**
   (usually `root`) and a **password**.

> **Why a server and not Lovable hosting?**
> This bot must run 24/7, install FFmpeg, run yt-dlp, and write video files to disk.
> Lovable's hosting runs short web requests, not long-running video downloads,
> so it cannot run this reliably. Docker on a small Ubuntu server is the simplest
> option that actually works. Everything is prepared for you below.

---

## STEP 1 — You already created the bot

In Telegram you talked to **@BotFather** and got a token that looks like:

```
123456789:AAG7v...longrandomtext...
```

Keep it handy. Never share it with anyone.

---

## STEP 2 — Add the bot to your Telegram channel

1. Open Telegram, open your private channel.
2. Tap the channel name at the top.
3. Tap **Edit** → **Administrators** → **Add Administrator**.
4. Search for your bot's username and select it.

---

## STEP 3 — Give the bot the right permissions

While adding it as administrator, turn ON:

- ✅ **Post Messages** (so it can upload the videos)
- ✅ **Delete Messages** (so it can remove your original link post)

Everything else can stay off. Tap the ✓ to save.

---

## STEP 4 — Deploy the application

### 4a. Connect to your server

On Windows use **PowerShell**, on Mac use **Terminal**. Type this
(replace `YOUR_SERVER_IP` with your server's IP address):

```bash
ssh root@YOUR_SERVER_IP
```

Type your password when asked (nothing appears while typing — that's normal).

### 4b. Install Docker (one command, copy the whole block)

```bash
apt update && apt install -y docker.io docker-compose-v2 git nano && systemctl enable --now docker
```

### 4c. Copy this project onto the server

If your project is on GitHub:

```bash
git clone YOUR_REPOSITORY_URL telegram-archive
cd telegram-archive/bot
```

If not, create the folder and copy the files with any SFTP tool
(for example **FileZilla** or **WinSCP**) into `/root/telegram-archive/bot`, then:

```bash
cd /root/telegram-archive/bot
```

---

## STEP 5 — Paste your BOT_TOKEN

Create your settings file:

```bash
cp .env.example .env
nano .env
```

A simple text editor opens. Fill in:

```
BOT_TOKEN=123456789:AAG7v...your real token...
ADMIN_USERNAME=admin
ADMIN_PASSWORD=pick-a-strong-password
```

Leave `ALLOWED_CHANNEL_ID=` empty for now.

Save and exit: press **Ctrl+O**, then **Enter**, then **Ctrl+X**.

Start the bot:

```bash
docker compose up -d
```

The first start takes a few minutes (it installs FFmpeg and yt-dlp).

---

## STEP 6 — Find and configure your Channel ID

1. In Telegram, post any message in your channel (for example "hello").
2. In your web browser open:

   ```
   http://YOUR_SERVER_IP:8080
   ```

3. Log in with the `ADMIN_USERNAME` / `ADMIN_PASSWORD` you chose.
4. The Dashboard shows your channel and its **Channel ID** (looks like `-1001234567890`)
   with a **Copy** button.
5. Back in the server terminal:

   ```bash
   nano .env
   ```

   Set:

   ```
   ALLOWED_CHANNEL_ID=-1001234567890
   ```

   Save with **Ctrl+O**, **Enter**, **Ctrl+X**.

Until this is set the bot is in **safe setup mode** and downloads nothing.

---

## STEP 7 — Restart the bot

```bash
docker compose up -d
```

The Dashboard should now show **Bot status: Online**, **Telegram connection: OK**
and your Channel ID.

The bot also starts automatically whenever the server reboots.

---

## STEP 8 — Test with an Instagram Reel

1. Open Instagram, find any public Reel.
2. Tap **Share** → **Telegram** → choose your channel.
3. Wait a few seconds.

---

## STEP 9 — Confirm

In your channel you should now see the **actual video**, playable inside Telegram,
with a caption like:

```
Title of the video
Source: Instagram
```

…and your original link post is gone. That's it — your archive is running.

---

## STEP 10 — Troubleshooting

| What you see | What to do |
| --- | --- |
| Nothing happens at all | Check the Dashboard: is **Bot status** Online? Is the Channel ID correct? |
| "⚠️ Could not download this video." | The message says why. Private content usually needs cookies (see below). |
| "…could not delete the original link" | Give the bot the **Delete Messages** permission in channel settings. |
| "The video is too large to upload" | Telegram bots can upload max **50 MB**. See "Bigger files" below. |
| Dashboard won't open | Your server firewall may block port 8080: `ufw allow 8080` |
| Want to see the logs | `docker compose logs -f` (press Ctrl+C to stop watching) |
| Update yt-dlp after a site changes | `docker compose build --no-cache && docker compose up -d` |
| Stop the bot | `docker compose down` |

### Private content (optional cookies)

Some Instagram/TikTok videos require being logged in. You can add cookies later:

1. Install a browser extension that exports cookies in **Netscape format**
   (for example "Get cookies.txt LOCALLY").
2. Log in to the site in your browser and export `cookies.txt`.
3. Upload it to the server into the `bot/cookies/` folder.
4. In `.env` set: `COOKIES_FILE=/cookies/cookies.txt`
5. Run `docker compose up -d`.

This is optional — public videos work without it.

### Bigger files than 50 MB

Telegram's normal Bot API caps bot uploads at 50 MB. The code is structured so a
**local Telegram Bot API server** (which raises the limit to 2 GB) can be added later:
run one, point the bot's API base URL at it, and raise `MAX_UPLOAD_MB`.

---

## All settings explained

| Variable | Meaning |
| --- | --- |
| `BOT_TOKEN` | Your BotFather token. Secret, never shown in the dashboard or logs. |
| `ALLOWED_CHANNEL_ID` | The only channel the bot reacts to. All other chats are ignored. |
| `DELETE_ORIGINAL` | `true` = delete your link post after the video uploads successfully. |
| `SKIP_DUPLICATES` | `true` = reply "Already saved ✅" instead of downloading the same link twice. |
| `INCLUDE_SOURCE_URL` | `true` = add the original link to the video caption. Default `false`. |
| `MAX_CONCURRENT_DOWNLOADS` | How many videos download at once (2 is recommended). |
| `DOWNLOAD_RETRIES` | Retries after a temporary network error. |
| `DOWNLOAD_TIMEOUT` | Seconds before giving up on one download. |
| `MAX_UPLOAD_MB` | Upload size limit (50 for the standard Telegram Bot API). |
| `COOKIES_FILE` | Optional path to `cookies.txt` for private content. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Login for the web dashboard. |
| `PORT` | Dashboard port (default 8080). |
| `LOG_LEVEL` | `INFO` normally, `DEBUG` for more detail. |

---

## How it works (short version)

```
Telegram channel post with a link
        ↓
URL detected, validated, normalised
        ↓  (only from ALLOWED_CHANNEL_ID)
Download queue (max 2 at a time, with retries)
        ↓
yt-dlp + FFmpeg → MP4
        ↓
Uploaded to the same channel as a streaming video
        ↓
Original link post deleted · temp files deleted · recorded in SQLite
```

Project layout:

```
bot/
  app/
    main.py          start everything
    config.py        environment variables
    bot.py           Telegram handlers + processing
    downloader.py    yt-dlp + FFmpeg
    queue.py         concurrency limit
    database.py      SQLite storage
    urls.py          URL detection / validation / normalisation
    web.py           dashboard
    templates/       dashboard pages
  tests/             automated tests
  Dockerfile
  docker-compose.yml
  .env.example
```

Run the tests any time with:

```bash
docker compose run --rm bot python -m pytest -q
```
