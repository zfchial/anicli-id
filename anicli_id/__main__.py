"""
Main entry point untuk anicli-id CLI v0.2.0
Multi-source + Auto-play next episode!
"""

import sys
import argparse

from .cli import flow_search_and_play, flow_quick_play, flow_download_only, console
from .scrapers import list_sources


def main():
    """Entry point utama CLI."""
    sources_info = "\n".join(
        f"  {s['id']:12s} — {s['name']:12s} {s['description']}"
        for s in list_sources()
    )
    
    parser = argparse.ArgumentParser(
        prog="anicli-id",
        description=(
            "🎌 Nonton anime subtitle Indonesia langsung dari terminal\n"
            "Multi-source: Otakudesu + Samehadaku\n"
            "Auto-play: marathon mode!"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            f"\n[bold cyan]Source Tersedia:[/bold cyan]\n"
            f"{sources_info}\n"
            f"\n[bold cyan]Contoh:[/bold cyan]\n"
            f"  %(prog)s                          # Mode interaktif (pilih source)\n"
            f"  %(prog)s \"frieren\"                # Quick play\n"
            f"  %(prog)s \"frieren\" -e 10          # Play episode 10\n"
            f"  %(prog)s \"frieren\" -d -e 10       # Download episode 10\n"
        ),
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Judul anime (quick mode)",
    )
    
    parser.add_argument(
        "-e", "--episode",
        type=int,
        default=None,
        help="Nomor episode",
    )
    
    parser.add_argument(
        "-d", "--download",
        action="store_true",
        help="Download mode (perlu --episode)",
    )
    
    parser.add_argument(
        "-q", "--quality",
        type=str,
        default="720p",
        choices=["360p", "480p", "720p", "1080p", "best"],
        help="Kualitas video (default: 720p)",
    )
    
    parser.add_argument(
        "-s", "--source",
        type=str,
        default="all",
        choices=[s["id"] for s in list_sources()] + ["all"],
        help="Source anime (default: search all)",
    )
    
    parser.add_argument(
        "-m", "--marathon",
        action="store_true",
        help="Marathon mode: play from --episode to latest",
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s v0.3.0 — 🎌 Anime Sub Indo Multi-Source",
    )

    args = parser.parse_args()

    if args.query:
        if args.download:
            # Download mode
            if not args.episode:
                console.print("[red]❌ Download mode perlu nomor episode (-e / --episode)[/red]")
                console.print("[dim]Contoh: anicli-id \"frieren\" -d -e 10[/dim]\n")
                sys.exit(1)
            flow_download_only(args.query, args.episode, args.quality)
        else:
            # Quick play
            flow_quick_play(args.query, args.episode, args.source)
    else:
        # Interactive mode
        flow_search_and_play()


if __name__ == "__main__":
    main()
