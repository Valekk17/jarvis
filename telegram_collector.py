import json
import subprocess
import os
import re
import time

INBOX_DIR = "/root/.openclaw/workspace/cybos_data/inbox"

def parse_json_output(output):
    try:
        # Remove ANSI codes
        clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', output)
        
        # Regex for JSON Array: [ followed by { or ] (empty)
        match_arr = re.search(r'\[\s*(?:\{|\])', clean)
        # Regex for JSON Object: { followed by "
        match_obj = re.search(r'\{\s*"', clean)
        
        start = -1
        if match_arr and (not match_obj or match_arr.start() < match_obj.start()):
            start = match_arr.start()
        elif match_obj:
            start = match_obj.start()
            
        if start != -1:
            dec = json.JSONDecoder()
            obj, _ = dec.raw_decode(clean[start:])
            return obj
            
    except Exception as e:
        print(f"JSON Parse Error: {e}")
    return None

def collect():
    if not os.path.exists(INBOX_DIR): os.makedirs(INBOX_DIR)
    
    # Always refresh chats
    if os.path.exists("chats.json"): os.remove("chats.json")
    subprocess.run("tg chats --json > chats.json", shell=True)

    with open("chats.json", "r") as f:
        chats = parse_json_output(f.read()) or []

    print(f"Collecting from {len(chats)} chats...")
    
    for i, chat in enumerate(chats):
        name = chat.get('name') or chat.get('title')
        if not name: continue
        if chat.get('type') != 'user': continue
        
        print(f"[{i+1}/{len(chats)}] Downloading: {name}")
        
        try:
            res = subprocess.run(["tg", "read", name, "-n", "50", "--json"], capture_output=True, text=True)
            data = parse_json_output(res.stdout)
            if not data: continue
            
            if isinstance(data, list):
                messages = data
            else:
                messages = data.get('messages', [])
        except: continue
            
        if not messages: continue
        
        # Save as Markdown
        chat_id = chat.get('id', 'unknown')
        filename = os.path.join(INBOX_DIR, f"telegram_{chat_id}.md")
        
        with open(filename, "w") as f:
            f.write(f"# Chat: {name}\n")
            f.write(f"Source: Telegram\n")
            f.write(f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for m in reversed(messages): # Oldest first
                sender = m.get('sender', 'Unknown')
                text = m.get('text') or m.get('message') or '[Media]'
                date = m.get('date', '')
                f.write(f"**{sender}** ({date}): {text}\n\n")
                
        print(f"  Saved to {filename}")

if __name__ == "__main__":
    collect()
