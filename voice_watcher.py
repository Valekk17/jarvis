import os
import time
import subprocess
import shutil
import sys
import json

sys.path.insert(0, "/root/.openclaw/workspace")

def extract(text):
    """Extract entities via gemini_cli."""
    try:
        res = subprocess.run(["/root/.openclaw/workspace/.venv/bin/python", "/root/.openclaw/workspace/gemini_cli.py", "ext", text], 
                            capture_output=True, text=True, timeout=30)
        output = res.stdout
        # gemini_cli ext prints JSON + summary line. We need JSON only.
        # But gemini_cli prints JSON first?
        # Let's try to find JSON block
        try:
            start = output.find('{')
            end = output.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(output[start:end])
        except:
            pass
        return {}
    except Exception as e:
        print(f"Extraction failed: {e}")
        return {}

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

    # 3. Extract entities → DB + md files (via collector_cron logic implicit in gemini_cli? No, gemini_cli just outputs JSON)
    # Wait, gemini_cli doesn't SAVE entities to graph!
    # I need to save them.
    # I should import append_to_graph from collector_cron? Or just append here?
    # Importing is cleaner.
    
    print(f"  🔍 Extracting entities...")
    try:
        entities = extract(f"Valekk (voice message): {text}")
        counts = {k: len(v) for k, v in entities.items() if isinstance(v, list)}
        print(f"  ✓ Extracted: {counts}")
        
        # Save to graph
        # Reuse collector_cron append_to_graph logic?
        # Or write to memory/context_graph.md directly?
        # Simpler: just append to daily log (already done).
        # But we want GRAPH updates.
        # gemini_cli doesn't update graph.
        
        # We need to save to graph.
        # I will load collector state? No, voice messages don't need dedup against collector state?
        # I'll just append to graph file.
        
        graph_file = "/root/.openclaw/workspace/memory/context_graph.md"
        with open(graph_file, "a") as f:
            for etype, items in entities.items():
                for item in items:
                    # Simple append format
                    content = item.get('content') or f"{item.get('name')}: {item.get('value')}"
                    quote = item.get('source_quote', text)
                    if etype == 'plans':
                        f.write(f"\n- [active] {content} | Quote: \"{quote}\"")
                    elif etype == 'promises':
                        f.write(f"\n- [pending] {content} | From: Me -> To: Chat | Quote: \"{quote}\"")
                    elif etype == 'decisions':
                        f.write(f"\n- {content} | Date: {today} | Quote: \"{quote}\"")
        
        print("  ✓ Saved to graph")

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
                    time.sleep(2)
                    process_audio(filepath)
        except Exception as e:
            print(f"❌ Watcher error: {e}")
        time.sleep(10)

if __name__ == "__main__":
    watch()
