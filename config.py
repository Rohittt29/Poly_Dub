import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "outputs")
TEMP_DIR = BASE_DIR / os.getenv("TEMP_DIR", "temp")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")

# Whisper Configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
# 'auto' means we'll check for CUDA, otherwise CPU
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")

# TTS Configuration
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-AriaNeural")

# Download/Quality Configuration
VIDEO_QUALITY = os.getenv("VIDEO_QUALITY", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best")
AUDIO_BITRATE = os.getenv("AUDIO_BITRATE", "192k")

# Ensure required directories exist
def init_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

init_directories()
