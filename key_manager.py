import json
import os
import time

KEYS_FILE = "/root/.openclaw/workspace/keys.json"

class KeyManager:
    def __init__(self):
        self.keys = self._load_keys()
        self.index = 0
        if not self.keys:
            raise ValueError("No keys found in keys.json")

    def _load_keys(self):
        if not os.path.exists(KEYS_FILE):
            return []
        with open(KEYS_FILE, "r") as f:
            return json.load(f)

    def get_key(self):
        return self.keys[self.index]

    def rotate(self):
        self.index = (self.index + 1) % len(self.keys)
        print(f"Rotating to key index {self.index}...")
        time.sleep(1)
        return self.get_key()
