import json
import os
import shutil
import subprocess

CHANNEL_ID = "MuseIndonesia"
CHANNEL_URL = "https://www.youtube.com/@MuseIndonesia"


def _cookie_args() -> list[str]:
    path = os.environ.get("MUSE_COOKIES", "")
    if path and os.path.isfile(path):
        return ["--cookies", path]
    return []


def _run(args: list[str], timeout: int = 45) -> str:
    if not shutil.which("yt-dlp"):
        return ""
    try:
        result = subprocess.run(
            ["yt-dlp", "--no-warnings", "--ignore-errors", *_cookie_args(), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def search_anime(query: str, limit: int = 12) -> list[dict]:
    search_query = f"ytsearch{max(limit * 3, 20)}:Muse Indonesia {query} anime episode"
    raw = _run(["--flat-playlist", "--dump-single-json", search_query])
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    results = []
    for entry in data.get("entries", []):
        if not entry:
            continue
        title = entry.get("title", "").strip()
        video_id = entry.get("id", "")
        uploader = (entry.get("uploader_id") or entry.get("channel_id") or "").lower()
        if not title or not video_id:
            continue
        if uploader and "muse" not in uploader:
            continue
        results.append({
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "status": "YouTube",
            "rating": "Muse Indonesia",
            "genres": [],
            "image": entry.get("thumbnail", ""),
            "source": "muse_indonesia",
        })
        if len(results) >= limit:
            break
    return results


def get_episode_list(video_url: str) -> list[dict]:
    return [{"episode_num": 1, "title": "Video Muse Indonesia", "url": video_url}]


def get_video_urls(episode_url: str) -> list[dict]:
    raw = _run([
        "-f", "136+140/135+140/134+140/133+140",
        "--get-url",
        episode_url,
    ], timeout=90)
    urls = [line.strip() for line in raw.splitlines() if line.strip().startswith("http")]
    if len(urls) < 2:
        return []
    return [{
        "quality": "720p",
        "url": urls[0],
        "audio_url": urls[1],
        "source": "direct_stream",
        "mirror_name": "Muse Indonesia YouTube",
    }]


def resolve_stream_url(embed_url: str) -> str:
    return embed_url


def search_channel() -> str:
    return CHANNEL_URL


def get_source_name() -> str:
    return "Muse Indonesia"
