import subprocess
from pathlib import Path
from typing import List, Dict
from utils import format_duration
from logger import get_logger
import os

logger = get_logger("Remixer")

def generate_srt(segments: List[Dict], output_path: Path):
    """Generates an SRT subtitle file from translated segments."""
    def format_srt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_srt_time(seg['start'])
        end = format_srt_time(seg['end'])
        text = seg.get('translated_text', '').strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

class Remixer:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        
    def _get_audio_duration(self, audio_path: str) -> float:
        """Use ffprobe to get duration of an audio file."""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 0.0

    def match_durations_and_concat(self, segments: List[Dict], output_merged_path: Path):
        """
        Adjusts speed of each TTS chunk to fit within the segment duration using FFmpeg atempo.
        Then concatenates them sequentially with exact silence padding based on Whisper timestamps.
        """
        # Prepare a complex filtergraph for ffmpeg or use individual files and a concat file
        # We will adjust each chunk, then use a concat list.
        concat_list_path = self.temp_dir / "concat.txt"
        
        # Adjust individual chunks
        adjusted_chunks = []
        for seg in segments:
            chunk_path = seg.get("audio_chunk")
            if not chunk_path or not Path(chunk_path).exists():
                continue
                
            orig_duration = seg['end'] - seg['start']
            tts_duration = self._get_audio_duration(chunk_path)
            
            adjusted_path = self.temp_dir / f"adjusted_{Path(chunk_path).name}"
            
            if tts_duration > 0:
                # Calculate required speedup or slowdown
                ratio = tts_duration / orig_duration
                # atempo filter range is 0.5 to 100.0
                ratio = max(0.5, min(100.0, ratio))
                
                # Apply atempo
                cmd = ["ffmpeg", "-y", "-i", chunk_path, "-filter:a", f"atempo={ratio}", str(adjusted_path)]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # If chunk is broken, just copy or skip
                continue
                
            if adjusted_path.exists():
                adjusted_chunks.append({
                    "path": adjusted_path,
                    "start": seg['start']
                })

        # Build concat with silences
        with open(concat_list_path, 'w', encoding='utf-8') as f:
            current_time = 0.0
            for chunk in adjusted_chunks:
                start_time = chunk["start"]
                if start_time > current_time:
                    # Insert silence
                    silence_dur = start_time - current_time
                    # We can use anullsrc for silence, but a simple way in concat is to just specify anullsrc
                    # Actually concat demuxer doesn't easily do silence generation. 
                    # Simpler approach: generate a silence file.
                    silence_path = self.temp_dir / f"silence_{current_time:.2f}.mp3"
                    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono", "-t", str(silence_dur), "-q:a", "9", "-acodec", "libmp3lame", str(silence_path)]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    f.write(f"file '{silence_path.resolve()}'\n")
                    current_time += silence_dur
                
                # Add the actual chunk
                chunk_dur = self._get_audio_duration(str(chunk["path"]))
                f.write(f"file '{chunk['path'].resolve()}'\n")
                current_time += chunk_dur

        # Concat all parts
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
            "-i", str(concat_list_path), "-c", "copy", str(output_merged_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"Concat failed: {res.stderr}")

    def replace_audio(self, video_path: Path, new_audio_path: Path, final_output_path: Path):
        """Replaces the audio track in the video with the new one."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(new_audio_path),
            "-map", "0:v:0", # Map original video
            "-map", "1:a:0", # Map new audio
            "-c:v", "copy",  # Don't re-encode video
            "-c:a", "aac",   # Encode audio to AAC for wide compatibility
            "-b:a", "192k",
            "-shortest",     # Finish encoding when shortest stream ends
            str(final_output_path)
        ]
        
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"Final merge failed: {res.stderr}")
            raise RuntimeError("Failed to replace audio in final video.")
