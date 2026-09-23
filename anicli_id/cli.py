"""
CLI Interface untuk anicli-id v0.2.0
Mendukung multi-source (Otakudesu, Anoboy) dan auto-play next episode!
"""

import sys
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.columns import Columns
from rich.text import Text

from .sources import search_all, get_episode_list, get_video_urls, resolve_stream_url
from .scrapers import list_sources
from .player import play_video, play_multiple, download_video, check_mpv_installed, list_available_players

console = Console()

BANNER = "[bold magenta]ANICLI-ID[/bold magenta] [dim]v0.3.0[/dim]"

SOURCE_COLORS = {
    "otakudesu": "blue",
    "anoboy": "green",
    "samehadaku": "yellow",
    "muse_indonesia": "red",
}


def print_banner():
    console.print(Panel(BANNER, subtitle="Nonton anime dari terminal", border_style="magenta", padding=(0, 2)))


def print_system_info():
    tools = list_available_players()
    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column("Label", style="cyan")
    table.add_column("Value")
    table.add_row("Sumber", ", ".join(s["name"] for s in list_sources()))
    table.add_row("Player", "[green]mpv siap[/green]" if tools["mpv"] else "[red]mpv tidak ditemukan[/red]")
    table.add_row("YouTube", "[green]yt-dlp siap[/green]" if tools["yt-dlp"] else "[yellow]yt-dlp tidak ditemukan[/yellow]")
    console.print(Panel(table, title="Status", border_style="dim", padding=(0, 1)))


def print_search_results(results: list[dict]):
    if not results:
        console.print("\n[yellow]  Tidak ditemukan hasil pencarian.[/yellow]")
        console.print("[dim]Coba gunakan kata kunci lain atau cek ejaan.[/dim]\n")
        return

    table = Table(
        title=f"Hasil Pencarian · {len(results)} hasil",
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        pad_edge=True,
    )
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Judul Anime", style="bold cyan", min_width=36, overflow="ellipsis")
    table.add_column("Sumber", justify="center", min_width=12)
    table.add_column("Info", style="green", justify="center", overflow="ellipsis")

    for i, anime in enumerate(results, 1):
        title = anime["title"]
        title = re.sub(r'\s*Subtitle\s*Indonesia', '', title, flags=re.IGNORECASE).strip()
        
        source_id = anime.get("source", "?")
        color = SOURCE_COLORS.get(source_id, "cyan")
        source_display = f"[{color}]{source_id.upper()}[/{color}]"
        
        table.add_row(
            str(i),
            title,
            source_display,
            anime.get("status") or anime.get("rating") or "-",
        )

    console.print(table)


def print_episode_list(episodes: list[dict], anime_title: str = ""):
    if not episodes:
        console.print("\n[yellow]  Tidak ada episode ditemukan.[/yellow]\n")
        return

    ep_numbers = [ep["episode_num"] for ep in episodes]
    total = len(episodes)
    
    table = Table(
        title=f"Episode · {anime_title[:40]} · {total} tersedia",
        title_style="bold green",
        show_header=True,
        header_style="bold green",
        border_style="green",
    )
    table.add_column("#", style="dim", width=5, justify="center")
    table.add_column("Episode", style="bold", justify="center")
    table.add_column("Judul", style="cyan")

    for i, ep in enumerate(episodes, 1):
        title = ep["title"]
        title = re.sub(r'\s*Subtitle\s*Indonesia', '', title, flags=re.IGNORECASE).strip()
        
        ep_str = f"Episode {ep['episode_num']}"
        if ep == episodes[-1]:
            ep_str += " [bold green][/]"
        
        table.add_row(str(i), ep_str, title[:60])

    console.print(table)
    console.print(f"[dim]Rentang episode: {ep_numbers[0]}–{ep_numbers[-1]} · pilih nomor episode[/dim]")


def print_video_options(videos: list[dict]):
    if not videos:
        console.print("\n[red] Tidak ada link video tersedia.[/red]\n")
        return

    table = Table(
        title=f"Sumber Video · {len(videos)} pilihan",
        title_style="bold yellow",
        show_header=True,
        header_style="bold yellow",
        border_style="yellow",
    )
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Type / Kualitas", style="bold", min_width=22)
    table.add_column("Mirror / Sumber", style="cyan", min_width=16)

    for i, vid in enumerate(videos, 1):
        quality = vid.get("quality", "unknown")
        mirror = vid.get("mirror_name", vid.get("source", "unknown"))
        
        if "STREAM" in quality.upper():
            quality = f"[bold green] {quality}[/bold green]"
            mirror = f"[bold green]{mirror}[/bold green]"
        elif "360" in quality:
            quality = f"[dim]{quality}[/dim]"
        elif "1080" in quality:
            quality = f"[bold]{quality}[/bold]"
        
        table.add_row(str(i), quality, mirror[:20])

    console.print(table)



def select_source() -> str | None:
    sources = list_sources()
    
    console.print("\n[bold cyan]Sumber Streaming[/bold cyan]")
    console.print("[dim]Pilih sumber untuk mencari judul anime[/dim]\n")
    
    for i, s in enumerate(sources, 1):
        color = SOURCE_COLORS.get(s["id"], "cyan")
        console.print(f"  [{color}]{i}[/{color}] [bold {color}]{s['name']}[/bold {color}] — [dim]{s['description']}[/dim]")
    
    console.print("  [yellow]A[/yellow] [bold]Semua sumber[/bold] — [dim]gabungkan hasil pencarian[/dim]")
    console.print()
    
    choice = Prompt.ask("Pilihan", default="1")
    
    if choice.upper() == "A":
        return "all"
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(sources):
            return sources[idx]["id"]
    except ValueError:
        pass
    
    return "all"


def _pick_best_video(videos: list[dict]) -> int:
    """
    Pilih indeks video terbaik untuk streaming.
    Prioritas: direct_stream 720p > direct_stream 480p > direct lainnya > embed
    """
    if not videos:
        return 0

    preferred = ["720p", "480p", "1080p", "360p"]

    for q in preferred:
        for i, v in enumerate(videos):
            if q in v.get("quality", "").lower() and v.get("source") == "direct_stream":
                return i

    for i, v in enumerate(videos):
        if v.get("source") == "direct_stream":
            return i

    for q in preferred:
        for i, v in enumerate(videos):
            if q in v.get("quality", "").lower():
                return i

    return 0



def flow_search_and_play():
    """
    Flow utama interaktif:
    Pilih Source → Search → Pilih Anime → Pilih Episode(s) → Pilih Kualitas → Play/Download
    """
    print_banner()
    print_system_info()

    if not check_mpv_installed():
        console.print("\n[bold red]  mpv tidak terinstall![/bold red]")
        console.print("[dim]Install: [cyan]sudo apt install mpv[/cyan][/dim]\n")
        if not Confirm.ask("Lanjutkan tanpa mpv?"):
            return

    source_id = select_source()
    if not source_id:
        return
    
    console.print("\n[bold] Cari anime[/bold]")
    query = Prompt.ask("   Masukkan judul").strip()
    
    if not query:
        console.print("[yellow]Query kosong.[/yellow]")
        return

    with console.status("[bold green] Mencari di semua sumber...[/bold green]"):
        if source_id == "all":
            results = search_all(query)
        else:
            from .scrapers import SOURCES
            module = SOURCES[source_id]["module"]
            results = module.search_anime(query)
            for r in results:
                r["source"] = source_id

    print_search_results(results)
    if not results:
        return

    console.print()
    choice = IntPrompt.ask(
        "Pilih nomor anime",
        default=1,
        choices=[str(i) for i in range(1, len(results) + 1)],
    )

    selected = results[choice - 1]
    src = selected.get("source", "otakudesu")
    anime_title = re.sub(r'\s*Subtitle\s*Indonesia', '', selected['title'], flags=re.IGNORECASE).strip()
    
    console.print(f"\n[bold green][/bold green] [bold cyan]{anime_title}[/bold cyan]")
    console.print(f"   [dim]Source: {src.upper()} | Status: {selected.get('status', '-')}[/dim]")

    with console.status(f"[bold green] Mengambil episode...[/bold green]"):
        episodes = get_episode_list(src, selected["url"])

    print_episode_list(episodes, anime_title)
    if not episodes:
        return

    console.print("\n[bold] Pilih Mode[/bold]")
    console.print("  [cyan]1[/cyan]. Nonton 1 episode")
    console.print("  [yellow]M[/yellow]. Marathon / Auto-play (nonton berurutan)")
    console.print()
    
    mode = Prompt.ask("Pilih", choices=["1", "m", "M"], default="1").lower()
    
    ep_numbers = [ep["episode_num"] for ep in episodes]
    start_ep = episodes[-1]["episode_num"]  # Default: episode terbaru
    
    if mode == "1":
        console.print(f"\n[dim]Tersedia: Ep {ep_numbers[0]} – {ep_numbers[-1]}[/dim]")
        ep_choice = IntPrompt.ask("Nomor episode", default=start_ep)
        
        selected_eps = []
        for ep in episodes:
            if ep["episode_num"] == ep_choice:
                selected_eps.append(ep)
                break
        if not selected_eps and 1 <= ep_choice <= len(episodes):
            selected_eps.append(episodes[ep_choice - 1])
        
        if not selected_eps:
            console.print(f"[red] Episode {ep_choice} tidak ditemukan.[/red]")
            return
    
    else:
        console.print(f"\n[dim]Tersedia: Ep {ep_numbers[0]} – {ep_numbers[-1]}[/dim]")
        start = IntPrompt.ask("Mulai dari episode", default=start_ep)
        end = IntPrompt.ask("Sampai episode", default=ep_numbers[-1])
        
        selected_eps = [ep for ep in episodes if start <= ep["episode_num"] <= end]
        if not selected_eps:
            console.print("[red] Tidak ada episode dalam range tersebut.[/red]")
            return
        
        console.print(f"[green] Akan memutar {len(selected_eps)} episode (Ep {start} – {end})[/green]")

    selected_videos = []
    stream_urls = []
    
    for ep in selected_eps:
        ep_title_clean = re.sub(r'\s*Subtitle\s*Indonesia', '', ep['title'], flags=re.IGNORECASE).strip()
        
        with console.status(f"[bold green] Mengambil link: Ep {ep['episode_num']}...[/bold green]"):
            videos = get_video_urls(src, ep["url"])
        
        if videos:
            selected_videos.append({
                "ep": ep,
                "title": ep_title_clean,
                "videos": videos,
            })
    
    if not selected_videos:
        console.print("[red] Gagal mendapatkan link video.[/red]")
        return

    first_videos = selected_videos[0]["videos"]
    print_video_options(first_videos)
    
    console.print()
    default_video_idx = _pick_best_video(first_videos)
    vid_choice = IntPrompt.ask(
        "Pilih sumber video",
        default=default_video_idx + 1,
        choices=[str(i) for i in range(1, len(first_videos) + 1)],
    )
    
    console.print()
    actions = ["play"]
    if mode == "m":
        actions.append("play-all")
    actions.extend(["download", "copy-url", "batal"])
    
    if mode == "1":
        action = Prompt.ask("Aksi", choices=actions, default="play")
    else:
        action = Prompt.ask("Aksi", choices=actions, default="play-all")
    
    title_full = f"{anime_title} - {selected_eps[0]['title']}"
    title_full = re.sub(r'\s*Subtitle\s*Indonesia', '', title_full, flags=re.IGNORECASE).strip()
    
    if action == "play":
        first = selected_videos[0]
        vid = first["videos"][vid_choice - 1]
        stream_url = resolve_stream_url(src, vid["url"])
        
        ep_title = first["title"]
        play_title = f"{anime_title} - {ep_title}"
        needs_ytdlp = vid.get("source") != "direct_stream"
        
        ok = play_video(stream_url, quality=vid["quality"], title=play_title, use_ytdlp=False, audio_url=vid.get("audio_url", ""))
        if not ok:
            for alt in first["videos"]:
                if alt is vid or alt.get("source") != "direct_stream":
                    continue
                alt_url = resolve_stream_url(src, alt["url"])
                if play_video(alt_url, quality=alt["quality"], title=play_title, use_ytdlp=False):
                    break
        
        if len(selected_videos) > 1:
            console.print()
            if Confirm.ask("Lanjut ke episode berikutnya?", default=False):
                _auto_play_remaining(selected_videos[1:], vid_choice - 1, anime_title, src)
    
    elif action == "play-all":
        video_list = []
        for ep_data in selected_videos:
            vid = ep_data["videos"][vid_choice - 1]
            stream_url = resolve_stream_url(src, vid["url"])
            needs_ytdlp = vid.get("source") != "direct_stream"
            video_list.append((stream_url, vid["quality"], ep_data["title"], needs_ytdlp))
        
        play_multiple(video_list, title_prefix=anime_title)
    
    elif action == "download":
        ep_data = selected_videos[0]
        vid = ep_data["videos"][vid_choice - 1]
        
        safe_filename = re.sub(r'[^\w\s\-_.()]', '', title_full).replace(' ', '_')
        output_path = f"./{safe_filename}.mp4"
        download_video(vid["url"], output_path=output_path, title=title_full, quality=vid["quality"])
    
    elif action == "copy-url":
        ep_data = selected_videos[0]
        vid = ep_data["videos"][vid_choice - 1]
        url = vid["url"]
        console.print(f"\n[cyan]{url}[/cyan]")
        
        try:
            import pyperclip
            pyperclip.copy(url)
            console.print("[green] URL disalin![/green]")
        except ImportError:
            pass
    
    else:
        console.print("[dim]Dibatalkan. [/dim]")


def _auto_play_remaining(remaining_videos: list, vid_idx: int, anime_title: str, src: str):
    video_list = []
    for ep_data in remaining_videos:
        try:
            vid = ep_data["videos"][vid_idx]
            stream_url = resolve_stream_url(src, vid["url"])
            needs_ytdlp = vid.get("source") != "direct_stream"
            video_list.append((stream_url, vid["quality"], ep_data["title"], needs_ytdlp))
        except (IndexError, Exception):
            if ep_data["videos"]:
                vid = ep_data["videos"][0]
                stream_url = resolve_stream_url(src, vid["url"])
                needs_ytdlp = vid.get("source") != "direct_stream"
                video_list.append((stream_url, vid["quality"], ep_data["title"], needs_ytdlp))
    
    if video_list:
        play_multiple(video_list, title_prefix=anime_title)


def flow_quick_play(anime_query: str, episode_num: int | None = None, source_filter: str = "all"):
    with console.status(f"[bold green] Mencari: {anime_query}...[/bold green]"):
        if source_filter == "all":
            results = search_all(anime_query)
        else:
            from .scrapers import SOURCES
            if source_filter in SOURCES:
                module = SOURCES[source_filter]["module"]
                results = module.search_anime(anime_query)
                for r in results:
                    r["source"] = source_filter
            else:
                results = search_all(anime_query)

    if not results:
        console.print(f"[red] Tidak ditemukan: '{anime_query}'[/red]")
        return

    selected = results[0]
    src = selected.get("source", "otakudesu")
    anime_title = re.sub(r'\s*Subtitle\s*Indonesia', '', selected['title'], flags=re.IGNORECASE).strip()
    console.print(f"[green][/green] [cyan]{anime_title}[/cyan] [dim]({src.upper()})[/dim]")

    with console.status("[bold green] Mengambil episode...[/bold green]"):
        episodes = get_episode_list(src, selected["url"])

    if not episodes:
        console.print("[red] Tidak ada episode.[/red]")
        return

    if episode_num is None:
        ep = episodes[-1]
    else:
        ep = next((e for e in episodes if e["episode_num"] == episode_num), None)
        if not ep:
            console.print(f"[red] Episode {episode_num} tidak ditemukan.[/red]")
            console.print(f"[dim]Tersedia: Ep {episodes[0]['episode_num']} - {episodes[-1]['episode_num']}[/dim]")
            return

    ep_title = re.sub(r'\s*Subtitle\s*Indonesia', '', ep['title'], flags=re.IGNORECASE).strip()
    console.print(f"[green][/green] {ep_title}")

    with console.status("[bold green] Mengambil link video...[/bold green]"):
        videos = get_video_urls(src, ep["url"])

    if not videos:
        console.print("[red] Tidak ada link video.[/red]")
        return

    best_idx = _pick_best_video(videos)
    vid = videos[best_idx]
    
    stream_url = resolve_stream_url(src, vid["url"])
    full_title = f"{anime_title} - {ep_title}"
    
    needs_ytdlp = vid.get("source") != "direct_stream"
    
    play_video(stream_url, quality=vid["quality"], title=full_title, use_ytdlp=needs_ytdlp)


def flow_download_only(anime_query: str, episode_num: int, quality: str = "720p"):
    with console.status(f"[bold green] Mencari: {anime_query}...[/bold green]"):
        results = search_all(anime_query)

    if not results:
        console.print(f"[red] Tidak ditemukan: '{anime_query}'[/red]")
        return

    selected = results[0]
    src = selected.get("source", "otakudesu")
    anime_title = re.sub(r'\s*Subtitle\s*Indonesia', '', selected['title'], flags=re.IGNORECASE).strip()
    console.print(f"[green][/green] [cyan]{anime_title}[/cyan] [dim]({src.upper()})[/dim]")

    with console.status("[bold green] Mengambil episode...[/bold green]"):
        episodes = get_episode_list(src, selected["url"])

    if not episodes:
        console.print("[red] Tidak ada episode.[/red]")
        return

    ep = next((e for e in episodes if e["episode_num"] == episode_num), None)
    if not ep:
        console.print(f"[red] Episode {episode_num} tidak ditemukan.[/red]")
        console.print(f"[dim]Tersedia: Ep {episodes[0]['episode_num']} - {episodes[-1]['episode_num']}[/dim]")
        return

    ep_title = re.sub(r'\s*Subtitle\s*Indonesia', '', ep['title'], flags=re.IGNORECASE).strip()
    console.print(f"[green][/green] {ep_title}")

    with console.status("[bold green] Mengambil link video...[/bold green]"):
        videos = get_video_urls(src, ep["url"])

    if not videos:
        console.print("[red] Tidak ada link video.[/red]")
        return

    vid = None
    q_lower = quality.lower()
    for v in videos:
        if q_lower in v.get("quality", "").lower() and v.get("source") == "download_mirror":
            vid = v
            break
    if not vid:
        for v in videos:
            if v.get("source") == "download_mirror":
                vid = v
                break
    if not vid:
        vid = videos[0]

    title_full = f"{anime_title} - {ep_title}"
    safe_filename = re.sub(r'[^\w\s\-_.()]', '', title_full).replace(' ', '_')
    output_path = f"./{safe_filename}.mp4"
    download_video(vid["url"], output_path=output_path, title=title_full, quality=vid["quality"])


def main():
    flow_search_and_play()
