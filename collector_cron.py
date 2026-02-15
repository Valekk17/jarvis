#!/usr/bin/env python3
"""
JARVIS Auto-Collector v2
Reads recent Telegram messages → Gemini extraction → markdown files
No PostgreSQL dependency. Built-in OpenClaw memory indexer picks up changes.
"""
import subprocess
import json
import os
import sys
import hashlib
import time
from datetime import date, datetime

# Config
JARVIS_DIR = "/root/.openclaw/workspace/jarvis"
MEMORY_DIR = os.path.join(JARVIS_DIR, "memory")
STATE_FILE = os.path.join(MEMORY_DIR, "collector_state.json")
GRAPH_FILE = os.path.join(MEMORY_DIR, "context_graph.md")
TODAY = date.today().isoformat()

# Personal chats to monitor
CHATS = [
    ("Мой Мир❤️", 50),       # Wife Arisha
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
    return {"last_run": None, "processed_chats": {}, "seen_hashes": []}

def save_state(state):
    state["last_run"] = datetime.now().isoformat()
    # Keep only last 500 hashes
    state["seen_hashes"] = state.get("seen_hashes", [])[-500:]
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def content_hash(text):
    """Generate hash for deduplication."""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

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
    """Extract entities using Gemini."""
    manager = KeyManager()
    
    # Load known actors
    actors_file = os.path.join(MEMORY_DIR, "actors.md")
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

    max_retries = 10
    for attempt in range(max_retries):
        key = manager.get_key()
        try:
            if USE_NEW_API:
                client = genai.Client(api_key=key)
                config = types.GenerateContentConfig(temperature=0.1)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config,
                )
                return response.text
            else:
                genai.configure(api_key=key)
                model = genai.GenerativeModel("models/gemini-2.5-pro")
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                manager.rotate()
                print(f"Rotating to key index {manager.current_index}...")
                continue
            print(f"  ❌ Gemini error: {e}")
            return None
    return None

def parse_json(text):
    """Parse JSON from Gemini response."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    try:
        return json.loads(text.strip())
    except:
        return None

def append_to_graph(data, state):
    """Append new entities to context_graph.md with deduplication."""
    seen = set(state.get("seen_hashes", []))
    
    # Read existing file
    existing = ""
    if os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE) as f:
            existing = f.read()
    
    new_lines = []
    saved = 0
    
    for entity_type in ["promises", "decisions", "metrics", "plans"]:
        items = data.get(entity_type, [])
        for item in items:
            # Create content string for hashing
            if entity_type == "metrics":
                content_str = f"{item.get('name','')}: {item.get('value','')}"
            else:
                content_str = item.get('content', '')
            
            h = content_hash(content_str)
            if h in seen:
                continue
            seen.add(h)
            
            # Format line
            quote = item.get('source_quote', '')
            conf = item.get('confidence', 0)
            
            if entity_type == "promises":
                line = f"- [pending] {content_str} | From: {item.get('from','')} → {item.get('to','')} | Deadline: {item.get('deadline','none')} | Quote: \"{quote}\""
            elif entity_type == "decisions":
                line = f"- {content_str} | Date: {item.get('date', TODAY)} | Quote: \"{quote}\""
            elif entity_type == "metrics":
                line = f"- **{item.get('name','')}**: {item.get('value','')} {item.get('unit','')} | Quote: \"{quote}\""
            elif entity_type == "plans":
                line = f"- [{item.get('status','active')}] {content_str} | Target: {item.get('target_date','none')} | Quote: \"{quote}\""
            
            new_lines.append((entity_type, line))
            saved += 1
    
    # Append to file by section
    if new_lines and os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE) as f:
            content = f.read()
        
        for entity_type, line in new_lines:
            section = entity_type.capitalize()
            marker = f"## {section}"
            if marker in content:
                content = content.replace(marker, f"{marker}\n{line}")
            else:
                content += f"\n\n{marker}\n{line}"
        
        with open(GRAPH_FILE, 'w') as f:
            f.write(content)
    elif new_lines:
        # Create new file
        sections = {}
        for entity_type, line in new_lines:
            sections.setdefault(entity_type, []).append(line)
        with open(GRAPH_FILE, 'w') as f:
            f.write("# Context Graph Entities\n\n")
            for sec, lines in sections.items():
                f.write(f"## {sec.capitalize()}\n")
                f.write("\n".join(lines) + "\n\n")
    
    # Update seen hashes
    state["seen_hashes"] = list(seen)
    return saved

def main():
    state = load_state()
    print(f"🚀 JARVIS Collector v2 (markdown) | {datetime.now().isoformat()}")
    print(f"   Last run: {state.get('last_run', 'never')}")
    
    total_saved = 0
    
    for chat_name, limit in CHATS:
        print(f"\n📥 {chat_name} (limit={limit})")
        text = read_chat(chat_name, limit)
        if not text:
            print("  No messages found")
            continue
        
        print(f"  {len(text)} chars → Gemini...")
        result = extract_with_gemini(text, chat_name)
        data = parse_json(result)
        
        if not data:
            print("  ❌ No valid JSON returned")
            continue
        
        counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
        print(f"  Extracted: {counts}")
        
        saved = append_to_graph(data, state)
        print(f"  ✓ Saved {saved} new entities (deduped)")
        total_saved += saved
    
    save_state(state)
    print(f"\n🏆 Total saved: {total_saved}")

if __name__ == "__main__":
    main()
