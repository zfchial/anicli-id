"""
Scraper module untuk Samehadaku (https://samehadaku.li/)
Menangani: search anime, daftar episode, dan ekstrak URL video streaming

Catatan: Samehadaku menggunakan Cloudflare + JS protection.
- Search & episode list bisa dari HTML langsung
- Video player di-load via JS — gunakan mpv+yt-dlp untuk streaming
"""

import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://samehadaku.li"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": BASE_URL,
}


def _fetch(url: str, timeout: int = 15) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"[ERROR] Gagal mengakses {url}: {e}")
        return None


def search_anime(query: str, limit: int = 12) -> list[dict]:
    """
    Cari anime di Samehadaku.
    URL pattern: /anime/slug/
    Returns list of dict: {title, url, status, genres, rating, source}
    """
    url = f"{BASE_URL}/?s={query}"
    soup = _fetch(url)
    if not soup:
        return []

    results = []
    seen_urls = set()

    for article in soup.find_all("article"):
        a_tag = article.select_one('a[itemprop="url"]')
        if not a_tag:
            continue

        href = a_tag.get("href", "")
        title = a_tag.get("title", "") or a_tag.get_text(strip=True)

        if not title or not href:
            continue
        if "/anime/" not in href.lower():
            continue
        if href in seen_urls:
            continue

        seen_urls.add(href)

        status_el = article.select_one(".status")
        status = status_el.get_text(strip=True) if status_el else ""

        type_el = article.select_one(".typez")
        anime_type = type_el.get_text(strip=True) if type_el else ""

        rating = ""

        results.append({
            "title": title,
            "url": href,
            "genres": "",
            "status": status,
            "rating": rating,
            "image": "",
            "source": "samehadaku",
        })

        if len(results) >= limit:
            break

    return results


def get_episode_list(anime_url: str) -> list[dict]:
    """
    Ambil daftar episode dari halaman detail anime Samehadaku.
    Episode links: /slug-episode-N-subtitle-indo
    Returns list of dict: {episode_num, url, title}
    """
    soup = _fetch(anime_url)
    if not soup:
        return []

    episodes = []
    seen_eps = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        title = a_tag.get_text(strip=True)

        if not href or not title:
            continue
        if "episode" not in href.lower() and "episode" not in title.lower():
            continue
        if href == "#" or "javascript" in href:
            continue

        ep_match = re.search(r'(?:episode|ep)\s*(\d+)', title, re.IGNORECASE)
        if not ep_match:
            ep_match = re.search(r'(?:episode|ep)\s*(\d+)', href, re.IGNORECASE)
        ep_num = int(ep_match.group(1)) if ep_match else 0

        if ep_num <= 0 or ep_num in seen_eps:
            continue

        seen_eps.add(ep_num)

        if not href.startswith("http"):
            href = BASE_URL + href if href.startswith("/") else f"{BASE_URL}/{href}"

        episodes.append({
            "episode_num": ep_num,
            "url": href,
            "title": title,
        })

    episodes.sort(key=lambda x: x["episode_num"])
    return episodes


def get_video_urls(episode_url: str) -> list[dict]:
    """
    Ambil URL video dari halaman episode Samehadaku.
    
    Karena Samehadaku menggunakan JS-heavy protection, video URL tidak
    langsung tersedia di HTML. Strategi:
    1. Cari download link di HTML (jika ada)
    2. Cari URL di JavaScript
    3. Fallback: return URL episode — mpv+yt-dlp handle JS protection
    
    Returns list of dict: {quality, url, source, mirror_name}
    """
    soup = _fetch(episode_url)
    if not soup:
        return []

    videos = []
    seen_urls = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        text = a_tag.get_text(strip=True)

        if not href or href in seen_urls:
            continue

        if any(domain in href.lower() for domain in [
            "desustream", "kwik", "mega", "gofile", "acefile",
            "odfiles", "pdrain", "mediafire", "zippyshare",
            "drive.google", "kfiles", ".mp4", ".m3u8", ".mkv",
        ]):
            quality = "Unknown"
            lower_all = (text + " " + href).lower()

            if "1080" in lower_all:
                quality = "1080p"
            elif "720" in lower_all:
                quality = "720p"
            elif "480" in lower_all:
                quality = "480p"
            elif "360" in lower_all:
                quality = "360p"

            videos.append({
                "quality": quality,
                "url": href,
                "source": "download_link",
                "mirror_name": text or "Mirror",
            })
            seen_urls.add(href)

    for script in soup.find_all("script"):
        if script.string:
            for pattern in [
                r'https?://[^\s"\'<>]+\.mp4(?:\?[^\s"\'<>]*)?',
                r'https?://[^\s"\'<>]+\.m3u8(?:\?[^\s"\'<>]*)?',
                r'(?:file|src|url|source)\s*[:=]\s*["\'](https?://[^"\']+)["\']',
                r'"url"\s*:\s*["\'](https?://[^"\']+)["\']',
            ]:
                matches = re.findall(pattern, script.string, re.IGNORECASE)
                for match in matches:
                    if match not in seen_urls and match.startswith("http"):
                        skip = False
                        for noise in ["wp-content", "wp-admin", "admin-ajax", "push-sdk", "sdk.js", "jquery", "facebook", "twitter", "instagram"]:
                            if noise in match.lower():
                                skip = True
                                break
                        if not skip:
                            videos.append({
                                "quality": "JS_DETECTED",
                                "url": match,
                                "source": "javascript",
                                "mirror_name": "Detected",
                            })
                            seen_urls.add(match)

    for sel in ["div.player-embed", "div#pembed", "div.video-embed"]:
        container = soup.select_one(sel)
        if container:
            iframe = container.select_one("iframe")
            if iframe:
                src = iframe.get("src", "")
                if src and src not in seen_urls and src != "about:blank":
                    videos.append({
                        "quality": "STREAM",
                        "url": src,
                        "source": "embed_iframe",
                        "mirror_name": "Samehadaku Player",
                    })
                    seen_urls.add(src)

    if not videos:
        videos.append({
            "quality": "PAGE (yt-dlp)",
            "url": episode_url,
            "source": "page_fallback",
            "mirror_name": "Episode Page (yt-dlp)",
        })

    return videos


def resolve_stream_url(embed_url: str) -> str | None:
    """
    Resolve stream URL untuk Samehadaku.
    Jika embed_url adalah URL episode (fallback), return as-is (yt-dlp handle).
    """
    if not embed_url:
        return None
    
    if "samehadaku" in embed_url.lower() and "episode" in embed_url.lower():
        return embed_url
    
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        resp = session.get(embed_url, timeout=15, allow_redirects=True)
        
        if any(ext in resp.url.lower() for ext in [".mp4", ".m3u8"]):
            return resp.url
        
        return embed_url
    except Exception:
        return embed_url
