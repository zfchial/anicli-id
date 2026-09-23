# 🎌 anicli-id

**Nonton anime subtitle Indonesia langsung dari terminal!**

CLI tool untuk streaming anime Sub Indo dari [Otakudesu](https://otakudesu.blog) via **mpv** player.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Source](https://img.shields.io/badge/Source-Otakudesu-red.svg)

## ✨ Fitur

- 🔍 **Search** anime berdasarkan judul
- 📺 **Pilih episode** dari daftar lengkap
- 🎬 **Stream langsung** via mpv (atau download)
- 💅 **Tampilan cantik** dengan Rich library
- ⚡ **Quick mode** — langsung play dari command line

## 📦 Instalasi

### Prasyarat

```bash
# Install mpv (wajib untuk streaming)
# Debian / Ubuntu
sudo apt install mpv

# Arch Linux
sudo pacman -S mpv

# Fedora
sudo dnf install mpv

# macOS
brew install mpv

# Windows (via Chocolatey)
choco install mpv
```

### Install anicli-id

```bash
# Clone repository
git clone https://github.com/user/anicli-id.git
cd anicli-id

# Install dependencies & package
pip install -e .

# Atau install langsung dari GitHub
pip install git+https://github.com/user/anicli-id.git
```

## 🚀 Cara Pakai

### Mode Interaktif (Recommended)

```bash
anicli-id
```

Lalu ikuti prompt:
1. Masukkan judul anime
2. Pilih anime dari hasil pencarian
3. Pilih episode
4. Pilih kualitas/sumber video
5. Play atau Download!

### Quick Mode

```bash
# Cari dan play episode terbaru
anicli-id "frieren"

# Play episode spesifik
anicli-id "jujutsu kaisen" --episode 15

# Singkat
anicli-id "sousou no frieren" -e 10
```

## 📸 Screenshot

```
╔═════════════════════════════════════════╗
║                                       ║
║     🎌  ANICLI-ID  🎌                 ║
║     Nonton Anime Sub Indo             ║
║     Langsung dari Terminal            ║
║                                       ║
║     Source: Otakudesu                 ║
║                                       ║
╚═════════════════════════════════════════╝

🔍 Cari anime yang ingin ditonton

> frieren

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        🔍 Hasil Pencarian              ┃
┣━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┫
┃  #   ┃ Judul                 ┃ Status  ┃Rating ┃ Genre     ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━┩
│  1   │ Sousou no Frieren... │ Ongoing │ 9.39  │ Adventure │
│  2   │ Sousou no Frieren... │Completed│ 8.99  │ Fantasy   │
└──────┴──────────────────────┴─────────┴───────┴───────────┘

> Pilih nomor anime [1]: 

📺 Daftar Episode
┏━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  #   ┃ Episode  ┃ Judul                         ┃
┡━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│  1   │ Episode 1 │ Sousou no Frieren S2 Ep 1... │
│  2   │ Episode 2 │ Sousou no Frieren S2 Ep 2... │
│ ...  │   ...    │             ...               │
│ 10   │ Episode 10│ Sousou no Frieren S2 Ep 10.. │
└──────┴──────────┴───────────────────────────────┘

▶️  Memutar: Sousou no Frieren Season 2 - Episode 10
   Kualitas: 720p
   Tekan 'q' untuk keluar, spasi untuk pause
```

## 🔧 Dependencies

| Package      | Versi   | Fungsi                        |
|--------------|---------|-------------------------------|
| `requests`   | ≥2.31   | HTTP requests ke Otakudesu    |
| `beautifulsoup4` | ≥4.12 | HTML parsing                  |
| `rich`       | ≥13.0   | Tampilan terminal yang cantik |
| `mpv`        | -       | Video player (external)       |

## 🏗 Struktur Proyek

```
anicli-id/
├── anicli_id/
│   ├── __init__.py      # Package info
│   ├── __main__.py      # Entry point
│   ├── cli.py           # Interface & flow logic
│   ├── scraper.py       # Otakudesu scraper
│   └── player.py        # mpv integration
├── pyproject.toml       # Package config
└── README.md            # Dokumentasi ini
```

## 🤝 Kontribusi

Contributions are welcome! Feel free to open issues or PRs.

## ⚠️ Disclaimer

Tool ini hanya untuk **penggunaan pribadi**. Dukungi official release anime dengan menonton dari platform resmi!

## 📜 License

MIT License
