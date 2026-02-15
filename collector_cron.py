#!/usr/bin/env python3
"""
JARVIS Auto-Collector
Cron-driven: reads recent Telegram messages → Gemini 2.5 Pro extraction → DB + md
"""
import subprocess
import json
import os
import sys
import uuid
import time
import psycopg2
from datetime import date, datetime

# Config
PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
JARVIS_DIR = "/root/.openclaw/workspace/jarvis"
STATE_FILE = "/root/.openclaw/workspace/jarvis/memory/collector_state.json"
TODAY = date.today().isoformat()

# Personal chats to monitor (name, messages_per_run)
CHATS = [
    ("Мой Мир❤️", 50),       # Wife Arisha
]

# Gemini extraction
import google.generativeai as genai
sys.path.insert(0, "/root/.openclaw/workspace")
from key_manager import KeyManager

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_run": None, "processed_chats": {}}

def save_state(state):
    state["last_run"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def read_chat(chat_name, limit=50):
    try:
        res = subprocess.run(["tg", "read", chat_name, "-n", str(limit), "--json"],
                            capture_output=True, text=True, timeout=30)
        output = res.stdout
        start = output.find('{')
        end = output.rfind('}') + 1
        if start == -1 or end == 0:
            return ""
        data = json.loads(output[start:end])
        messages = data.get('messages', [])
        
        lines = []
        for m in messages:
            is_out = m.get('isOutgoing', False)
            sender = "Valekk" if is_out else chat_name.split('@')[0].strip()
            text = m.get('text', '')
            if text and len(text) > 3:
                lines.append(f"{sender}: {text}")
        return "\n".join(lines)
    except Exception as e:
        print(f"  ❌ Read error: {e}")
        return ""

def extract_with_gemini(text, chat_name):
    """Extract entities using Gemini 2.5 Pro (free tier)."""
    manager = KeyManager()
    
    # Load known actors
    actors_file = os.path.join(JARVIS_DIR, "memory/actors.md")
    known_actors = []
    if os.path.exists(actors_file):
        with open(actors_file) as f:
            for line in f:
                if line.strip().startswith("- canonical_name:"):
                    known_actors.append(line.split(":", 1)[1].strip())

    prompt = f"""You are JARVIS entity extractor. Current date: {TODAY}. Chat: {chat_name}.

RULES:
1. Anti-Noise: Ignore greetings, small talk, pure emotions.
2. **Implicit Tasks**: If a fact implies a concrete action, extract as PLAN.
   - "Order arrived" → Plan: "Pick up order"
3. **Principles vs Tasks**:
   - Concrete actions (call, buy, go) → PLAN.
   - Abstract stances (be polite, ignore haters, life rules) → DECISION.
   - Example: "Communicate adequately" → Decision (Stance), NOT Plan.
4. Only extract if confidence >= 0.7
5. Include source_quote (original text) for every entity
6. Known actors: {json.dumps(known_actors)}

OUTPUT JSON:
{{
  "promises": [{{"from":"Name","to":"Name","content":"what","deadline":"YYYY-MM-DD or null","status":"pending","confidence":0.9,"source_quote":"original"}}],
  "decisions": [{{"content":"what","date":"YYYY-MM-DD","confidence":0.9,"source_quote":"original"}}],
  "metrics": [{{"name":"metric","value":123,"unit":"unit","confidence":0.9,"source_quote":"original"}}],
  "plans": [{{"content":"goal","status":"active","confidence":0.9,"source_quote":"original"}}]
}}

TEXT:
"{text[:6000]}"
"""

    max_retries = len(manager.keys) * 2
    for attempt in range(max_retries):
        key = manager.get_key()
        genai.configure(api_key=key)
        # Try Pro first, fallback to Flash
        model_name = 'models/gemini-2.5-pro' if attempt < 3 else 'models/gemini-2.5-flash'
        model = genai.GenerativeModel(model_name)
        try:
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                manager.rotate()
                time.sleep(2)
                continue
            print(f"  ❌ Gemini error: {e}")
            return {}
    return {}

ACTOR_MAP = {
    "valekk": "actor-owner", "valekk_17": "actor-owner", "я": "actor-owner", "me": "actor-owner",
    "arisha": "actor-arisha", "ариша": "actor-arisha", "жена": "actor-arisha", "wife": "actor-arisha",
    "мой мир❤️": "actor-arisha", "мой мир": "actor-arisha",
    "leha": "actor-leha-kosenko", "леха": "actor-leha-kosenko", "лёха": "actor-leha-kosenko",
    "alexey kosenko": "actor-leha-kosenko", "косенко": "actor-leha-kosenko",
    "мама": "actor-evgeniya", "evgeniya": "actor-evgeniya",
    "андрей": "actor-andrey", "брат": "actor-andrey",
}

def resolve_actor(name):
    return ACTOR_MAP.get(name.lower().strip(), name)

def save_entities(data, chat_name):
    """Save to PostgreSQL + md files with actor resolution."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    saved = 0

    for p in data.get("promises", []):
        uid = f"promise-{uuid.uuid4().hex[:8]}"
        from_a = resolve_actor(p.get('from',''))
        to_a = resolve_actor(p.get('to',''))
        try:
            cur.execute("""INSERT INTO promises (id, from_actor, to_actor, content, deadline, status, source_quote, source_date, confidence)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (uid, from_a, to_a, p.get('content',''),
                 p.get('deadline'), p.get('status','pending'), p.get('source_quote',''), TODAY, p.get('confidence',0.8)))
            saved += 1
        except: conn.rollback()

    for d in data.get("decisions", []):
        uid = f"decision-{uuid.uuid4().hex[:8]}"
        try:
            cur.execute("""INSERT INTO decisions (id, content, decision_date, source_quote, confidence)
                VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (uid, d.get('content',''), d.get('date',TODAY), d.get('source_quote',''), d.get('confidence',0.8)))
            saved += 1
        except: conn.rollback()

    for m in data.get("metrics", []):
        uid = f"metric-{uuid.uuid4().hex[:8]}"
        try:
            cur.execute("""INSERT INTO metrics (id, name, value, unit, metric_date, source_quote, confidence)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (uid, m.get('name',''), m.get('value',0), m.get('unit',''), TODAY, m.get('source_quote',''), m.get('confidence',0.8)))
            saved += 1
        except: conn.rollback()

    for p in data.get("plans", []):
        uid = f"plan-{uuid.uuid4().hex[:8]}"
        try:
            cur.execute("""INSERT INTO plans (id, actor_id, content, status, source_quote, confidence)
                VALUES (%s,'actor-owner',%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (uid, p.get('content',''), p.get('status','active'), p.get('source_quote',''), p.get('confidence',0.8)))
            saved += 1
        except: conn.rollback()

    conn.commit()
    conn.close()
    return saved

def run():
    state = load_state()
    print(f"🚀 JARVIS Collector | {datetime.now().isoformat()}")
    print(f"   Last run: {state.get('last_run', 'never')}")
    
    total_saved = 0
    for chat_name, limit in CHATS:
        print(f"\n📥 {chat_name} (limit={limit})")
        text = read_chat(chat_name, limit)
        if not text or len(text) < 30:
            print(f"  ⚠ Skip (too short)")
            continue
        print(f"  {len(text)} chars → Gemini 2.5 Pro...")
        
        result = extract_with_gemini(text, chat_name)
        if not result:
            print(f"  ⚠ Empty result")
            continue
        
        counts = {k: len(v) for k, v in result.items() if isinstance(v, list)}
        print(f"  Extracted: {counts}")
        
        saved = save_entities(result, chat_name)
        total_saved += saved
        print(f"  ✓ Saved {saved} entities")
        
        state["processed_chats"][chat_name] = {"last": datetime.now().isoformat(), "entities": saved}
    
    save_state(state)
    print(f"\n🏆 Total saved: {total_saved}")
    return total_saved

if __name__ == "__main__":
    run()
