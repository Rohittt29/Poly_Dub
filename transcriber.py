import json
from pathlib import Path
from typing import Dict, Any, Tuple
from faster_whisper import WhisperModel
import torch
from logger import get_logger

logger = get_logger("Transcriber")

class Transcriber:
    def __init__(self, model_size: str, device: str = "auto"):
        self.model_size = model_size
        
        # Hardware detection
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        logger.info(f"Initializing Whisper model '{self.model_size}' on device '{self.device}' with compute type '{self.compute_type}'")
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def transcribe(self, audio_path: Path, output_dir: Path) -> Tuple[str, float, list]:
        """
        Transcribes the audio file and saves the segments.
        Returns a tuple of (detected_language, confidence, segments).
        """
        logger.info(f"Starting transcription for {audio_path.name}")
        
        # We use word_timestamps=True if we want very precise timings, 
        # but standard segment timestamps are usually sufficient for dubbing.
        segments_gen, info = self.model.transcribe(str(audio_path), beam_size=5)
        
        lang = info.language
        confidence = info.language_probability
        
        segments = []
        transcript_text = []
        
        for segment in segments_gen:
            seg_data = {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            segments.append(seg_data)
            transcript_text.append(f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text.strip()}")
            
        # Save original transcript
        transcript_path = output_dir / "original_transcript.txt"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(transcript_text))
            
        # Save structured segments for easy loading
        segments_path = output_dir / "segments.json"
        with open(segments_path, 'w', encoding='utf-8') as f:
            json.dump({"language": lang, "confidence": confidence, "segments": segments}, f, indent=4)
            
        logger.info(f"Transcription complete. Detected {lang} ({confidence:.2f}). {len(segments)} segments.")
        return lang, confidence, segments
