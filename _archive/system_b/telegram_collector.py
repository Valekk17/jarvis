import json
import subprocess
import os
import re
import time
from datetime import datetime
from event_logger import get_event_logger

INBOX_DIR = "/root/.openclaw/workspace/cybos_data/inbox"
STATE_FILE = "telegram_state.json"

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

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def collect():
    if not os.path.exists(INBOX_DIR): os.makedirs(INBOX_DIR)
    
    # Use absolute path for events.jsonl
    events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'events.jsonl')
    logger = get_event_logger({
        'events_file_path': events_path
    })
    state = load_state()

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
        
        chat_id = str(chat.get('id', 'unknown'))
        last_seen_id = state.get(chat_id, 0)
        max_id_in_batch = last_seen_id

        print(f"[{i+1}/{len(chats)}] Processing: {name} (last_id: {last_seen_id})")
        
        try:
            # Poll 50 messages
            res = subprocess.run(["tg", "read", name, "-n", "50", "--json"], capture_output=True, text=True)
            data = parse_json_output(res.stdout)
            if not data: continue
            
            if isinstance(data, list):
                messages = data
            else:
                messages = data.get('messages', [])
        except Exception as e:
            print(f"Error reading chat {name}: {e}")
            continue
            
        if not messages: continue
        
        # Sort messages by ID (oldest first) to process individually
        # tg-cli messages usually have 'id' field
        messages.sort(key=lambda x: x.get('id', 0))

        # Save as Markdown (full update)
        filename = os.path.join(INBOX_DIR, f"telegram_{chat_id}.md")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Chat: {name}\n")
                f.write(f"Source: Telegram\n")
                f.write(f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for m in messages:
                    msg_id = m.get('id', 0)
                    sender = m.get('sender', 'Unknown')
                    text = m.get('text') or m.get('message') or '[Media]'
                    date = m.get('date', '')
                    
                    f.write(f"**{sender}** ({date}): {text}\n\n")
                    
                    # LOG NEW EVENTS
                    if msg_id > last_seen_id:
                        # Log event
                        event_type = 'user_message' if sender != 'Jarvis' else 'agent_response' # Approximation
                        logger.log({
                            "source": "telegram",
                            "action": event_type,
                            "actor": "user" if sender != "Jarvis" else "agent", 
                            "content_hash": logger.hash_content(text),
                            "entities": [name], # associate with chat name
                            "metadata": {
                                "chat_id": chat_id,
                                "msg_id": msg_id,
                                "sender": sender,
                                "date": date
                            }
                        })
                        max_id_in_batch = max(max_id_in_batch, msg_id)
        
        except Exception as e:
            print(f"Error saving chat {name}: {e}")

        # Update state with max ID seen
        state[chat_id] = max_id_in_batch
        
    save_state(state)
    print("Done.")

if __name__ == "__main__":
    collect()
