"""URL extraction, validation and normalisation helpers."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

URL_RE = re.compile(r"https?://[^\s<>\"'()]+", re.IGNORECASE)

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "igshid",
    "igsh",
    "mibextid",
    "share_id",
    "_r",
    "_t",
    "si",
    "feature",
    "ref",
    "ref_src",
    "ref_url",
    "s",
}

# Params that must never be stripped, they identify the media itself.
KEEP_PARAMS = {"v", "list", "id", "story_fbid", "story_id", "video_id", "t"}

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}

SOURCE_NAMES = {
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "twitter.com": "X",
    "x.com": "X",
    "facebook.com": "Facebook",
    "fb.watch": "Facebook",
    "vimeo.com": "Vimeo",
    "reddit.com": "Reddit",
    "twitch.tv": "Twitch",
    "dailymotion.com": "Dailymotion",
}


def extract_urls(text: str | None) -> list[str]:
    """Return every unique http(s) URL found in a text, in order."""
    if not text:
        return []
    found: list[str] = []
    for raw in URL_RE.findall(text):
        cleaned = raw.rstrip(".,;:!?)]}\u201d\u2019")
        if is_valid_url(cleaned) and cleaned not in found:
            found.append(cleaned)
    return found


def is_valid_url(url: str) -> bool:
    """Only public http/https URLs with a real hostname are accepted."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    if not host or "." not in host:
        return False
    if host in BLOCKED_HOSTS or host.endswith(".local"):
        return False
    if host.startswith("10.") or host.startswith("192.168.") or host.startswith("169.254."):
        return False
    if re.match(r"^172\.(1[6-9]|2\d|3[01])\.", host):
        return False
    return True


def normalize_url(url: str) -> str:
    """Strip tracking noise so the same video is recognised as a duplicate."""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("m.") and len(host) > 2:
        host = host[2:]

    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if k in KEEP_PARAMS or k.lower() not in TRACKING_PARAMS
    ]
    path = parsed.path.rstrip("/") or "/"

    netloc = host
    if parsed.port and parsed.port not in (80, 443):
        netloc = f"{host}:{parsed.port}"

    return urlunparse((parsed.scheme.lower(), netloc, path, "", urlencode(query), ""))


def source_name(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    for domain, name in SOURCE_NAMES.items():
        if host == domain or host.endswith("." + domain):
            return name
    return host or "Unknown"


def safe_filename(name: str, fallback: str = "video") -> str:
    """Reduce any title to a safe, short, path-free filename stem."""
    name = re.sub(r"[^\w\s.-]", "", name or "", flags=re.UNICODE).strip()
    name = re.sub(r"\s+", "_", name).strip("._-")
    return (name or fallback)[:80]
