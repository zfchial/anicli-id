"""
Scraper module untuk Otakudesu
Menangani: search anime, daftar episode, dan ekstrak URL video streaming

Struktur HTML Otakudesu (terbaru):
- Search results: ul.chivsrc > li
  - img (thumbnail)  
  - h2 > a (judul + URL anime) — Hanya /anime/, skip /episode/
  - div.set (Genres, Status, Rating)

- Anime detail page:
  - div.episodelist > ul > li > a (daftar episode)

- Episode page:
  - div#pembed (class: player-embed) > iframe (video embed/stream)
  - div.download > ul > li 
    - <strong> = kualitas (Mp4 360p, Mp4 480p, dll.)
    - <a> = mirror link (ODFiles, Mega, dll.)
    - <i> = file size
"""

import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://otakudesu.blog"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Domain yang dianggap sebagai mirror/download yang valid
VALID_MIRROR_DOMAINS = [
    "desustream.com", "kwik.cx", "kwik.si",
    "mega.nz", "megadrive", "mediafire.com", "gofile.io",
    "acefile.co", "odfiles", "pdrain", "kfiles",
    "zippyshare", "drive.google.com", "cloud",
]

# Domain/pattern yang harus DIHAPUS (noise)
NOISE_PATTERNS = [
    "facebook.com", "twitter.com", "otakudesu.blog/genre",
    "otakudesu.blog/episode", "sharer.php", "/wp-content/",
]


def _is_valid_video_url(url: str) -> bool:
    """Cek apakah URL adalah link video/mirror yang valid."""
    url_lower = url.lower()
    
    # Skip noise patterns
    for pattern in NOISE_PATTERNS:
        if pattern in url_lower:
            return False
    
    # Cek apakah mengandung domain mirror yang valid
    for domain in VALID_MIRROR_DOMAINS:
        if domain in url_lower:
            return True
    
    # Jika tidak match domain manapun, cek pola umum streaming
    if any(p in url_lower for p in ["stream", "dstream", "player", "embed"]):
        return True
    
    return False


def search_anime(query: str, limit: int = 12) -> list[dict]:
    """
    Cari anime berdasarkan query.
    Returns list of dict: {title, url, genres, status, rating, image}
    
    Hanya mengembalikan hasil anime (URL /anime/), bukan episode (/episode/).
    """
    url = f"{BASE_URL}/?s={query}&s_type=all"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Gagal mengakses {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for item in soup.select("ul.chivsrc > li"):
        if len(results) >= limit:
            break
            
        try:
            h2_tag = item.select_one("h2 a")
            if not h2_tag:
                continue

            href = h2_tag.get("href", "")
            title = h2_tag.get_text(strip=True)

            # SKIP episode links — hanya ambil anime detail pages
            if "/episode/" in href.lower():
                continue

            # Parse metadata dari div.set
            set_divs = item.select("div.set")
            genres = ""
            status = ""
            rating = ""
            
            for div in set_divs:
                text = div.get_text(strip=True)
                bold_tag = div.select_one("b")
                label = bold_tag.get_text(strip=True) if bold_tag else ""
                
                if "Genre" in label:
                    genre_links = [a.get_text(strip=True) for a in div.select("a")]
                    genres = ", ".join(genre_links)
                elif "Status" in label:
                    status = text.replace(label, "").replace(":", "").strip()
                elif "Rating" in label:
                    rating = text.replace(label, "").replace(":", "").strip()

            # Thumbnail image
            img_tag = item.select_one("img")
            image = img_tag.get("src", "") if img_tag else ""

            results.append({
                "title": title,
                "url": href,
                "genres": genres,
                "status": status,
                "rating": rating,
                "image": image,
            })
        except Exception as e:
            continue

    return results


def get_episode_list(anime_url: str) -> list[dict]:
    """
    Ambil daftar episode dari halaman detail anime.
    Returns list of dict: {episode_num, url, title}
    """
    try:
        resp = requests.get(anime_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Gagal mengakses {anime_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    episodes = []

    for li in soup.select("div.episodelist ul li"):
        a_tag = li.select_one("a")
        if not a_tag:
            continue

        href = a_tag.get("href", "")
        title = a_tag.get_text(strip=True)

        ep_match = re.search(r"Episode\s*(\d+)", title, re.IGNORECASE)
        ep_num = int(ep_match.group(1)) if ep_match else 0

        episodes.append({
            "episode_num": ep_num,
            "url": href,
            "title": title,
        })

    episodes.sort(key=lambda x: x["episode_num"])
    return episodes


AJAX_URL = f"{BASE_URL}/wp-admin/admin-ajax.php"


def _fetch_nonce_and_actions(soup):
    """Extract nonce action dan mirror action dari JS di halaman episode."""
    nonce_action = None
    mirror_action = None
    for script in soup.find_all("script"):
        txt = script.string or ""
        if "nonce" in txt and "ajax" in txt:
            actions = re.findall(r'action:"([a-f0-9]+)"', txt)
            if len(actions) >= 2:
                mirror_action = actions[0]
                nonce_action = actions[1]
            elif len(actions) == 1:
                nonce_action = actions[0]
            break
    return nonce_action, mirror_action


def _get_nonce(session, nonce_action):
    """Fetch nonce via AJAX."""
    if not nonce_action:
        return None
    try:
        resp = session.post(AJAX_URL, data={"action": nonce_action}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", "")
    except Exception:
        pass
    return None


def _resolve_mirror_ajax(session, mirror_action, nonce, mirror_data):
    """Resolve mirror via AJAX → dapet iframe HTML (base64)."""
    if not mirror_action or not nonce:
        return None
    try:
        post_data = {**mirror_data, "nonce": nonce, "action": mirror_action}
        resp = session.post(AJAX_URL, data=post_data, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            html_b64 = result.get("data", "")
            if html_b64:
                import base64
                decoded = base64.b64decode(html_b64).decode()
                s = BeautifulSoup(decoded, "html.parser")
                iframe = s.select_one("iframe")
                if iframe:
                    return iframe.get("src", "")
    except Exception:
        pass
    return None


def _resolve_desustream(embed_url):
    """Resolve desustream embed → direct video URL (googlevideo/mp4)."""
    if not embed_url:
        return None
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        session.headers["Referer"] = BASE_URL + "/"
        resp = session.get(embed_url, timeout=15)
        if resp.status_code != 200:
            return embed_url
        soup = BeautifulSoup(resp.text, "html.parser")
        source = soup.select_one("video source[src]")
        if source:
            src = source.get("src", "")
            if src.startswith("http"):
                return src
        for tag in soup.find_all("video"):
            src = tag.get("src", "")
            if src.startswith("http"):
                return src
        for script in soup.find_all("script"):
            txt = script.string or ""
            urls = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|m3u8)(?:\?[^\s"\'<>]*)?', txt)
            if urls:
                return urls[0]
        return embed_url
    except Exception:
        return embed_url


def get_video_urls(episode_url: str) -> list[dict]:
    """
    Ambil URL video streaming dari halaman episode.
    Flow: load page → extract mirror data → fetch nonce → resolve mirrors via AJAX
    → resolve desustream embed → direct video URL.

    Returns list of dict: {quality, url, source, mirror_name}
    """
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        resp = session.get(episode_url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Gagal mengakses {episode_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    videos = []
    seen_urls = set()

    nonce_action, mirror_action = _fetch_nonce_and_actions(soup)
    nonce = _get_nonce(session, nonce_action)

    mirror_div = soup.select_one("div.mirrorstream")
    if mirror_div and nonce and mirror_action:
        quality_map = {
            "m360p": "360p",
            "m480p": "480p",
            "m720p": "720p",
            "m1080p": "1080p",
        }
        for ul in mirror_div.find_all("ul"):
            ul_classes = " ".join(ul.get("class", []))
            quality_label = "Unknown"
            for cls, qlabel in quality_map.items():
                if cls in ul_classes:
                    quality_label = qlabel
                    break

            for a_tag in ul.find_all("a", attrs={"data-content": True}):
                mirror_name = a_tag.get_text(strip=True)
                try:
                    import json as _json
                    import base64 as _b64
                    dc = a_tag["data-content"]
                    mirror_data = _json.loads(_b64.b64decode(dc))
                except Exception:
                    continue

                embed_url = _resolve_mirror_ajax(session, mirror_action, nonce, mirror_data)
                if not embed_url or embed_url in seen_urls:
                    continue

                direct_url = None
                if "desustream" in embed_url.lower():
                    direct_url = _resolve_desustream(embed_url)

                final_url = direct_url or embed_url
                if final_url in seen_urls:
                    continue
                seen_urls.add(final_url)

                is_direct = final_url and ("googlevideo" in final_url or final_url.endswith(".mp4") or ".mp4?" in final_url or ".m3u8" in final_url)
                vid_source = "direct_stream" if is_direct else "embed_stream"

                videos.append({
                    "quality": quality_label,
                    "url": final_url,
                    "source": vid_source,
                    "mirror_name": mirror_name,
                })

    if not videos:
        pembed = soup.select_one("div#pembed") or soup.select_one("div.player-embed")
        if pembed:
            iframe = pembed.select_one("iframe")
            if iframe:
                src = iframe.get("src", "")
                if src and src not in seen_urls:
                    direct = _resolve_desustream(src) if "desustream" in src.lower() else src
                    videos.append({
                        "quality": "STREAM",
                        "url": direct or src,
                        "source": "embed_stream",
                        "mirror_name": "DesuStream Player",
                    })

    return videos


def resolve_stream_url(embed_url: str) -> str | None:
    """Resolve embed/direct URL. Jika sudah direct (googlevideo/mp4), return as-is."""
    if not embed_url:
        return None
    if "googlevideo" in embed_url or ".mp4" in embed_url or ".m3u8" in embed_url:
        return embed_url
    if "desustream" in embed_url.lower():
        return _resolve_desustream(embed_url) or embed_url
    return embed_url


def get_anime_info(anime_url: str) -> dict:
    """
    Ambil info lengkap dari halaman detail anime.
    Returns: {title, synopsis, genres, status, rating, total_episodes, image}
    """
    try:
        resp = requests.get(anime_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Gagal mengakses {anime_url}: {e}")
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    info = {}
    
    # Judul
    for sel in ["h1", ".jdlz", ".title"]:
        tag = soup.select_one(sel)
        if tag:
            info["title"] = tag.get_text(strip=True)
            break
    
    # Info container
    for sel in [".infoz", ".info"]:
        info_div = soup.select_one(sel)
        if info_div:
            text = info_div.get_text(separator="\n", strip=True)
            for line in text.split("\n"):
                if ":" in line:
                    key, _, value = line.partition(":")
                    key_lower = key.strip().lower()
                    value = value.strip()
                    if "genre" in key_lower:
                        info["genres"] = value
                    elif "status" in key_lower:
                        info["status"] = value
                    elif "rating" in key_lower:
                        info["rating"] = value
                    elif "episode" in key_lower:
                        info["total_episodes"] = value
            break
    
    # Sinopsis
    for sel in [".sinopsis", ".desc", ".summary"]:
        sinop = soup.select_one(sel)
        if sinop:
            info["synopsis"] = sinop.get_text(strip=True)
            break
    
    # Image
    for sel in [".fotoanime img", "div.thumb img", ".image img"]:
        img = soup.select_one(sel)
        if img:
            info["image"] = img.get("src", "")
            break
    
    return info
