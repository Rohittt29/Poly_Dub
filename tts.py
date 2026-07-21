import asyncio
import edge_tts
from pathlib import Path
from typing import List, Dict
from logger import get_logger

logger = get_logger("TTS")

class TTSProvider:
    """Interface for Text-To-Speech providers to allow future voice-cloning extensions."""
    async def generate_audio(self, text: str, output_path: Path, speaker_id: str = None) -> bool:
        raise NotImplementedError

class EdgeTTSProvider(TTSProvider):
    def __init__(self, default_voice: str = "en-US-AriaNeural"):
        self.default_voice = default_voice
        # Here we could map speaker IDs to different Edge-TTS voices
        self.speaker_voice_map = {}

    def get_voice_for_speaker(self, speaker_id: str) -> str:
        return self.speaker_voice_map.get(speaker_id, self.default_voice)

    async def generate_audio(self, text: str, output_path: Path, speaker_id: str = None) -> bool:
        voice = self.get_voice_for_speaker(speaker_id)
        communicate = edge_tts.Communicate(text, voice)
        try:
            await communicate.save(str(output_path))
            return True
        except Exception as e:
            logger.error(f"Edge-TTS failed to generate audio for text '{text}': {e}")
            return False

class TTSManager:
    def __init__(self, provider: TTSProvider):
        self.provider = provider

    async def _generate_segment_async(self, segment: Dict, output_dir: Path) -> Path:
        """Generates TTS for a single segment and returns the path."""
        # Clean text
        text = segment.get("translated_text", "").strip()
        if not text:
            # Fallback to silence or empty if no text
            return None
            
        segment_idx = segment.get("id", 0)
        output_path = output_dir / f"chunk_{segment_idx:04d}.mp3"
        
        # Optional: check if exists to resume
        if output_path.exists() and output_path.stat().st_size > 0:
            segment["audio_chunk"] = str(output_path)
            return output_path

        # Generate audio
        success = await self.provider.generate_audio(text, output_path)
        if success:
            segment["audio_chunk"] = str(output_path)
            return output_path
        return None

    async def generate_all_async(self, segments: List[Dict], output_dir: Path) -> List[Dict]:
        """Generates TTS for all segments concurrently."""
        tasks = [self._generate_segment_async(seg, output_dir) for seg in segments]
        await asyncio.gather(*tasks)
        return segments

    def generate_all(self, segments: List[Dict], output_dir: Path) -> List[Dict]:
        """Synchronous wrapper for concurrent TTS generation."""
        return asyncio.run(self.generate_all_async(segments, output_dir))
