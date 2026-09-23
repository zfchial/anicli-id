"""
Scraper module untuk Anoboy (https://anoboy.be/)
Menangani: search anime, daftar episode, dan ekstrak URL video streaming

Struktur HTML Anoboy (berdasarkan observasi):
- Homepage: div.latest > div.item (atau similar)
- Search: /?s=query → hasil di div dengan class tertentu
- Anime detail: /anime/slug/ 
  - Biasanya ada daftar episode
- Episode page: embed video (biasanya langsung atau via iframe)
"""

import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://anoboy.be"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": BASE_URL,
}

VALID_VIDEO_DOMAINS = [
    "anoboy", "desustream", "kwik", "mega", "mediafire", "gofile",
    "acefile", "odfiles", "pdrain", "zippyshare", "drive.google",
    "cloud", "stream", "dstream", "embed", "player",
]

NOISE_PATTERNS = [
    "facebook.com", "twitter.com", "instagram.com", "/wp-content/",
    "/category/", "/genre/", "#", "javascript:",
]


def _fetch(url: str, timeout: int = 15) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"[ERROR] Gagal mengakses {url}: {e}")
        return None


def _is_valid_video_url(url: str) -> bool:
    url_lower = url.lower()
    
    for pattern in NOISE_PATTERNS:
        if pattern in url_lower:
            return False
    
    for domain in VALID_VIDEO_DOMAINS:
        if domain in url_lower:
            return True
    
    if any(p in url_lower for p in ["stream", ".mp4", ".m3u8", ".mkv", "embed"]):
        return True
    
    return False


def search_anime(query: str, limit: int = 12) -> list[dict]:
    """
    Cari anime di Anoboy.
    Returns list of dict: {title, url, status, episode_info, source}
    """
    url = f"{BASE_URL}/?s={query}"
    soup = _fetch(url)
    if not soup:
        return []

    results = []

    
    seen_urls = set()
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        title = a_tag.get_text(strip=True)
        
        if len(title) < 3:
            continue
        if href in seen_urls:
            continue
            
        if any(skip in href.lower() for skip in ["/category/", "/genre/", "/page/", "javascript:", "#"]):
            continue
        
        if query.lower() in title.lower() or any(
            ep in title.lower() for ep in ["episode", "sub", "subtitle", "season"]
        ) or (
            "/anime/" in href.lower() and len(title) > 5
        ):
            parent = a_tag.parent
            status = ""
            ep_info = ""
            
            if parent:
                parent_text = parent.get_text(strip=True)
                if "completed" in parent_text.lower():
                    status = "Completed"
                elif "ongoing" in parent_text.lower() or "tv" in parent_text.lower():
                    status = "Ongoing"
                
                ep_match = re.search(r'(?:ep|episode)\s*(\d+)', parent_text, re.IGNORECASE)
                if ep_match:
                    ep_info = f"Ep {ep_match.group(1)}"
            
            if href not in seen_urls and len(results) < limit:
                seen_urls.add(href)
                results.append({
                    "title": title,
                    "url": href,
                    "genres": "",  # Anoboy search biasanya tidak show genres di result
                    "status": status,
                    "rating": "",
                    "image": "",
                    "episode_info": ep_info,
                    "source": "anoboy",
                })

    return results


def get_episode_list(anime_url: str) -> list[dict]:
    """
    Ambil daftar episode dari halaman detail anime Anoboy.
    Returns list of dict: {episode_num, url, title}
    """
    soup = _fetch(anime_url)
    if not soup:
        return []

    episodes = []
    seen_eps = set()

    
    episode_selectors = [
        "div.episode-list li a",
        "div.eps li a", 
        "ul.episodes li a",
        "div#episode a",
        "table tr td a",
        "a[href*='episode']",
        "a[href*='ep-']",
    ]
    
    for selector in episode_selectors:
        for a_tag in soup.select(selector):
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)
            
            if not href or not title:
                continue
                
            ep_match = re.search(r'(?:ep|episode)\s*(\d+)', title, re.IGNORECASE)
            ep_num = int(ep_match.group(1)) if ep_match else 0
            
            if ep_num not in seen_eps and ep_num > 0:
                seen_eps.add(ep_num)
                
                if not href.startswith("http"):
                    href = BASE_URL + href if href.startswith("/") else f"{anime_url}/{href}"
                
                episodes.append({
                    "episode_num": ep_num,
                    "url": href,
                    "title": title,
                })

    if not episodes:
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)
            
            if re.search(r'(?:ep|episode)\s*\d+', title, re.IGNORECASE):
                ep_match = re.search(r'(?:ep|episode)\s*(\d+)', title, re.IGNORECASE)
                ep_num = int(ep_match.group(1)) if ep_match else 0
                
                if ep_num not in seen_eps and ep_num > 0:
                    seen_eps.add(ep_num)
                    
                    if not href.startswith("http"):
                        href = BASE_URL + href if href.startswith("/") else f"{anime_url}/{href}"
                    
                    episodes.append({
                        "episode_num": ep_num,
                        "url": href,
                        "title": title,
                    })

    episodes.sort(key=lambda x: x["episode_num"])
    return episodes


def get_video_urls(episode_url: str) -> list[dict]:
    """
    Ambil URL video streaming dari halaman episode Anoboy.
    Returns list of dict: {quality, url, source, mirror_name}
    
    Anoboy biasanya:
    - Embed video langsung di halaman (iframe/video tag)
    - Atau redirect ke player eksternal
    """
    soup = _fetch(episode_url)
    if not soup:
        return []

    videos = []
    seen_urls = set()

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if src and src not in seen_urls and _is_valid_video_url(src):
            videos.append({
                "quality": "STREAM",
                "url": src,
                "source": "embed_iframe",
                "mirror_name": "Anoboy Player",
            })
            seen_urls.add(src)

    for video_tag in soup.find_all("video"):
        src = video_tag.get("src", "")
        if src and _is_valid_video_url(src):
            videos.append({
                "quality": "DIRECT",
                "url": src,
                "source": "html5_video",
                "mirror_name": "Direct Stream",
            })
            seen_urls.add(src)
        
        for source in video_tag.find_all("source"):
            src = source.get("src", "")
            if src and _is_valid_video_url(src):
                quality = source.get("label", "Unknown") or source.get("data-quality", "Unknown")
                videos.append({
                    "quality": quality,
                    "url": src,
                    "source": "html5_source",
                    "mirror_name": "Direct Stream",
                })
                seen_urls.add(src)

    for sel in ["div.download", "div.mirror", "div.sources", "div.quality"]:
        section = soup.select_one(sel)
        if section:
            for a_tag in section.find_all("a", href=True):
                href = a_tag.get("href", "")
                mirror_name = a_tag.get_text(strip=True)
                
                if href and href not in seen_urls and _is_valid_video_url(href):
                    parent_text = a_tag.parent.get_text(strip=True) if a_tag.parent else ""
                    quality = "Unknown"
                    
                    q_match = re.search(r'(\d{3,4})\s*[Pp]', parent_text)
                    if q_match:
                        quality = f"{q_match.group(1)}p"
                    elif "360" in parent_text:
                        quality = "360p"
                    elif "480" in parent_text:
                        quality = "480p"
                    elif "720" in parent_text:
                        quality = "720p"
                    elif "1080" in parent_text:
                        quality = "1080p"
                    
                    videos.append({
                        "quality": quality,
                        "url": href,
                        "source": "download_mirror",
                        "mirror_name": mirror_name or "Mirror",
                    })
                    seen_urls.add(href)

    for script in soup.find_all("script"):
        if script.string:
            for pattern in [
                r'https?://[^\s"\']+\.mp4(?:\?[^\s"\']*)?',
                r'https?://[^\s"\']+\.m3u8(?:\?[^\s"\']*)?',
                r'(?:file|src|url|source)\s*[:=]\s*["\'](https?://[^"\']+)["\']',
            ]:
                matches = re.findall(pattern, script.string, re.IGNORECASE)
                for match in matches:
                    if match not in seen_urls and _is_valid_video_url(match):
                        videos.append({
                            "quality": "JS_DETECTED",
                            "url": match,
                            "source": "javascript",
                            "mirror_name": "Detected URL",
                        })
                        seen_urls.add(match)

    if not videos:
        videos.append({
            "quality": "PAGE_URL",
            "url": episode_url,
            "source": "page_redirect",
            "mirror_name": "Open in Browser",
        })

    return videos


def resolve_stream_url(embed_url: str) -> str | None:
    """
    Resolve Anoboy embed URL ke direct stream.
    Anoboy kadang menggunakan redirect chain.
    """
    if not embed_url:
        return None
        
    if "anoboy" in embed_url.lower():
        return _resolve_anoboy_url(embed_url)
    
    return _resolve_generic_url(embed_url)


def _resolve_anoboy_url(url: str) -> str | None:
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        resp = session.get(url, timeout=20, allow_redirects=True)
        final_url = resp.url
        
        if any(ext in final_url.lower() for ext in [".mp4", ".m3u8", ".mkv"]):
            return final_url
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for script in soup.find_all("script"):
            if script.string:
                patterns = [
                    r'(?:file|source|url|src)\s*[:=]\s*["\'](https?://[^"\']+\.(?:mp4|m3u8)[^"\']*)["\']',
                    r'https?://[^\s"\']+\.(?:mp4|m3u8)(?:\?[^\s"\']*)?',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    if matches:
                        return matches[0]
        
        return final_url

    except Exception as e:
        print(f"[WARNING] Gagal resolve Anoboy URL: {e}")
        return url


def _resolve_generic_url(url: str) -> str | None:
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        resp = session.get(url, timeout=20, allow_redirects=True)
        
        if any(ext in resp.url.lower() for ext in [".mp4", ".m3u8", ".mkv"]):
            return resp.url
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for script in soup.find_all("script"):
            if script.string:
                for pattern in [
                    r'https?://[^\s"\']+\.(?:mp4|m3u8)(?:\?[^\s"\']*)?',
                    r'"(https?://[^"]*(?:\.mp4|\.m3u8)[^"]*)"',
                ]:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    if matches:
                        return matches[0]
        
        return url
    except Exception as e:
        print(f"[WARNING] Gagal resolve URL: {e}")
        return url


def get_latest_anime(limit: int = 20) -> list[dict]:
    """
    Ambil daftar anime terbaru dari homepage Anoboy.
    Returns list of dict: {title, url, latest_ep, status}
    """
    soup = _fetch(BASE_URL)
    if not soup:
        return []

    results = []
    seen_titles = set()

    containers = [
        "div.latest", "div.recent", "div.newest", "div.update",
        "div.content", "main", "div.home",
    ]

    for container_sel in containers:
        container = soup.select_one(container_sel)
        if not container:
            continue
        
        for item in container.find_all(["div", "li", "article"], class_=True):
            a_tag = item.select_one("a")
            if not a_tag:
                continue
            
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)
            
            if not title or title in seen_titles:
                continue
            if len(title) < 5:
                continue
            
            item_text = item.get_text(strip=True)
            ep_match = re.search(r'(?:ep|episode)\s*(\d+)', item_text, re.IGNORECASE)
            latest_ep = f"Ep {ep_match.group(1)}" if ep_match else ""
            
            status = "Ongoing"
            if "completed" in item_text.lower():
                status = "Completed"
            
            seen_titles.add(title)
            results.append({
                "title": title,
                "url": href,
                "latest_ep": latest_ep,
                "status": status,
                "source": "anoboy",
            })
            
            if len(results) >= limit:
                break
        
        if len(results) >= limit:
            break

    return results
