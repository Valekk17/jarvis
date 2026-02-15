import os
import time
import subprocess
import shutil
import sys

sys.path.insert(0, "/root/.openclaw/workspace")
from jarvis_extractor import extract

INBOUND_DIR = "/root/.openclaw/media/inbound"
ARCHIVE_DIR = "/root/.openclaw/media/archive"

os.makedirs(ARCHIVE_DIR, exist_ok=True)

def process_audio(filepath):
    filename = os.path.basename(filepath)
    print(f"🎤 Processing: {filename}")
    
    # 1. Transcribe with Whisper base
    try:
        result = subprocess.run(
            ["whisper", filepath, "--model", "base", "--output_format", "txt",
             "--output_dir", "/tmp/whisper_out"],
            capture_output=True, text=True, timeout=120
        )
    except Exception as e:
        print(f"  ❌ Whisper error: {e}")
        return

    # Find output file
    base = os.path.splitext(filename)[0]
    txt_file = f"/tmp/whisper_out/{base}.txt"
    if not os.path.exists(txt_file):
        print(f"  ❌ No transcription output")
        return

    with open(txt_file) as f:
        text = f.read().strip()
    
    if not text or len(text) < 5:
        print(f"  ⚠ Empty transcription")
        shutil.move(filepath, os.path.join(ARCHIVE_DIR, filename))
        return

    print(f"  📝 Transcribed: {text[:80]}...")

    # 2. Save to daily log
    today = time.strftime("%Y-%m-%d")
    daily_log = f"/root/.openclaw/workspace/memory/{today}.md"
    os.makedirs(os.path.dirname(daily_log), exist_ok=True)
    with open(daily_log, "a") as f:
        f.write(f"\n## Voice Note ({time.strftime('%H:%M')})\n{text}\n")

    # 3. Extract entities → DB + md files
    print(f"  🔍 Extracting entities...")
    try:
        entities = extract(f"Valekk (voice message): {text}", save=True)
        counts = {k: len(v) for k, v in entities.items() if isinstance(v, list)}
        print(f"  ✓ Extracted: {counts}")
    except Exception as e:
        print(f"  ⚠ Extraction error: {e}")

    # 4. Archive
    shutil.move(filepath, os.path.join(ARCHIVE_DIR, filename))
    print(f"  ✓ Archived: {filename}")

def watch():
    print("🎧 JARVIS Voice Watcher Started")
    print(f"   Watching: {INBOUND_DIR}")
    os.makedirs("/tmp/whisper_out", exist_ok=True)
    
    while True:
        try:
            for filename in os.listdir(INBOUND_DIR):
                if filename.endswith((".ogg", ".mp3", ".wav", ".m4a")):
                    filepath = os.path.join(INBOUND_DIR, filename)
                    # Wait for file to finish writing
                    time.sleep(2)
                    process_audio(filepath)
        except Exception as e:
            print(f"❌ Watcher error: {e}")
        time.sleep(10)

if __name__ == "__main__":
    watch()
