from app.urls import extract_urls, is_valid_url, normalize_url, safe_filename, source_name


def test_extract_single_url():
    assert extract_urls("look https://www.instagram.com/reel/ABC123/") == [
        "https://www.instagram.com/reel/ABC123/"
    ]


def test_extract_multiple_urls():
    text = (
        "https://www.instagram.com/reel/A/\n"
        "https://www.tiktok.com/@x/video/123\n"
        "https://youtu.be/dQw4w9WgXcQ"
    )
    assert len(extract_urls(text)) == 3


def test_extract_ignores_non_urls_and_empty():
    assert extract_urls("just a note") == []
    assert extract_urls(None) == []


def test_extract_deduplicates():
    url = "https://vimeo.com/12345"
    assert extract_urls(f"{url} {url}") == [url]


def test_extract_strips_trailing_punctuation():
    assert extract_urls("see https://x.com/a/status/1.") == ["https://x.com/a/status/1"]


def test_unsupported_and_unsafe_urls_rejected():
    assert not is_valid_url("ftp://example.com/a.mp4")
    assert not is_valid_url("file:///etc/passwd")
    assert not is_valid_url("http://localhost:8080/admin")
    assert not is_valid_url("http://192.168.1.10/video")
    assert is_valid_url("https://example.com/v")


def test_normalize_removes_tracking_params():
    got = normalize_url(
        "https://www.instagram.com/reel/ABC/?utm_source=ig&igshid=99&fbclid=zz"
    )
    assert got == "https://instagram.com/reel/ABC"


def test_normalize_keeps_video_id():
    got = normalize_url("https://www.youtube.com/watch?v=abc123&utm_campaign=x")
    assert got == "https://youtube.com/watch?v=abc123"


def test_normalize_is_stable_for_duplicates():
    a = normalize_url("https://www.tiktok.com/@user/video/999/?_t=1&_r=1")
    b = normalize_url("https://tiktok.com/@user/video/999")
    assert a == b


def test_source_names():
    assert source_name("https://www.instagram.com/reel/A/") == "Instagram"
    assert source_name("https://youtu.be/A") == "YouTube"
    assert source_name("https://x.com/a/status/1") == "X"


def test_safe_filename():
    assert safe_filename("../../etc/passwd") == "etcpasswd"
    assert safe_filename("My Cool Video!!") == "My_Cool_Video"
    assert safe_filename("") == "video"
