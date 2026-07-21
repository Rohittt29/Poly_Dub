import json
from pathlib import Path
from typing import Dict, Any

class StateManager:
    """
    Manages the processing state of a video to allow resuming capability
    and storing metadata statistics.
    """
    def __init__(self, output_dir: Path):
        self.state_file = output_dir / "processing.json"
        self.state: Dict[str, Any] = {
            "stages": {
                "download": "pending",
                "extract_audio": "pending",
                "transcribe": "pending",
                "translate": "pending",
                "tts": "pending",
                "remix": "pending",
                "cleanup": "pending"
            },
            "metadata": {},
            "timings": {}
        }
        self.load_state()

    def load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge loaded state carefully
                    if "stages" in loaded:
                        self.state["stages"].update(loaded["stages"])
                    if "metadata" in loaded:
                        self.state["metadata"].update(loaded["metadata"])
                    if "timings" in loaded:
                        self.state["timings"].update(loaded["timings"])
            except Exception:
                pass # Corrupt state file, start fresh

    def save_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4)

    def is_completed(self, stage: str) -> bool:
        return self.state["stages"].get(stage) == "completed"

    def mark_completed(self, stage: str):
        self.state["stages"][stage] = "completed"
        self.save_state()

    def set_metadata(self, key: str, value: Any):
        self.state["metadata"][key] = value
        self.save_state()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.state["metadata"].get(key, default)

    def set_timing(self, key: str, value: float):
        self.state["timings"][key] = value
        self.save_state()
