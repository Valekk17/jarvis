import json
import hashlib
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class EventLogger:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Use workspace directory by default if not specified
        self.events_file_path = self.config.get(
            'events_file_path', 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'events.jsonl')
        )
        self.max_age_days = self.config.get('max_age_days', 30)
        self.hash_algorithm = self.config.get('hash_algorithm', 'sha256')
        self.exclude_raw_text = self.config.get('exclude_raw_text', True)
        self.event_counter = 0
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.events_file_path), exist_ok=True)

    def log(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log an event to the events.jsonl file.
        event_data should contain: source, action, actor, entities, etc.
        """
        full_event = {
            "id": self._generate_event_id(),
            "ts": datetime.utcnow().isoformat() + "Z",
            **event_data
        }
        
        try:
            with open(self.events_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(full_event, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[EventLogger] Error writing event: {e}")
            
        return full_event

    def hash_content(self, text: str) -> str:
        """Hash content for privacy."""
        if not text:
            return ""
        h = hashlib.new(self.hash_algorithm)
        h.update(text.encode('utf-8'))
        return f"{self.hash_algorithm}:{h.hexdigest()[:16]}"

    def _generate_event_id(self) -> str:
        date_str = datetime.utcnow().strftime('%Y%m%d')
        self.event_counter = (self.event_counter + 1) % 10000
        # Add random component to avoid collision in multiprocess
        import random
        rand_suffix = random.randint(1000, 9999)
        return f"evt_{date_str}_{self.event_counter:04d}_{rand_suffix}"

# Singleton instance
_logger = None

def get_event_logger(config=None):
    global _logger
    if _logger is None:
        _logger = EventLogger(config)
    return _logger
