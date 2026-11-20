# anicli-id

**Nonton anime subtitle Indonesia langsung dari terminal!**

CLI tool untuk streaming & download anime Sub Indo dari **Otakudesu** dan **Samehadaku** via **mpv** player.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-0.3.0-orange.svg)

## Fitur

- Multi-source: Otakudesu + Samehadaku
- Stream langsung via mpv (direct MP4, tanpa yt-dlp pun jalan)
- Download episode (yt-dlp / curl / wget)
- Marathon mode — auto-play episode berurutan
- Quick mode — langsung play dari command line
- Tampilan CLI dengan Rich

## Instalasi

### Linux

```bash
# Install mpv
sudo apt install mpv          # Debian/Ubuntu
sudo pacman -S mpv            # Arch
sudo dnf install mpv          # Fedora

# (Opsional tapi recommended)
pip install yt-dlp

# Clone & install
git clone https://github.com/zfchial/anicli-id.git
cd anicli-id
pip install -e .
```

### Windows

**Cara cepat (1x klik):** download [install.bat](https://github.com/zfchial/anicli-id/raw/refs/heads/main/install.bat), letakkan di folder mana pun, lalu double-click. Script otomatis memasang Python 3.9+, Git, mpv, yt-dlp, mengunduh source, membuat virtual environment, dan membuat shortcut `anicli-id.bat` di Desktop.

Catatan: klik "Ya" jika muncul UAC, dan "More info → Run anyway" jika SmartScreen memperingatkan file .bat. Python otomatis diunduh lewat winget, atau langsung dari python.org jika winget tidak tersedia.

**Cara manual:**

```powershell
# 1. Install Python 3.9+ dari python.org (centang "Add to PATH")

# 2. Install mpv (pilih salah satu):
#    - Download dari https://mpv.io/installation/ lalu tambah ke PATH
#    - Atau via Chocolatey:
choco install mpv
#    - Atau via Scoop:
scoop install mpv

# 3. (Opsional) Install yt-dlp
pip install yt-dlp

# 4. Clone & install
git clone https://github.com/zfchial/anicli-id.git
cd anicli-id
pip install -e .
```

### macOS

```bash
brew install mpv
pip install yt-dlp  # opsional

git clone https://github.com/zfchial/anicli-id.git
cd anicli-id
pip install -e .
```

## Cara Pakai

### Mode Interaktif

```bash
anicli-id
```

Flow: Pilih source → Search → Pilih anime → Pilih episode → Play/Download

### Quick Mode

```bash
anicli-id "frieren"                  # Play episode terbaru
anicli-id "frieren" -e 10            # Play episode 10
anicli-id "frieren" -d -e 10         # Download episode 10
anicli-id "frieren" -d -e 5 -q 480p  # Download 480p
```

### Opsi CLI

| Flag | Fungsi |
|------|--------|
| `-e`, `--episode` | Nomor episode |
| `-d`, `--download` | Download mode |
| `-q`, `--quality` | Kualitas: 360p / 480p / 720p / 1080p / best |
| `-s`, `--source` | Source: otakudesu / samehadaku / all |
| `-m`, `--marathon` | Marathon mode (auto-play) |
| `-v`, `--version` | Tampilkan versi |

## Dependencies

| Package | Versi | Fungsi |
|---------|-------|--------|
| `requests` | >= 2.31 | HTTP requests |
| `beautifulsoup4` | >= 4.12 | HTML parsing |
| `rich` | >= 13.0 | Tampilan terminal |
| `mpv` | - | Video player (external) |
| `yt-dlp` | - | Opsional, fallback downloader |

## Struktur

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

## Disclaimer

Tool ini hanya untuk penggunaan pribadi. Dukung official release anime dengan menonton dari platform resmi!

## License

MIT License
