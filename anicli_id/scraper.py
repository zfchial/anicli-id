"""
Backward-compatible wrapper — meng-export semua fungsi dari scrapers package.
Agar kode lama yang import 'from .scraper import ...' tetap berfungsi.
"""

from .scrapers.otakudesu import *
