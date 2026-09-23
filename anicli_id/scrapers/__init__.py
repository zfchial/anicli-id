"""
Scrapers package — semua source anime yang didukung.
Saat ini: Otakudesu, Samehadaku
Anoboy: disabled (domain mati)
"""

from . import otakudesu
from . import samehadaku
from . import muse_indonesia

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
    "muse_indonesia": {
        "name": "Muse Indonesia",
        "url": "https://www.youtube.com/@MuseIndonesia",
        "description": "Anime resmi YouTube Muse Indonesia",
        "module": muse_indonesia,
    },
}

def get_source(name: str):
    source = SOURCES.get(name)
    if source:
        return source["module"]
    return None

def list_sources() -> list[dict]:
    return [
        {"id": k, "name": v["name"], "url": v["url"], "description": v["description"]}
        for k, v in SOURCES.items()
    ]
