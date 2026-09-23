"""
Scrapers package — semua source anime yang didukung.
Saat ini: Otakudesu, Samehadaku
Anoboy: disabled (domain mati)
"""

from . import otakudesu
from . import samehadaku

SOURCES = {
    "otakudesu": {
        "name": "Otakudesu",
        "url": "https://otakudesu.blog",
        "description": "Anime Sub Indo dengan banyak pilihan kualitas & mirror",
        "module": otakudesu,
    },
    "samehadaku": {
        "name": "Samehadaku",
        "url": "https://samehadaku.li",
        "description": "Anime Sub Indo populer dengan update lengkap",
        "module": samehadaku,
    },
}

def get_source(name: str):
    """Get a source module by name."""
    source = SOURCES.get(name)
    if source:
        return source["module"]
    return None

def list_sources() -> list[dict]:
    """List all available sources with info."""
    return [
        {"id": k, "name": v["name"], "url": v["url"], "description": v["description"]}
        for k, v in SOURCES.items()
    ]
