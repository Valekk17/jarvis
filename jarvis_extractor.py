import os
import re
import json
import uuid
from datetime import date
import google.generativeai as genai
from key_manager import KeyManager

JARVIS_DIR = "/root/.openclaw/workspace/jarvis"
ACTORS_FILE = os.path.join(JARVIS_DIR, "memory/actors.md")
PROMISES_FILE = os.path.join(JARVIS_DIR, "memory/promises.md")
DECISIONS_FILE = os.path.join(JARVIS_DIR, "memory/decisions.md")
METRICS_FILE = os.path.join(JARVIS_DIR, "memory/metrics.md")
PLANS_FILE = os.path.join(JARVIS_DIR, "memory/plans.md")
ONTOLOGY_FILE = os.path.join(JARVIS_DIR, "ONTOLOGY.md")

TODAY = date.today().isoformat()

def load_actors():
    aliases = {}
    if not os.path.exists(ACTORS_FILE): return {}
    with open(ACTORS_FILE, "r") as f:
        content = f.read()
    current_id = None
    for line in content.splitlines():
        if line.startswith("## actor-"):
            current_id = line.strip().replace("## ", "")
        elif line.strip().startswith("- aliases:") and current_id:
            try:
                json_str = line.split(":", 1)[1].strip()
                names = json.loads(json_str)
                for name in names:
                    aliases[name.lower()] = current_id
            except: pass
    return aliases

def resolve_actor(name, actors_map):
    lower = name.lower()
    return actors_map.get(lower, name)

def save_to_memory(data):
    """Save extracted entities to jarvis/memory/*.md files."""
    
    # Save promises
    if data.get("promises"):
        with open(PROMISES_FILE, "a") as f:
            for p in data["promises"]:
                uid = str(uuid.uuid4())[:8]
                f.write(f"\n## promise-{uid}\n")
                f.write(f"- from: {p.get('from', 'unknown')}\n")
                f.write(f"- to: {p.get('to', 'unknown')}\n")
                f.write(f"- content: {p.get('content', '')}\n")
                f.write(f"- deadline: {p.get('deadline', 'null')}\n")
                f.write(f"- status: {p.get('status', 'pending')}\n")
                f.write(f"- source_quote: \"{p.get('source_quote', p.get('content', ''))}\"\n")
                f.write(f"- source_date: {TODAY}\n")
                f.write(f"- confidence: {p.get('confidence', 0.8)}\n")
    
    # Save decisions
    if data.get("decisions"):
        with open(DECISIONS_FILE, "a") as f:
            for d in data["decisions"]:
                uid = str(uuid.uuid4())[:8]
                f.write(f"\n## decision-{uid}\n")
                f.write(f"- actors: [actor-owner]\n")
                f.write(f"- content: {d.get('content', '')}\n")
                f.write(f"- date: {d.get('date', TODAY)}\n")
                f.write(f"- source_quote: \"{d.get('source_quote', d.get('content', ''))}\"\n")
                f.write(f"- confidence: {d.get('confidence', 0.8)}\n")
    
    # Save metrics
    if data.get("metrics"):
        with open(METRICS_FILE, "a") as f:
            for m in data["metrics"]:
                uid = str(uuid.uuid4())[:8]
                f.write(f"\n## metric-{uid}\n")
                f.write(f"- actor: {m.get('actor_id', 'null')}\n")
                f.write(f"- name: {m.get('name', '')}\n")
                f.write(f"- value: {m.get('value', 0)}\n")
                f.write(f"- unit: {m.get('unit', '')}\n")
                f.write(f"- date: {TODAY}\n")
                f.write(f"- source_quote: \"{m.get('source_quote', m.get('name', ''))}\"\n")
                f.write(f"- confidence: {m.get('confidence', 0.8)}\n")
    
    # Save plans
    if data.get("plans"):
        with open(PLANS_FILE, "a") as f:
            for p in data["plans"]:
                uid = str(uuid.uuid4())[:8]
                f.write(f"\n## plan-{uid}\n")
                f.write(f"- actor: actor-owner\n")
                f.write(f"- content: {p.get('content', '')}\n")
                f.write(f"- target_date: {p.get('target_date', 'null')}\n")
                f.write(f"- status: {p.get('status', 'active')}\n")
                f.write(f"- source_quote: \"{p.get('source_quote', p.get('content', ''))}\"\n")
                f.write(f"- confidence: {p.get('confidence', 0.8)}\n")

def extract(text, save=False):
    manager = KeyManager()
    
    with open(ONTOLOGY_FILE, "r") as f:
        ontology = f.read()
        
    actors_map = load_actors()
    known_actors = list(actors_map.keys())
    
    prompt = f"""
    You are the Indexer Agent for JARVIS.
    Your task is to extract structured entities from the text based on the ONTOLOGY.
    Current date: {TODAY}
    
    RULES:
    1.  **Anti-Noise**: Ignore greetings, small talk, emotions. If no facts/promises/decisions, return empty JSON.
    2.  **Strict Schema**: Output must match the JSON schema below.
    3.  **Resolution**: Map names to known Actor IDs if possible.
        Known Aliases: {json.dumps(known_actors[:50])}
    4.  **Confidence**: Only include entities with confidence >= 0.7
    5.  **source_quote**: Always include the original quote from text
    
    SCHEMA:
    {{
      "actors": [ {{"canonical_name": "Name", "role": "Role", "aliases": []}} ],
      "promises": [ {{"from": "ActorName", "to": "ActorName", "content": "What", "deadline": "YYYY-MM-DD", "status": "pending", "confidence": 0.9, "source_quote": "original text"}} ],
      "decisions": [ {{"content": "What", "date": "YYYY-MM-DD", "confidence": 0.9, "source_quote": "original text"}} ],
      "metrics": [ {{"name": "Metric", "value": 123, "unit": "unit", "confidence": 0.9, "source_quote": "original text"}} ],
      "plans": [ {{"content": "Goal", "status": "active", "confidence": 0.9, "source_quote": "original text"}} ]
    }}
    
    TEXT:
    "{text}"
    
    OUTPUT JSON:
    """
    
    max_retries = len(manager.keys) * 2
    for attempt in range(max_retries):
        key = manager.get_key()
        genai.configure(api_key=key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        try:
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            result = json.loads(response.text)
            
            if save:
                save_to_memory(result)
                
            return result
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                manager.rotate()
                continue
            else:
                return {"error": str(e)}
    return {}

if __name__ == "__main__":
    test_text = "Привет, как дела? Вчера виделся с Лехой Косенко. Он обещал скинуть отчет до пятницы. Решили использовать Postgres."
    print(f"Input: {test_text}\n")
    result = extract(test_text, save=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))
