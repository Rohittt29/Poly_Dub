import subprocess
import shutil
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def check_ffmpeg_installed() -> bool:
    """
    Checks if FFmpeg is installed and accessible in the system PATH.
    If not, displays a helpful installation guide and returns False.
    """
    if shutil.which("ffmpeg") is None:
        error_msg = (
            "[bold red]FFmpeg is not installed or not found in system PATH.[/bold red]\n\n"
            "This application requires FFmpeg for audio extraction and merging.\n\n"
            "[bold yellow]Installation Guide:[/bold yellow]\n"
            "• [bold]Windows:[/bold] Download from [link=https://gyan.dev/ffmpeg/builds/]gyan.dev[/link], extract, and add the 'bin' folder to your System PATH, or use `winget install ffmpeg`.\n"
            "• [bold]macOS:[/bold] Run `brew install ffmpeg` using Homebrew.\n"
            "• [bold]Linux (Ubuntu/Debian):[/bold] Run `sudo apt update && sudo apt install ffmpeg`.\n\n"
            "Please install FFmpeg and restart the application."
        )
        console.print(Panel(error_msg, title="Missing Dependency", expand=False))
        return False
    return True

def clean_directory(dir_path: Path):
    """Safely removes all files in the given directory."""
    if dir_path.exists() and dir_path.is_dir():
        for item in dir_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                pass # Don't crash on cleanup errors

def format_duration(seconds: float) -> str:
    """Formats seconds into MM:SS format."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
