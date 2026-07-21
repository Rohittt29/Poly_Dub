import yt_dlp
import subprocess
from pathlib import Path
from typing import Callable, Optional
from config import VIDEO_QUALITY


class VideoDownloader:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    def download(self, url: str, progress_callback: Optional[Callable[[float], None]] = None) -> Path:
        """
        Downloads a YouTube video to the temp directory.
        Returns the path to the downloaded video.
        """

        output_template = str(self.temp_dir / "%(id)s_original.%(ext)s")

        def hook(d):
            if d["status"] == "downloading" and progress_callback:
                try:
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    downloaded = d.get("downloaded_bytes", 0)
                    if total:
                        progress_callback((downloaded / total) * 100)
                except Exception:
                    pass

        ydl_opts = {
            "format": VIDEO_QUALITY,
            "outtmpl": output_template,
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Get the final merged filename
            final_path = Path(ydl.prepare_filename(info)).with_suffix(".mp4")

        if not final_path.exists():
            webm = final_path.with_suffix(".webm")
            if webm.exists():
                final_path = webm
            else:
                raise RuntimeError("Failed to download video or locate the downloaded file.")

        return final_path

    def extract_audio(self, video_path: Path) -> Path:
        """
        Extract audio from the downloaded video.
        """
        audio_path = video_path.with_name(f"{video_path.stem}_audio.wav")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(audio_path),
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")

        if not audio_path.exists():
            raise RuntimeError("Audio extraction failed.")

        return audio_path