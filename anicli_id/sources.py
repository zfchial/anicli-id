"""
Sources abstraction layer — unified API untuk semua source anime.
CLI cukup panggil satu fungsi, semua source akan dipanggil otomatis.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from .scrapers import SOURCES, list_sources


def search_all(query: str, limit: int = 20) -> list[dict]:
    """
    Cari anime di SEMUA source yang tersedia.
    Returns list of dict: {title, url, status, rating, genres, image, source}
    
    Source ditandai di field 'source' (otakudesu / anoboy).
    Hasil diurutkan: source mana yang duluan return.
    """
    all_results = []
    
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as executor:
        futures = {}
        for source_id, source_info in SOURCES.items():
            future = executor.submit(_search_source, source_id, source_info, query, limit)
            futures[future] = source_id
        
        for future in as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                source_id = futures[future]
                # Silently skip failed source — user doesn't need to see this
    
    return all_results


def _search_source(source_id: str, source_info: dict, query: str, limit: int) -> list[dict]:
    """Search in a single source (helper for threading)."""
    try:
        module = source_info["module"]
        results = module.search_anime(query, limit)
        
        # Pastikan setiap result punya field 'source'
        for r in results:
            if "source" not in r or not r["source"]:
                r["source"] = source_id
        
        return results
    except Exception:
        return []


def get_episode_list(source_id: str, anime_url: str) -> list[dict]:
    """Get episode list from a specific source."""
    module = _get_module(source_id)
    if not module:
        return []
    
    try:
        episodes = module.get_episode_list(anime_url)
        # Filter: hanya episode yang punya nomor
        episodes = [ep for ep in episodes if ep["episode_num"] > 0]
        return sorted(episodes, key=lambda x: x["episode_num"])
    except Exception as e:
        print(f"[ERROR] Gagal ambil episode dari {source_id}: {e}")
        return []


def get_video_urls(source_id: str, episode_url: str) -> list[dict]:
    """Get video URLs from a specific source."""
    module = _get_module(source_id)
    if not module:
        return []
    
    try:
        return module.get_video_urls(episode_url)
    except Exception as e:
        print(f"[ERROR] Gagal ambil video URL dari {source_id}: {e}")
        return []


def resolve_stream_url(source_id: str, embed_url: str) -> str | None:
    """Resolve stream URL from a specific source."""
    module = _get_module(source_id)
    if not module:
        return embed_url
    
    try:
        if hasattr(module, "resolve_stream_url"):
            return module.resolve_stream_url(embed_url)
        return embed_url
    except Exception:
        return embed_url


def _get_module(source_id: str):
    """Get scraper module by source ID."""
    source = SOURCES.get(source_id)
    if source:
        return source["module"]
    
    # Fallback: coba cari berdasarkan nama
    for sid, sinfo in SOURCES.items():
        if source_id in sid or sid in source_id:
            return sinfo["module"]
    
    return None


# Shortcut: untuk backward compatibility
search_anime = search_all
