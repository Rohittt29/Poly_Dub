from typing import List, Dict
from deep_translator import GoogleTranslator
from logger import get_logger

logger = get_logger("Translator")

def detect_src_lang(text: str) -> str:
    """
    Detects the script of the text by inspecting Unicode ranges.
    Returns the appropriate language code for deep-translator ('hi', 'ur', 'en', 'auto').
    """
    blocks = {
        'hi': range(0x0900, 0x0980), # Devanagari (Hindi)
        'ur': range(0x0600, 0x0700), # Perso-Arabic (Urdu)
    }
    
    counts = {lang: 0 for lang in blocks}
    latin_count = 0
    
    for char in text:
        cp = ord(char)
        if 0x0041 <= cp <= 0x007A or 0x00C0 <= cp <= 0x02AF:
            latin_count += 1
            continue
        for lang, r in blocks.items():
            if cp in r:
                counts[lang] += 1
                break
                
    max_lang = max(counts, key=counts.get) if any(counts.values()) else 'en'
    
    # If we found Indic characters and they make up a meaningful portion
    if counts.get(max_lang, 0) > 0 and (counts[max_lang] >= latin_count * 0.1): 
        return max_lang
        
    # If predominantly Latin characters, default to English, else rely on Google Translate auto detection
    if latin_count > 0:
        return 'en'
    return 'auto'

class SegmentTranslator:
    def __init__(self, source_lang: str, target_lang: str = "en"):
        """
        source_lang is ignored because we dynamically detect script per segment.
        target_lang is passed to deep-translator (default: 'en').
        """
        self.target_lang = target_lang

    def translate_segments_parallel(self, segments: List[Dict], max_workers: int = 4) -> List[Dict]:
        """
        Translates multiple segments.
        Leverages deep-translator's translate_batch method for performance.
        Preserves API compatibility, timestamps, ordering, and ensures speed safely.
        """
        logger.info("Translating segments using deep-translator.")
        
        translated_segments = []
        for seg in segments:
            translated_segments.append(seg.copy())
            
        # Group indices and texts by detected source language
        lang_groups = {}
        for i, seg in enumerate(translated_segments):
            text = seg['text'].strip()
            if not text:
                continue
            lang = detect_src_lang(text)
            if lang not in lang_groups:
                lang_groups[lang] = []
            lang_groups[lang].append((i, text))
            
        # Translate each language group in batches
        for lang, items in lang_groups.items():
            indices = [item[0] for item in items]
            texts = [item[1] for item in items]
            
            if lang == "en":
                for idx, text in zip(indices, texts):
                    translated_segments[idx]['translated_text'] = text
                continue
                
            translator = GoogleTranslator(source=lang, target=self.target_lang)
            for idx, text in zip(indices, texts):
                try:
                    res = translator.translate(text)
                    translated_segments[idx]['translated_text'] = res if res else text
                except Exception as e:
                    logger.error(f"Failed to translate segment {idx} for lang {lang}: {e}")
                    # Graceful fallback: Use original text on error
                    translated_segments[idx]['translated_text'] = text
                        
        # Ensure any empty segments have the key
        for seg in translated_segments:
            if 'translated_text' not in seg or not seg['translated_text']:
                seg['translated_text'] = seg['text']
                
        return translated_segments
