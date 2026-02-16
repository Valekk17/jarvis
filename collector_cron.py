#!/usr/bin/env python3
"""
JARVIS Auto-Collector v3
Reads Telegram messages → Gemini extraction → Graph
+ Romance Mode: Detects "I love you" from Wife and replies.
"""
import subprocess
import json
import os
import sys
import hashlib
import time
import random
from datetime import date, datetime

# Config
JARVIS_DIR = "/root/.openclaw/workspace/memory"
STATE_FILE = os.path.join(JARVIS_DIR, "collector_state.json")
GRAPH_FILE = os.path.join(JARVIS_DIR, "context_graph.md")
TODAY = date.today().isoformat()

# Personal chats to monitor
CHATS = [
    ("Мой Мир❤️", 50),
    ("Леха Косенко", 50),
    ("Андрейка Братик", 50),
    ("Мамуля", 50)
]

WIFE_CHAT = "Мой Мир❤️"
LOVE_KEYWORDS = ["люблю", "love", "обожаю", "скучаю"]
LOVE_REPLIES = [
    "Я тоже тебя очень сильно люблю! ❤️ Ты — мое счастье!",
    "И я тебя люблю безумно! ❤️ Ты самая лучшая жена!",
    "Обожаю тебя, родная! ❤️ Скучаю по тебе!",
    "Люблю тебя больше всего на свете! ❤️ Ты делаешь меня счастливым!",
    "Сильно-сильно люблю тебя! ❤️ Обнимаю крепко!",
    "И я тебя люблю, солнышко! ❤️",
    "Я тоже тебя люблю! ❤️ Ты мой мир."
]

# Gemini
try:
    from google import genai
    from google.genai import types
    USE_NEW_API = True
except ImportError:
    import google.generativeai as genai
    USE_NEW_API = False

sys.path.insert(0, "/root/.openclaw/workspace")
from key_manager import KeyManager

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_run": None, "processed_chats": {}, "seen_hashes": [], "last_msg_ids": {}, "last_love_reply": 0}

def save_state(state):
    state["last_run"] = datetime.now().isoformat()
    state["seen_hashes"] = state.get("seen_hashes", [])[-1000:]
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def content_hash(text):
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

def read_chat_raw(chat_name, limit=50):
    """Read chat and return raw messages list."""
    try:
        res = subprocess.run(["tg", "read", chat_name, "-n", str(limit), "--json"],
                            capture_output=True, text=True, timeout=30)
        output = res.stdout
        start = output.find('{')
        end = output.rfind('}') + 1
        if start == -1 or end == 0:
            return []
        data = json.loads(output[start:end])
        return data.get('messages', [])
    except Exception as e:
        print(f"  ❌ Read error: {e}")
        return []

def send_message(chat_name, text):
    """Send message via tg CLI."""
    print(f"  💌 Sending to {chat_name}: {text}")
    try:
        subprocess.run(["tg", "send", chat_name, text], check=True, timeout=30)
        return True
    except Exception as e:
        print(f"  ❌ Send error: {e}")
        return False

def extract_with_gemini(text, chat_name):
    """Extract entities using Gemini."""
    manager = KeyManager()
    
    # Load known actors from GRAPH_FILE
    actors_file = GRAPH_FILE
    known_actors = []
    if os.path.exists(actors_file):
        with open(actors_file) as f:
            for line in f:
                if line.strip().startswith("- **") and "Role:" in line:
                    parts = line.split("**")
                    if len(parts) >= 3:
                        known_actors.append(parts[1])

    prompt = f"""You are JARVIS entity extractor. Current date: {TODAY}. Chat: {chat_name}.

RULES:
1. Anti-Noise: Ignore greetings, small talk, pure emotions, and STATUS updates ("I am ready", "I am here").
2. **Implicit Tasks**: Only if specific.
   - "Order arrived" -> Plan: "Pick up order" (Specific).
   - "I am ready" -> IGNORE (Status).
   - "We will solve it" -> IGNORE (Vague).
3. **Specificity**: Do NOT extract tasks with missing objects ("Do it", "Solve problem", "Show").
4. **Principles vs Tasks**: Concrete -> PLAN, Abstract -> DECISION.
5. **Relations**: Identify relationships between Actors and Entities.
   - "Arisha promised Valekk" -> relation: "PROMISED", target: "Valekk"
   - "Valekk decided to go" -> relation: "DECIDED", actor: "Valekk"

OUTPUT JSON:
{{
  "promises": [{{"from":"Name","to":"Name","content":"what","deadline":"date","status":"pending","confidence":0.9,"source_quote":"text"}}],
  "decisions": [{{"actor":"Name","content":"what","date":"date","confidence":0.9,"source_quote":"text"}}],
  "metrics": [{{"actor":"Name","name":"metric","value":123,"unit":"unit","confidence":0.9,"source_quote":"text"}}],
  "plans": [{{"actor":"Name","content":"goal","status":"active","confidence":0.9,"source_quote":"text"}}]
}}

TEXT:
"{text[:6000]}"
"""

    max_retries = 10
    model_name = "gemini-2.5-pro"
    
    for attempt in range(max_retries):
        key = manager.get_key()
        try:
            if USE_NEW_API:
                client = genai.Client(api_key=key)
                config = types.GenerateContentConfig(temperature=0.1)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                return response.text
            else:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                manager.rotate()
                if attempt > 2: model_name = "gemini-2.5-flash"
                continue
            return None
    return None

def parse_json(text):
    if not text: return None
    text = text.strip()
    if text.startswith("```"): text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"): text = text.rsplit("```", 1)[0]
    try: return json.loads(text.strip())
    except: return None

def append_to_graph(data, state):
    seen = set(state.get("seen_hashes", []))
    existing = ""
    if os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE) as f: existing = f.read()
    
    new_lines = []
    saved = 0
    
    for entity_type in ["promises", "decisions", "metrics", "plans"]:
        items = data.get(entity_type, [])
        for item in items:
            if entity_type == "metrics":
                content_str = f"{item.get('name','')}: {item.get('value','')}"
            else:
                content_str = item.get('content', '')
            
            h = content_hash(content_str)
            if h in seen: continue
            seen.add(h)
            
            quote = item.get('source_quote', '')
            
            if entity_type == "promises":
                line = f"- [pending] {content_str} | From: {item.get('from','')} -> {item.get('to','')} | Deadline: {item.get('deadline','none')} | Quote: \"{quote}\""
            elif entity_type == "decisions":
                line = f"- {content_str} | Actor: {item.get('actor','Valekk_17')} | Date: {item.get('date', TODAY)} | Quote: \"{quote}\""
            elif entity_type == "metrics":
                line = f"- **{item.get('name','')}**: {item.get('value','')} {item.get('unit','')} | Actor: {item.get('actor','Valekk_17')} | Quote: \"{quote}\""
            elif entity_type == "plans":
                line = f"- [{item.get('status','active')}] {content_str} | Actor: {item.get('actor','Valekk_17')} | Target: {item.get('target_date','none')} | Quote: \"{quote}\""
            
            new_lines.append((entity_type, line))
            saved += 1
    
    # Append
    if new_lines:
        with open(GRAPH_FILE, "a") as f:
            f.write("\n" + "\n".join([line for _, line in new_lines]))
            
    state["seen_hashes"] = list(seen)
    return saved

def archive_completed():
    """Move completed tasks to archive."""
    if not os.path.exists(GRAPH_FILE): return False
    with open(GRAPH_FILE) as f: lines = f.readlines()
    
    active_lines = []
    archive_lines = []
    
    for line in lines:
        if "- [completed]" in line or "- [done]" in line:
            archive_lines.append(line)
        else:
            active_lines.append(line)
            
    if archive_lines:
        with open(GRAPH_FILE, "w") as f:
            f.writelines(active_lines)
            
        archive_file = os.path.join(JARVIS_DIR, "archive_tasks.md")
        with open(archive_file, "a") as f:
            f.write(f"\n## Archive {datetime.now().isoformat()}\n")
            f.writelines(archive_lines)
            
        print(f"  📦 Archived {len(archive_lines)} completed tasks")
        return True
    return False

def get_unique_reply(state):
    """Get a love reply different from the last one."""
    last_msg = state.get("last_love_message", "")
    available = [m for m in LOVE_REPLIES if m != last_msg]
    if not available: available = LOVE_REPLIES 
    reply = random.choice(available)
    state["last_love_message"] = reply
    return reply

def git_push():
    """Sync to GitHub."""
    try:
        status = subprocess.run(["git", "status", "--porcelain"], cwd=JARVIS_DIR, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "add", "."], cwd=JARVIS_DIR, check=True)
            subprocess.run(["git", "commit", "-m", f"Auto-update {datetime.now().strftime('%Y-%m-%d %H:%M')}"], 
                           cwd=JARVIS_DIR, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "push"], cwd=JARVIS_DIR, check=True)
        print("  ☁️ Git Sync: Pushed to GitHub")
    except Exception as e:
        print(f"  ❌ Git Sync failed: {e}")

def main():
    state = load_state()
    print(f"🚀 JARVIS Collector v3 (Romance) | {datetime.now().isoformat()}")
    
    last_ids = state.get("last_msg_ids", {})
    total_saved = 0
    
    for chat_name, limit in CHATS:
        print(f"\n📥 {chat_name}")
        messages = read_chat_raw(chat_name, limit)
        if not messages:
            print("  No messages")
            continue
            
        # Filter new messages (id > last_id)
        last_id = last_ids.get(chat_name, 0)
        new_msgs = [m for m in messages if m['id'] > last_id]
        
        if not new_msgs:
            print("  No new messages")
            continue
            
        print(f"  {len(new_msgs)} new messages")
        
        # Prepare text for graph extraction
        text_lines = []
        for m in new_msgs:
            is_out = m.get('isOutgoing', False)
            sender = "Valekk_17" if is_out else chat_name.split('@')[0].strip()
            text = m.get('text', '')
            if text:
                text_lines.append(f"{sender}: {text}")
                
            # Romance Logic (Wife Only)
            if chat_name == WIFE_CHAT and not is_out and text:
                text_lower = text.lower()
                if any(k in text_lower for k in LOVE_KEYWORDS):
                    # Check cooldown (don't spam reply every minute)
                    now = time.time()
                    last_reply = state.get("last_love_reply", 0)
                    if now - last_reply > 3600: # 1 hour cooldown
                        print("  ❤️ Love detected! Sending reply...")
                        reply = get_unique_reply(state)
                        
                        if send_message(chat_name, reply):
                            state["last_love_reply"] = now
                    else:
                        print("  ❤️ Love detected (cooldown)")

            # Find last outgoing LOVE message time
            last_out_love_ts = 0
            for m in messages:
                if m.get('isOutgoing'):
                    text_out = m.get('text', '').lower()
                    if any(k in text_out for k in LOVE_KEYWORDS):
                        try:
                            dt = datetime.fromisoformat(m['date'].replace('Z', '+00:00'))
                            ts = dt.timestamp()
                            if ts > last_out_love_ts:
                                last_out_love_ts = ts
                        except: pass
            
            # Fallback
            now = time.time()
            last_reply = state.get("last_love_reply", 0)
            
            hours_since_last_love = (now - last_out_love_ts) / 3600
            hours_since_auto_reply = (now - last_reply) / 3600
            current_hour = datetime.now().hour
            
            # If silent (no love) > 6h, daytime (9-22), and didn't auto-reply recently
            if hours_since_last_love > 6 and 9 <= current_hour <= 22 and hours_since_auto_reply > 6:
                print(f"  ❤️ Proactive Love! Last love: {hours_since_last_love:.1f}h ago")
                reply = get_unique_reply(state)
                if send_message(chat_name, reply):
                    state["last_love_reply"] = now

        # Update last_id
        last_ids[chat_name] = max([m['id'] for m in new_msgs])
        
        # Graph Extraction
        full_text = "\n".join(text_lines)
        if len(full_text) > 10:
            print("  Extracting entities...")
            result = extract_with_gemini(full_text, chat_name)
            data = parse_json(result)
            if data:
                saved = append_to_graph(data, state)
                print(f"  ✓ Saved {saved} entities")
                total_saved += saved
    
    state["last_msg_ids"] = last_ids
    save_state(state)
    
    # Archive completed tasks
    archived = archive_completed()
    
    if total_saved > 0 or archived:
        print("🎨 Regenerating D3 graph...")
        try:
            subprocess.run(["python3", "/root/.openclaw/workspace/generate_canvas.py"], 
                          stdout=open("/root/.openclaw/workspace/graph.html", "w"))
        except: pass

    git_push()

if __name__ == "__main__":
    main()
