import argparse
import sys
import os
import signal
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from config import OUTPUT_DIR, TEMP_DIR, LOG_DIR, WHISPER_MODEL, WHISPER_DEVICE, TTS_VOICE
from utils import check_ffmpeg_installed, clean_directory, format_duration
from progress import DubbingProgress
from logger import get_logger
from state_manager import StateManager
from downloader import VideoDownloader
from transcriber import Transcriber
from translator import SegmentTranslator
from tts import TTSManager, EdgeTTSProvider
from remixer import Remixer, generate_srt

logger = get_logger("Main")
cancel_requested = False

def signal_handler(sig, frame):
    global cancel_requested
    print("\n[bold red]Cancellation requested... saving state and exiting safely.[/bold red]")
    cancel_requested = True
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def get_video_id(url: str) -> str:
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc:
        qs = parse_qs(parsed.query)
        if 'v' in qs:
            return qs['v'][0]
    elif 'youtu.be' in parsed.netloc:
        return parsed.path.lstrip('/')
    # Fallback to timestamp if not standard YT url
    return f"video_{int(time.time())}"

def main():
    parser = argparse.ArgumentParser(description="Automated Video Dubbing System")
    parser.add_argument("url", help="YouTube URL to dub")
    parser.add_argument("--voice", default=TTS_VOICE, help="Edge-TTS voice (e.g., en-US-AriaNeural)")
    parser.add_argument("--model", default=WHISPER_MODEL, help="Whisper model size (tiny, base, small, medium, large-v3)")
    parser.add_argument("--cpu", action="store_true", help="Force CPU usage for Whisper")
    parser.add_argument("--generate-srt", action="store_true", help="Generate English subtitles")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files after completion")
    args = parser.parse_args()

    if not check_ffmpeg_installed():
        sys.exit(1)

    start_time_total = time.time()
    video_id = get_video_id(args.url)
    
    # Specific output dir for this video
    video_out_dir = OUTPUT_DIR / video_id
    video_out_dir.mkdir(parents=True, exist_ok=True)
    video_temp_dir = TEMP_DIR / video_id
    video_temp_dir.mkdir(parents=True, exist_ok=True)

    state = StateManager(video_out_dir)
    logger.info(f"Starting dubbing process for {args.url} (ID: {video_id})")

    try:
        with DubbingProgress() as progress:
            
            # --- STAGE 1: Download ---
            if not state.is_completed("download"):
                task_id = progress.add_stage("Downloading Video")
                progress.start_stage("Downloading Video")
                downloader = VideoDownloader(video_temp_dir)
                
                t0 = time.time()
                def progress_cb(pct):
                    progress.update_stage("Downloading Video", completed=pct)
                    
                video_path = downloader.download(args.url, progress_cb)
                state.set_timing("download", time.time() - t0)
                state.set_metadata("video_path", str(video_path))
                progress.complete_stage("Downloading Video")
                state.mark_completed("download")
            else:
                video_path = Path(state.get_metadata("video_path"))
                
            # --- STAGE 2: Extract Audio ---
            if not state.is_completed("extract_audio"):
                task_id = progress.add_stage("Extracting Audio")
                progress.start_stage("Extracting Audio")
                downloader = VideoDownloader(video_temp_dir)
                
                t0 = time.time()
                audio_path = downloader.extract_audio(video_path)
                state.set_timing("extract_audio", time.time() - t0)
                state.set_metadata("audio_path", str(audio_path))
                progress.complete_stage("Extracting Audio")
                state.mark_completed("extract_audio")
            else:
                audio_path = Path(state.get_metadata("audio_path"))

            # --- STAGE 3: Transcribe ---
            if not state.is_completed("transcribe"):
                task_id = progress.add_stage("Transcribing")
                progress.start_stage("Transcribing")
                
                t0 = time.time()
                device = "cpu" if args.cpu else "auto"
                transcriber = Transcriber(model_size=args.model, device=device)
                
                lang, conf, segments = transcriber.transcribe(audio_path, video_out_dir)
                
                state.set_timing("transcribe", time.time() - t0)
                state.set_metadata("detected_language", lang)
                state.set_metadata("language_confidence", conf)
                state.set_metadata("segments", segments)
                progress.update_stage("Transcribing", description=f"Transcribing (Detected: {lang})")
                progress.complete_stage("Transcribing")
                state.mark_completed("transcribe")
            else:
                lang = state.get_metadata("detected_language")
                segments = state.get_metadata("segments")

            # --- STAGE 4: Translate ---
            if not state.is_completed("translate"):
                task_id = progress.add_stage("Translating Segments", total=len(segments))
                progress.start_stage("Translating Segments")
                
                t0 = time.time()
                translator = SegmentTranslator(source_lang=lang, target_lang="en")
                translated_segments = translator.translate_segments_parallel(segments)
                
                # Save translated transcript
                trans_text = [f"[{s['start']:.2f} -> {s['end']:.2f}] {s['translated_text']}" for s in translated_segments]
                with open(video_out_dir / "translated_transcript.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(trans_text))
                    
                state.set_timing("translate", time.time() - t0)
                state.set_metadata("segments", translated_segments)
                progress.complete_stage("Translating Segments")
                state.mark_completed("translate")
            else:
                translated_segments = state.get_metadata("segments")
                
            # --- STAGE 5: TTS ---
            if not state.is_completed("tts"):
                task_id = progress.add_stage("Generating Speech Chunks")
                progress.start_stage("Generating Speech Chunks")
                
                t0 = time.time()
                tts_provider = EdgeTTSProvider(default_voice=args.voice)
                tts_manager = TTSManager(provider=tts_provider)
                
                # Create a subfolder for TTS chunks
                tts_dir = video_temp_dir / "tts_chunks"
                tts_dir.mkdir(exist_ok=True)
                
                tts_segments = tts_manager.generate_all(translated_segments, tts_dir)
                
                state.set_timing("tts", time.time() - t0)
                state.set_metadata("segments", tts_segments)
                progress.complete_stage("Generating Speech Chunks")
                state.mark_completed("tts")
            else:
                tts_segments = state.get_metadata("segments")

            # --- STAGE 6: Remixer & SRT ---
            if not state.is_completed("remix"):
                task_id = progress.add_stage("Matching Duration & Merging")
                progress.start_stage("Matching Duration & Merging")
                
                t0 = time.time()
                remixer = Remixer(video_temp_dir)
                merged_audio_path = video_out_dir / "english_audio.mp3"
                remixer.match_durations_and_concat(tts_segments, merged_audio_path)
                
                final_video_path = video_out_dir / f"{video_id}_dubbed.mp4"
                remixer.replace_audio(video_path, merged_audio_path, final_video_path)
                
                if args.generate_srt:
                    generate_srt(tts_segments, video_out_dir / "english_subtitles.srt")
                
                state.set_timing("remix", time.time() - t0)
                state.set_metadata("final_video_path", str(final_video_path))
                progress.complete_stage("Matching Duration & Merging")
                state.mark_completed("remix")

            # --- STAGE 7: Cleanup ---
            if not args.keep_temp:
                task_id = progress.add_stage("Cleaning Files")
                progress.start_stage("Cleaning Files")
                clean_directory(video_temp_dir)
                video_temp_dir.rmdir()
                progress.complete_stage("Cleaning Files")
                
            total_time = time.time() - start_time_total
            state.set_timing("total_execution", total_time)
            
            # Print Final Statistics
            from rich.console import Console
            from rich.table import Table
            c = Console()
            
            c.print("\n[bold green]Dubbing Completed Successfully![/bold green]")
            table = Table(title="Processing Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Detected Language", f"{state.get_metadata('detected_language')} ({state.get_metadata('language_confidence'):.2f})")
            table.add_row("Whisper Model", args.model)
            table.add_row("TTS Voice", args.voice)
            table.add_row("Total Segments", str(len(state.get_metadata('segments', []))))
            
            timings = state.state.get("timings", {})
            table.add_row("Download Time", format_duration(timings.get("download", 0)))
            table.add_row("Transcription Time", format_duration(timings.get("transcribe", 0)))
            table.add_row("Translation Time", format_duration(timings.get("translate", 0)))
            table.add_row("TTS Generation Time", format_duration(timings.get("tts", 0)))
            table.add_row("Merge Time", format_duration(timings.get("remix", 0)))
            table.add_row("Total Execution Time", format_duration(total_time))
            table.add_row("Output Directory", str(video_out_dir.resolve()))
            
            c.print(table)
            
    except Exception as e:
        logger.exception("A fatal error occurred during processing.")
        from rich.console import Console
        c = Console()
        c.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
