#!/usr/bin/env python3
"""
Backfill Collector
Reads last 500 messages from specific chats -> Gemini extraction -> Append to Graph
"""
import subprocess
import json
import os
import sys
import hashlib
import time
from datetime import date, datetime

# Reuse collector logic by importing or copying
# We will copy core functions to be safe and independent

JARVIS_DIR = "/root/.openclaw/workspace/memory" # Updated path
GRAPH_FILE = os.path.join(JARVIS_DIR, "context_graph.md")
STATE_FILE = os.path.join(JARVIS_DIR, "collector_state.json")
TODAY = date.today().isoformat()

CHATS = [
    ("Леха Косенко", 500),
    ("Андрейка Братик", 500),
    ("Мамуля", 500)
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
    state["seen_hashes"] = state.get("seen_hashes", [])[-1000:] # Keep more history
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def content_hash(text):
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

def read_chat(chat_name, limit=500):
    print(f"Reading {limit} messages from {chat_name}...")
    try:
        # tg read command
        res = subprocess.run(["tg", "read", chat_name, "-n", str(limit), "--json"],
                            capture_output=True, text=True, timeout=120) # Long timeout
        output = res.stdout
        start = output.find('{')
        end = output.rfind('}') + 1
        if start == -1 or end == 0:
            print("  No JSON output found")
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
1. Anti-Noise: Ignore greetings, small talk, pure emotions.
2. **Implicit Tasks**: If a fact implies a concrete action, extract as PLAN.
   - "Order arrived" -> Plan: "Pick up order"
3. **Principles vs Tasks**: Concrete -> PLAN, Abstract -> DECISION.
4. **Relations**: Identify relationships between Actors and Entities.
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
"{text[:30000]}"
"""
    # Increased text limit for backfill (Gemini Pro context is large)

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
                print(f"Key exhausted ({model_name}). Rotating...")
                manager.rotate()
                if attempt > 2: model_name = "gemini-2.5-flash"
                time.sleep(2)
                continue
            print(f"  ❌ Gemini error: {e}")
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
    
    if new_lines and os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE) as f: content = f.read()
        for entity_type, line in new_lines:
            section = entity_type.capitalize()
            marker = f"## {section}"
            if marker in content:
                content = content.replace(marker, f"{marker}\n{line}")
            else:
                content += f"\n\n{marker}\n{line}"
        with open(GRAPH_FILE, 'w') as f: f.write(content)
    elif new_lines:
        sections = {}
        for entity_type, line in new_lines: sections.setdefault(entity_type, []).append(line)
        with open(GRAPH_FILE, 'w') as f:
            f.write("# Context Graph Entities\n\n")
            for sec, lines in sections.items():
                f.write(f"## {sec.capitalize()}\n")
                f.write("\n".join(lines) + "\n\n")
    
    state["seen_hashes"] = list(seen)
    return saved

def main():
    state = load_state()
    print("🚀 JARVIS Backfill | 500 messages")
    total_saved = 0
    
    for chat_name, limit in CHATS:
        print(f"\n📥 {chat_name} (limit={limit})")
        text = read_chat(chat_name, limit)
        if not text:
            print("  No messages found")
            continue
        
        # Chunk text if too long (Gemini limit)
        # Simple chunking by lines
        lines = text.split('\n')
        chunk_size = 300 # ~15-20k chars
        chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
        
        print(f"  Processing {len(lines)} lines in {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            chunk_text = "\n".join(chunk)
            print(f"  Chunk {i+1}/{len(chunks)} ({len(chunk_text)} chars) → Gemini...")
            
            result = extract_with_gemini(chunk_text, chat_name)
            data = parse_json(result)
            
            if data:
                counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
                print(f"    Extracted: {counts}")
                saved = append_to_graph(data, state)
                print(f"    ✓ Saved {saved}")
                total_saved += saved
            else:
                print("    ❌ Failed")
            
            time.sleep(2) # Rate limit friendly
    
    save_state(state)
    print(f"\n🏆 Total saved: {total_saved}")
    
    # Update visualization
    print("🎨 Updating graph.html...")
    try:
        subprocess.run(["python3", "/root/.openclaw/workspace/generate_canvas.py"], 
                      stdout=open("/root/.openclaw/workspace/graph.html", "w"),
                      check=True)
        print("   ✓ Done")
    except: pass

if __name__ == "__main__":
    main()
