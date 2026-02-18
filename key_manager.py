import json
import os
import time

KEYS_FILE = "/root/.openclaw/workspace/keys.json"
STATE_FILE = "/root/.openclaw/workspace/key_manager_state.json"

class KeyManager:
    def __init__(self):
        self.keys = self._load_keys()
        self.index = self._load_state()
        if not self.keys:
            raise ValueError("No keys found in keys.json")

    def _load_keys(self):
        if not os.path.exists(KEYS_FILE):
            return []
        with open(KEYS_FILE, "r") as f:
            return json.load(f)

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                    return state.get("index", 0) % len(self.keys)
            except:
                pass
        return 0

    def _save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump({"index": self.index}, f)

    def get_key(self):
        return self.keys[self.index]

    def rotate(self):
        self.index = (self.index + 1) % len(self.keys)
        self._save_state()
        print(f"Rotating to key index {self.index}...")
        time.sleep(1)
        return self.get_key()
