
**Nonton anime subtitle Indonesia langsung dari terminal!**

CLI tool untuk streaming & download anime Sub Indo dari **Otakudesu** dan **Samehadaku** via **mpv** player.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-0.3.0-orange.svg)


- Multi-source: Otakudesu + Samehadaku
- Stream langsung via mpv (direct MP4, tanpa yt-dlp pun jalan)
- Download episode (yt-dlp / curl / wget)
- Marathon mode — auto-play episode berurutan
- Quick mode — langsung play dari command line
- Tampilan CLI dengan Rich



```bash
sudo apt install mpv          # Debian/Ubuntu
sudo pacman -S mpv            # Arch
sudo dnf install mpv          # Fedora

pip install yt-dlp

git clone https://github.com/zfchial/anicli-id.git
cd anicli-id
pip install -e .
```


```powershell

choco install mpv
scoop install mpv

pip install yt-dlp

git clone https://github.com/zfchial/anicli-id.git
cd anicli-id
pip install -e .
```


```bash
brew install mpv
pip install yt-dlp  # opsional

git clone https://github.com/zfchial/anicli-id.git
cd anicli-id
pip install -e .
```



```bash
anicli-id
```

Flow: Pilih source → Search → Pilih anime → Pilih episode → Play/Download


```bash
anicli-id "frieren"                  # Play episode terbaru
anicli-id "frieren" -e 10            # Play episode 10
anicli-id "frieren" -d -e 10         # Download episode 10
anicli-id "frieren" -d -e 5 -q 480p  # Download 480p
```


| Flag | Fungsi |
|------|--------|
| `-e`, `--episode` | Nomor episode |
| `-d`, `--download` | Download mode |
| `-q`, `--quality` | Kualitas: 360p / 480p / 720p / 1080p / best |
| `-s`, `--source` | Source: otakudesu / samehadaku / all |
| `-m`, `--marathon` | Marathon mode (auto-play) |
| `-v`, `--version` | Tampilkan versi |


| Package | Versi | Fungsi |
|---------|-------|--------|
| `requests` | >= 2.31 | HTTP requests |
| `beautifulsoup4` | >= 4.12 | HTML parsing |
| `rich` | >= 13.0 | Tampilan terminal |
| `mpv` | - | Video player (external) |
| `yt-dlp` | - | Opsional, fallback downloader |


```
anicli-id/
├── anicli_id/
│   ├── __init__.py
│   ├── __main__.py       # Entry point + argparse
│   ├── cli.py            # Interface & flow logic
│   ├── player.py         # mpv/yt-dlp playback & download
│   ├── sources.py        # Multi-source abstraction
│   └── scrapers/
│       ├── __init__.py   # Source registry
│       ├── otakudesu.py  # Otakudesu scraper
│       └── samehadaku.py # Samehadaku scraper
├── pyproject.toml
└── README.md
```


Tool ini hanya untuk penggunaan pribadi. Dukung official release anime dengan menonton dari platform resmi!


MIT License
