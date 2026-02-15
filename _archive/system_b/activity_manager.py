import json
import os
import time
import uuid
from datetime import datetime, timedelta
import google.generativeai as genai
from key_manager import KeyManager

# Configuration
WORKSPACE_DIR = "/root/.openclaw/workspace"
EVENTS_FILE = os.path.join(WORKSPACE_DIR, "events.jsonl")
ACTIVITY_FILE = os.path.join(WORKSPACE_DIR, "activity_graph.jsonl")
GRAPH_FILE = os.path.join(WORKSPACE_DIR, "knowledge_graph.json")
STATE_FILE = os.path.join(WORKSPACE_DIR, "activity_manager_state.json")

GAP_THRESHOLD_MINUTES = 30
MIN_EVENTS_PER_ACTIVITY = 2

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return None
    return None

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_jsonl(path, data):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def load_events(start_line=0):
    events = []
    current_line = 0
    if not os.path.exists(EVENTS_FILE):
        return [], 0
        
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            current_line += 1
            if current_line <= start_line:
                continue
            try:
                events.append(json.loads(line))
            except: continue
    return events, current_line

def cluster_events_by_time(events, gap_minutes=30):
    clusters = []
    if not events:
        return clusters

    current_cluster = [events[0]]
    
    for i in range(1, len(events)):
        prev = events[i-1]
        curr = events[i]
        
        # Parse timestamps (assume ISO format from event_logger)
        try:
            t_prev = datetime.fromisoformat(prev['ts'].replace('Z', '+00:00'))
            t_curr = datetime.fromisoformat(curr['ts'].replace('Z', '+00:00'))
            delta = (t_curr - t_prev).total_seconds() / 60
        except:
            delta = 0 # Fallback if time parsing fails
            
        if delta <= gap_minutes:
            current_cluster.append(curr)
        else:
            clusters.append(current_cluster)
            current_cluster = [curr]
            
    if current_cluster:
        clusters.append(current_cluster)
        
    return clusters

def summarize_activity(cluster, key_manager, known_projects):
    """Use LLM to summarize a cluster of events into an Activity."""
    if not cluster: return None
    
    # Prepare text for LLM
    text_log = ""
    start_time = cluster[0].get('ts')
    end_time = cluster[-1].get('ts')
    
    for e in cluster:
        # details
        content = e.get('content', '') or str(e.get('metadata', ''))
        text_log += f"[{e.get('ts')}] {e.get('action')}: {content}\n"
        
    models = ['models/gemini-2.5-flash', 'models/gemini-1.5-flash']
    
    prompt = f"""
    Analyze this sequence of user events and summarize it as a single Activity.
    
    Context:
    - Known Projects: {", ".join(known_projects)}
    
    Events:
    {text_log}
    
    Task:
    1. Identify the core intent (what was the user doing?).
    2. Assign a short Title.
    3. Link to a Project (if applicable, else "Miscellaneous").
    4. Summarize the Outcome.
    
    Return JSON:
    {{
      "title": "Short Title",
      "project": "Project Name",
      "summary": "What happened...",
      "tags": ["tag1", "tag2"]
    }}
    """
    
    for model_name in models:
        try:
            key = key_manager.get_key()
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            result = json.loads(response.text)
            
            # Enrich result
            result['id'] = f"act_{uuid.uuid4().hex[:8]}"
            result['start_ts'] = start_time
            result['end_ts'] = end_time
            result['event_count'] = len(cluster)
            result['event_ids'] = [e['id'] for e in cluster if 'id' in e]
            
            return result
        except Exception as e:
            print(f"LLM Error ({model_name}): {e}")
            key_manager.rotate()
            continue
            
    return None

def main():
    print(f"Activity Manager started at {datetime.now()}")
    
    # Load state
    state = load_json(STATE_FILE) or {"processed_lines": 0}
    processed_lines = state.get("processed_lines", 0)
    
    # Load events
    new_events, total_lines = load_events(processed_lines)
    print(f"Loaded {len(new_events)} new events (lines {processed_lines} to {total_lines}).")
    
    if len(new_events) < MIN_EVENTS_PER_ACTIVITY:
        print("Not enough events to cluster.")
        return

    # Load Knowledge Graph for context
    graph = load_json(GRAPH_FILE)
    known_projects = []
    if graph:
        for n in graph.get('nodes', []):
            if n.get('group', '').lower() in ['project', 'plan', 'goal']:
                known_projects.append(n.get('name'))
    
    # Cluster
    clusters = cluster_events_by_time(new_events, GAP_THRESHOLD_MINUTES)
    print(f"Identified {len(clusters)} clusters.")
    
    key_manager = KeyManager()
    
    for cluster in clusters:
        if len(cluster) < MIN_EVENTS_PER_ACTIVITY:
            continue # Skip noise
            
        print(f"Processing cluster: {len(cluster)} events...")
        activity = summarize_activity(cluster, key_manager, known_projects)
        
        if activity:
            append_jsonl(ACTIVITY_FILE, activity)
            print(f"  -> Saved Activity: {activity['title']}")
        else:
            print("  -> Failed to summarize.")
            
    # Update state
    state["processed_lines"] = total_lines
    save_json(STATE_FILE, state)
    print("Done.")

if __name__ == "__main__":
    main()
