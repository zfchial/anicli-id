"""
Player module — handle streaming & download video
Supports: mpv (direct), mpv + yt-dlp (for protected streams), download via yt-dlp/curl/wget
"""

import subprocess
import shutil
import sys
import os

from rich.console import Console

console = Console()


def check_mpv_installed() -> bool:
    """Cek apakah mpv terinstall di sistem."""
    return shutil.which("mpv") is not None


def check_ytdlp_installed() -> bool:
    """Cek apakah yt-dlp terinstall."""
    return shutil.which("yt-dlp") is not None


def play_video(url: str, quality: str = "", title: str = "", use_ytdlp: bool = True) -> bool:
    """
    Putar video menggunakan mpv.
    
    Jika use_ytdlp=True dan yt-dlp tersedia, gunakan mpv + yt-dlp 
    (direkomendasikan untuk link yang dilindungi/redirect).
    Jika tidak, coba direct stream ke mpv.
    
    Returns True jika berhasil, False jika gagal.
    """
    if not check_mpv_installed():
        print("\n[ERROR] mpv tidak ditemukan!")
        print("  Install dulu:")
        print("  • Debian/Ubuntu: sudo apt install mpv")
        print("  • Arch:         sudo pacman -S mpv")
        print("  • Fedora:       sudo dnf install mpv")
        print("  • macOS:        brew install mpv")
        print("  • Windows:      choco install mpv")
        return False

    # Tentukan strategi pemutaran
    ytdlp_available = check_ytdlp_installed()
    
    if use_ytdlp and ytdlp_available:
        return _play_with_ytdlp(url, quality, title)
    else:
        if use_ytdlp and not ytdlp_available:
            print("[INFO] yt-dlp tidak ditemukan. Mencoba direct stream...")
            print("       Install yt-dlp untuk hasil terbaik: pip install yt-dlp")
            print()
        return _play_direct(url, quality, title)


def play_multiple(video_list: list[tuple], title_prefix: str = "") -> bool:
    """
    Putar MULTIPLE video berurutan (auto-play mode).
    video_list: list of (url, quality, title, use_ytdlp)
    Setelah satu video selesai, langsung play video berikutnya.
    Pengguna bisa menekan Ctrl+C untuk stop auto-play.
    """
    total = len(video_list)
    
    console.print(f"\n[bold cyan]🎬 AUTO-PLAY MODE: {total} episode[/bold cyan]")
    console.print(f"   [dim]Tekan Ctrl+C untuk stop auto-play[/dim]\n")
    
    for i, item in enumerate(video_list, 1):
        url = item[0]
        quality = item[1]
        title = item[2]
        use_ytdlp = item[3] if len(item) > 3 else True
        
        full_title = f"{title_prefix} - {title}" if title_prefix else title
        console.print(f"\n[cyan]▶️  [{i}/{total}] {full_title}[/cyan]")
        
        try:
            success = play_video(url, quality=quality, title=full_title, use_ytdlp=use_ytdlp)
            if not success:
                console.print(f"[yellow]⚠️  Gagal memutar episode {i}. Skip ke berikutnya...[/yellow]")
        except KeyboardInterrupt:
            console.print("\n[yellow]⏸️  Auto-play dihentikan.[/yellow]")
            return False
    
    console.print(f"\n[green]✅ Auto-play selesai! ({total} episode)[/green]")
    return True


def _play_with_ytdlp(url: str, quality: str = "", title: str = "") -> bool:
    """Play video using mpv + yt-dlp pipe."""
    display_title = title or "Anime"
    
    fmt = _get_ytdlp_format(quality)
    cmd = [
        "mpv",
        f"--title={display_title}",
        "--force-window=immediate",
        "--ytdl",
        f"--ytdl-format={fmt}",
        "--",
        url,
    ]

    print(f"\n▶️  Memutar: {display_title}")
    print(f"   Kualitas: {quality or 'auto'}")
    print(f"   Mode: mpv + yt-dlp")
    print("   Tekan 'q' untuk keluar, spasi untuk pause\n")

    try:
        process = subprocess.run(cmd)
        return process.returncode == 0
    except KeyboardInterrupt:
        print("\n⏹  Dihentikan oleh user.")
        return True
    except Exception as e:
        print(f"\n[ERROR] Gagal memutar (yt-dlp mode): {e}")
        print("       Mencoba direct stream...")
        return _play_direct(url, quality, title)


def _play_direct(url: str, quality: str = "", title: str = "") -> bool:
    """Play video directly with mpv (no yt-dlp)."""
    display_title = title or "Anime"
    
    cmd = [
        "mpv",
        f"--title={display_title}",
        "--force-window=immediate",
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--referrer=https://otakudesu.blog/",
        "--",
        url,
    ]

    print(f"\n▶️  Memutar: {display_title}")
    print(f"   Kualitas: {quality or 'default'}")
    print(f"   Mode: Direct stream")
    print("   Tekan 'q' untuk keluar, spasi untuk pause\n")

    try:
        process = subprocess.run(cmd)
        return process.returncode == 0
    except KeyboardInterrupt:
        print("\n⏹  Dihentikan oleh user.")
        return True
    except Exception as e:
        print(f"\n[ERROR] Gagal memutar video: {e}")
        return False


def _get_ytdlp_format(quality: str) -> str:
    """
    Tentukan format string untuk yt-dlp berdasarkan quality label.
    """
    q_lower = quality.lower() if quality else ""
    
    if "1080" in q_lower:
        return "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
    elif "720" in q_lower:
        return "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    elif "480" in q_lower:
        return "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
    elif "360" in q_lower:
        return "worst"
    else:
        return "best"


def download_video(url: str, output_path: str | None = None, title: str = "", quality: str = "") -> bool:
    """
    Download video.
    Priority: yt-dlp > curl > wget
    
    Returns True jika berhasil.
    """
    # Generate filename jika tidak diberikan
    if not output_path:
        safe_title = _sanitize_filename(title or "anime_episode")
        output_path = f"./{safe_title}.mp4"

    # Coba yt-dlp dulu (paling reliable)
    if check_ytdlp_installed():
        return _download_with_ytdlp(url, output_path, quality)

    # Fallback ke curl
    if shutil.which("curl"):
        return _download_curl(url, output_path)

    # Fallback ke wget
    if shutil.which("wget"):
        return _download_wget(url, output_path)

    print("[ERROR] Tidak ada downloader yang tersedia!")
    print("  Install salah satu: yt-dlp (recommended), curl, atau wget")
    print("  yt-dlp: pip install yt-dlp")
    return False


def _download_with_ytdlp(url: str, output_path: str, quality: str = "") -> bool:
    """Download menggunakan yt-dlp."""
    fmt = _get_ytdlp_format(quality)
    
    cmd = [
        "yt-dlp",
        "-o", output_path,
        "--format", fmt,
        "--no-playlist",
        url,
    ]

    print(f"\n📥 Mendownload: {output_path}")
    print(f"   Format: {quality or 'best'}")
    print()

    try:
        result = subprocess.run(cmd)
        if result.returncode == 0:
            print(f"\n✅ Download selesai: {output_path}")
            return True
        else:
            print(f"\n❌ Download gagal dengan kode: {result.returncode}")
            return False
    except KeyboardInterrupt:
        print("\n⏹  Download dibatalkan.")
        return False
    except Exception as e:
        print(f"[ERROR] yt-dlp gagal: {e}")
        return False


def _download_curl(url: str, output_path: str) -> bool:
    """Download menggunakan curl."""
    cmd = [
        "curl",
        "-L",           # Follow redirects
        "-o", output_path,
        "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "-H", "Referer: https://otakudesu.blog/",
        "--progress-bar",
        url,
    ]

    print(f"\n📥 Mendownload (curl): {output_path}")

    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] curl gagal: {e}")
        return False


def _download_wget(url: str, output_path: str) -> bool:
    """Download menggunakan wget."""
    cmd = [
        "wget",
        "-O", output_path,
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "--referer=https://otakudesu.blog/",
        url,
    ]

    print(f"\n📥 Mendownload (wget): {output_path}")

    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] wget gagal: {e}")
        return False


def _sanitize_filename(name: str) -> str:
    """Sanitasi nama file — hapus karakter tidak aman."""
    import re
    # Hapus/hapus karakter tidak aman
    name = re.sub(r'[^\w\s\-_.()\[\]]', '', name)
    name = name.replace(' ', '_')
    # Batas panjang
    if len(name) > 200:
        name = name[:200]
    return name.strip('_') or "anime"


def list_available_players() -> dict:
    """List available video players and tools."""
    return {
        "mpv": check_mpv_installed(),
        "yt-dlp": check_ytdlp_installed(),
        "curl": shutil.which("curl") is not None,
        "wget": shutil.which("wget") is not None,
    }
