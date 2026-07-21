# Automated Video Dubbing System

A completely free, open-source, and locally-run production-quality Python project to download a YouTube video and dub it into English, preserving timestamps, pacing, and video quality.

## Features
- **Downloads highest quality video** using `yt-dlp`
- **Audio Extraction** via `FFmpeg`
- **Transcription & Language Detection** with hardware-accelerated `faster-whisper`
- **Segment-Based Translation** using `argostranslate` to preserve meaning and pacing
- **Natural English TTS** using `edge-tts` (concurrently processed)
- **Audio Synchronization** automatically adjusts timing of the English speech to match the original speaker's pace using FFmpeg `atempo`.
- **Parallel Processing** utilizes `asyncio` and `ThreadPoolExecutor` for high performance.
- **Resume Capability** saves state to `processing.json` to recover from interruptions.
- **Beautiful Terminal UI** with `rich` and `tqdm`.
- **Organized Outputs** generates original and translated transcripts, `.srt` subtitles, merged audio, and the final dubbed `.mp4` into a dedicated folder.

## Architecture

```
[YouTube URL] -> Downloader (yt-dlp) -> Temp Original Video
                   |
                   v
             Extractor (FFmpeg) -> Temp Original Audio (WAV)
                   |
                   v
             Transcriber (faster-whisper) -> Original Transcript + Segments
                   |
                   v
             Translator (argostranslate) -> English Translated Segments
                   |
                   v
             TTS Manager (edge-tts) -> Temp Audio Chunks (MP3)
                   |
                   v
             Remixer (FFmpeg) -> Merged English Audio Track -> Replaced in Final Video
```

## Folder Structure

```
video_dubber/
├── main.py              # CLI entry point and orchestrator
├── config.py            # Environment configurations
├── state_manager.py     # Resume capability and metadata storage
├── downloader.py        # Video/Audio download logic
├── transcriber.py       # Whisper inference
├── translator.py        # Argos translate logic
├── tts.py               # Edge-TTS generation interface
├── remixer.py           # FFmpeg merging and SRT generation
├── progress.py          # Rich terminal UI
├── logger.py            # Event logging
├── utils.py             # Helpers (FFmpeg check, formatting)
├── requirements.txt
├── README.md
├── logs/                # processing.log
├── outputs/             # Output folder (per video ID)
└── temp/                # Temporary processing files
```

## Installation

### 1. Install System Dependencies
**FFmpeg** is required for audio manipulation.
- **Windows**: `winget install ffmpeg` or download from gyan.dev and add to PATH.
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 2. Python Setup
Requires Python 3.10+
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Config (Optional)
Copy `.env.example` to `.env` and modify as needed to adjust models and voices.

## Usage

```bash
python main.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" --generate-srt
```

### CLI Arguments
- `--voice`: Override default Edge-TTS voice (default: `en-US-AriaNeural`).
- `--model`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`).
- `--cpu`: Force CPU inference for Whisper.
- `--generate-srt`: Generate an English `.srt` subtitle file.
- `--keep-temp`: Keep temporary chunks and files instead of cleaning up.

## Limitations & Future Improvements
- **Voice Cloning / Diarization**: Currently uses a single predefined Edge-TTS voice for all speakers. The `TTSProvider` interface is designed so that a true voice cloning engine (like Coqui XTTS) and speaker diarization (like Pyannote) can be plugged in later to map individual speakers to unique cloned voices.
- **Translation Context**: Argos Translate processes segment-by-segment. Sometimes, a sentence split across two segments might lose some context. Using a sliding window translation approach could improve it.
