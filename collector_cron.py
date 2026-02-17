#!/usr/bin/env python3
"""
JARVIS Auto-Collector v4.1
Reads Telegram messages → Gemini extraction → Graph
+ Romance Mode
+ Morning Greetings
+ Sync
+ Live Dashboard (via API)
+ Smart Notifications (Deadlines)
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
DASHBOARD_CHAT_ID = "1700440705"
DASHBOARD_MSG_ID = 1230
API_TOKEN = "6b9b90cc1d18c70e6741594c6c07e15526fb740fb213b3c8"

# Personal chats to monitor
CHATS = [
    ("Мой Мир❤️", 50),
    ("Леха Косенко", 50),
    ("Андрейка Братик", 50),
    ("Мамуля", 50)
]

WIFE_CHAT = "Мой Мир❤️"
MOM_CHAT = "Мамуля"

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

MORNING_GREETINGS = [
    "Доброе утро, мамуля! ❤️ Я тебя люблю!",
    "С добрым утром! ❤️ Люблю тебя, хорошего дня!",
    "Мамулечка, доброе утро! ❤️ Я тебя люблю!",
    "Доброе утро! ❤️ Как настроение? Люблю!",
    "Привет, мамуля! ❤️ Доброе утро! Люблю тебя!"
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
    return {"last_run": None, "processed_chats": {}, "seen_hashes": [], "last_msg_ids": {}, "last_love_reply": 0, "last_morning_greet_mom": ""}

def save_state(state):
    state["last_run"] = datetime.now().isoformat()
    state["seen_hashes"] = state.get("seen_hashes", [])[-1000:]
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def content_hash(text):
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

def read_chat_raw(chat_name, limit=50):
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
    print(f"  💌 Sending to {chat_name}: {text}")
    try:
        subprocess.run(["tg", "send", chat_name, text], check=True, timeout=30)
        return True
    except Exception as e:
        print(f"  ❌ Send error: {e}")
        return False

def update_dashboard():
    """Update pinned dashboard message via API."""
    try:
        # Read Tasks
        tasks = []
        day_file = os.path.join(JARVIS_DIR, "Tasks/Day.md")
        if os.path.exists(day_file):
            with open(day_file) as f:
                for line in f:
                    if line.strip().startswith("- [ ]"):
                        tasks.append(line.strip()[5:].strip())
        
        # Read Metrics
        metrics = []
        if os.path.exists(GRAPH_FILE):
            with open(GRAPH_FILE) as f:
                for line in f:
                    if "**pregnancy_start_date**" in line:
                        # Calc days
                        try:
                            val = line.split("**:")[1].split("|")[0].strip()
                            start_date = datetime.strptime(val, "%Y-%m-%d").date()
                            days = (date.today() - start_date).days
                            weeks = days // 7
                            days_rem = days % 7
                            metrics.append(f"Беременность: {days} дн. ({weeks} нед. {days_rem} дн.)")
                        except: pass
                    elif "**Pregnancy**" in line: 
                         metrics.append(line.split("|")[0].strip().replace("- ", ""))
                         
        # Compose Text
        text = f"📊 **JARVIS Live Dashboard**\n━━━━━━━━━━━━━━━━━━\n\n📅 **Сегодня ({datetime.now().strftime('%d.%m')}):**\n"
        if tasks:
            for t in tasks[:5]:
                text += f"▫️ {t}\n"
            if len(tasks) > 5:
                text += f"... и еще {len(tasks)-5}\n"
        else:
            text += "✅ Задач нет\n"
            
        if metrics:
            text += "\n📈 **Метрики:**\n"
            for m in metrics:
                text += f"▫️ {m}\n"
        
        text += f"\n🔄 *Обновлено: {datetime.now().strftime('%H:%M')}*"
        
        # Call API
        payload = {
            "tool": "message",
            "action": "edit",
            "args": {
                "messageId": str(DASHBOARD_MSG_ID),
                "chatId": DASHBOARD_CHAT_ID,
                "message": text
            }
        }
        
        subprocess.run([
            "curl", "-s", "-X", "POST",
            "-H", f"Authorization: Bearer {API_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
            "http://127.0.0.1:18789/tools/invoke"
        ], stdout=subprocess.DEVNULL)
        print("  📊 Dashboard updated")

    except Exception as e:
        print(f"Dashboard update failed: {e}")

def check_deadlines(state):
    if not os.path.exists(GRAPH_FILE): return
    with open(GRAPH_FILE) as f: lines = f.readlines()
    notified = set(state.get("notified_tasks", []))
    new_notified = set()
    today_str = date.today().isoformat()
    for line in lines:
        if "[active]" in line and "Target:" in line:
            try:
                target_part = line.split("Target:")[1].split("|")[0].strip()
                if len(target_part) == 10:
                    task_content = line.split("|")[0].replace("- [active]", "").strip()
                    task_hash = content_hash(task_content)
                    if task_hash in notified:
                        new_notified.add(task_hash)
                        continue
                    if target_part == today_str:
                        subprocess.run(["tg", "send", "me", f"🔔 **Дедлайн сегодня:**\n{task_content}"])
                        new_notified.add(task_hash)
            except: pass
    state["notified_tasks"] = list(new_notified)

def extract_with_gemini(text, chat_name):
    manager = KeyManager()
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
1. Anti-Noise: Ignore greetings, small talk, STATUS.
2. Implicit Tasks: Specific only.
3. Specificity: No vague tasks.
4. Relevance: Ignore others' plans.
5. Relations: Identify.
OUTPUT JSON:
{{ "promises": [], "decisions": [], "metrics": [], "plans": [] }}
TEXT: "{text[:6000]}"
"""
    max_retries = 10
    model_name = "gemini-2.5-pro"
    for attempt in range(max_retries):
        key = manager.get_key()
        try:
            if USE_NEW_API:
                client = genai.Client(api_key=key)
                config = types.GenerateContentConfig(temperature=0.1)
                response = client.models.generate_content(model=model_name, contents=prompt, config=config)
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
            content_str = item.get('content', '') if entity_type != 'metrics' else f"{item.get('name')}: {item.get('value')}"
            h = content_hash(content_str)
            if h in seen: continue
            seen.add(h)
            quote = item.get('source_quote', '')
            if entity_type == "promises": line = f"- [pending] {content_str} | From: {item.get('from','')} -> {item.get('to','')} | Deadline: {item.get('deadline','none')} | Quote: \"{quote}\""
            elif entity_type == "decisions": line = f"- {content_str} | Actor: {item.get('actor','Valekk_17')} | Date: {item.get('date', TODAY)} | Quote: \"{quote}\""
            elif entity_type == "metrics": line = f"- **{item.get('name','')}**: {item.get('value','')} {item.get('unit','')} | Actor: {item.get('actor','Valekk_17')} | Quote: \"{quote}\""
            elif entity_type == "plans": line = f"- [{item.get('status','active')}] {content_str} | Actor: {item.get('actor','Valekk_17')} | Target: {item.get('target_date','none')} | Quote: \"{quote}\""
            new_lines.append((entity_type, line))
            saved += 1
    if new_lines:
        with open(GRAPH_FILE, "a") as f: f.write("\n" + "\n".join([line for _, line in new_lines]))
    state["seen_hashes"] = list(seen)
    return saved

def archive_completed():
    if not os.path.exists(GRAPH_FILE): return False
    with open(GRAPH_FILE) as f: lines = f.readlines()
    active_lines = []
    archive_lines = []
    for line in lines:
        if "- [completed]" in line or "- [done]" in line: archive_lines.append(line)
        else: active_lines.append(line)
    if archive_lines:
        with open(GRAPH_FILE, "w") as f: f.writelines(active_lines)
        archive_dir = os.path.join(JARVIS_DIR, ".archive")
        os.makedirs(archive_dir, exist_ok=True)
        with open(os.path.join(archive_dir, "archive_tasks.md"), "a") as f:
            f.write(f"\n## Archive {datetime.now().isoformat()}\n")
            f.writelines(archive_lines)
        print(f"  📦 Archived {len(archive_lines)} completed tasks")
        return True
    return False

def get_unique_reply(state):
    last_msg = state.get("last_love_message", "")
    available = [m for m in LOVE_REPLIES if m != last_msg]
    if not available: available = LOVE_REPLIES 
    reply = random.choice(available)
    state["last_love_message"] = reply
    return reply

def git_push():
    try:
        subprocess.run(["git", "pull", "--rebase"], cwd=JARVIS_DIR, check=False) 
        status = subprocess.run(["git", "status", "--porcelain"], cwd=JARVIS_DIR, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "add", "."], cwd=JARVIS_DIR, check=True)
            subprocess.run(["git", "commit", "-m", f"Auto-update {datetime.now().strftime('%Y-%m-%d %H:%M')}"], cwd=JARVIS_DIR, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "push"], cwd=JARVIS_DIR, check=True)
        print("  ☁️ Git Sync: Pushed to GitHub")
    except Exception as e: print(f"  ❌ Git Sync failed: {e}")

def main():
    state = load_state()
    print(f"🚀 JARVIS Collector v4.1 | {datetime.now().isoformat()}")
    last_ids = state.get("last_msg_ids", {})
    total_saved = 0
    for chat_name, limit in CHATS:
        print(f"\n📥 {chat_name}")
        messages = read_chat_raw(chat_name, limit)
        if not messages: continue
        last_id = last_ids.get(chat_name, 0)
        new_msgs = [m for m in messages if m['id'] > last_id]
        if new_msgs:
            print(f"  {len(new_msgs)} new messages")
        
        text_lines = []
        for m in new_msgs:
            is_out = m.get('isOutgoing', False)
            sender = "Valekk_17" if is_out else chat_name.split('@')[0].strip()
            text = m.get('text', '')
            if text: text_lines.append(f"{sender}: {text}")
            if chat_name == WIFE_CHAT and not is_out and text:
                text_lower = text.lower()
                if any(k in text_lower for k in LOVE_KEYWORDS):
                    now = time.time()
                    last_reply = state.get("last_love_reply", 0)
                    if now - last_reply > 3600:
                        print("  ❤️ Love detected!")
                        reply = get_unique_reply(state)
                        if send_message(chat_name, reply): state["last_love_reply"] = now

        if chat_name == MOM_CHAT:
            now_dt = datetime.now()
            hour = now_dt.hour
            date_str = now_dt.strftime("%Y-%m-%d")
            last_greet = state.get("last_morning_greet_mom", "")
            if 7 <= hour < 9 and last_greet != date_str:
                print(f"  ☀️ Morning Greeting")
                msg = random.choice(MORNING_GREETINGS)
                if send_message(chat_name, msg): state["last_morning_greet_mom"] = date_str

        if new_msgs:
            last_ids[chat_name] = max([m['id'] for m in new_msgs])
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
    print("📝 Syncing User Tasks...")
    try: subprocess.run(["python3", "/root/.openclaw/workspace/sync_tasks.py"])
    except: pass
    
    archived = archive_completed()
    check_deadlines(state)
    update_dashboard() # Update pinned msg
    
    if total_saved > 0 or archived:
        print("🎨 Regenerating D3 graph...")
        try: subprocess.run(["python3", "/root/.openclaw/workspace/generate_canvas.py"], stdout=open("/root/.openclaw/workspace/graph.html", "w"))
        except: pass
    git_push()

if __name__ == "__main__":
    main()
