import json
import os
import time
import google.generativeai as genai
from key_manager import KeyManager
from datetime import datetime

# Paths
WORKSPACE_DIR = "/root/.openclaw/workspace"
GRAPH_FILE = os.path.join(WORKSPACE_DIR, "knowledge_graph.json")
LEGACY_GRAPH_FILE = os.path.join(WORKSPACE_DIR, "graph_data.json")
EVENTS_FILE = os.path.join(WORKSPACE_DIR, "events.jsonl")
STATE_FILE = os.path.join(WORKSPACE_DIR, "graph_updater_state.json")

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def migrate_legacy_graph():
    """Migrate graph_data.json to knowledge_graph.json if needed."""
    if os.path.exists(GRAPH_FILE):
        return load_json(GRAPH_FILE)
    
    legacy = load_json(LEGACY_GRAPH_FILE)
    if not legacy:
        return {"nodes": [], "edges": []}
        
    print("Migrating legacy graph_data.json...")
    graph = {
        "nodes": legacy.get("nodes", []),
        "edges": legacy.get("links", []) # Rename links to edges
    }
    
    # Normalize edges if they use 'links' format
    for edge in graph["edges"]:
        if "source" in edge and "target" in edge:
            pass # d3 format OK
        # Ensure we have standard keys if needed
        
    save_json(GRAPH_FILE, graph)
    return graph

def get_new_events(last_id):
    events = []
    if not os.path.exists(EVENTS_FILE):
        return []
        
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                evt = json.loads(line)
                if not last_id or evt['id'] > last_id:
                    events.append(evt)
            except:
                continue
    return events

def extract_entities(text, key_manager):
    """Calling LLM to extract entities."""
    models = ['models/gemini-2.5-flash', 'models/gemini-1.5-flash']
    
    prompt = f"""
    Analyze the following text from a user's life log and extract Knowledge Graph entities.
    
    **Ontology:**
    - **Entities** (Nodes): Person, Place, Project, Skill, Metric, Promise, Decision, Goal.
    - **Relations** (Edges): KNOWS, VISITED, WORKING_ON, HAS_SKILL, MEASURED, PROMISED_TO, DECIDED.
    
    **Rules:**
    - Extract ONLY widely useful, long-term facts. Ignore trivial daily chatter.
    - If a Promise is made ("I will do X"), capture it as a Node (Promise) and link to Actor.
    - Return JSON.
    
    Text:
    {text}
    
    Output JSON format:
    {{
      "nodes": [ {{"name": "...", "label": "...", "properties": {{ "confidence": 0.9 }} }} ],
      "edges": [ {{"source": "Name1", "target": "Name2", "relation": "..."}} ]
    }}
    """
    
    for model_name in models:
        try:
            key = key_manager.get_key()
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            print(f"LLM Error ({model_name}): {e}")
            key_manager.rotate()
            continue
    return None

def update_graph(graph, extraction):
    if not extraction: return graph
    
    # 1. Update/Add Nodes
    # Using a simple lookup by name for now (Phase 2)
    # Phase 3: Embedding based deduplication
    
    existing_nodes = {str(n.get('name', '')).lower(): n for n in graph['nodes']}
    max_id = max([int(n.get('id', 0)) for n in graph['nodes']]) if graph['nodes'] else 0
    
    for node in extraction.get('nodes', []):
        name = node.get('name')
        if not name: continue
        
        key = name.lower()
        if key in existing_nodes:
            # Update existing
            existing = existing_nodes[key]
            # Merge properties?
            existing['last_seen'] = datetime.now().isoformat()
            # print(f"Updated node: {name}")
        else:
            # Add new
            max_id += 1
            node['id'] = max_id
            node['group'] = node.get('label', 'Entity') # Map label to group (legacy)
            node['last_seen'] = datetime.now().isoformat()
            graph['nodes'].append(node)
            existing_nodes[key] = node # Update lookup
            print(f"Added node: {name}")

    # 2. Update/Add Edges
    # Need to resolve names to IDs for edges if using ID-based links
    node_name_to_id = {str(n.get('name', '')).lower(): n.get('id') for n in graph['nodes']}
    
    for edge in extraction.get('edges', []):
        src_name = str(edge.get('source', '')).lower()
        tgt_name = str(edge.get('target', '')).lower()
        
        src_id = node_name_to_id.get(src_name)
        tgt_id = node_name_to_id.get(tgt_name)
        
        if src_id is not None and tgt_id is not None:
            # Check existence
            exists = False
            for e in graph['edges']:
                if e.get('source') == src_id and e.get('target') == tgt_id and e.get('relation') == edge.get('relation'):
                    exists = True
                    break
            
            if not exists:
                new_edge = {
                    "source": src_id,
                    "target": tgt_id,
                    "relation": edge.get('relation')
                }
                graph['edges'].append(new_edge)
                print(f"Added edge: {src_name} -> {tgt_name}")

    return graph

def main():
    print(f"Graph Updater started at {datetime.now()}")
    
    # 1. Load Graph
    graph = migrate_legacy_graph()
    print(f"Graph loaded: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    
    # 2. Load State
    state = load_json(STATE_FILE) or {"last_event_id": None}
    last_id = state.get("last_event_id")
    
    # 3. Get New Events
    events = get_new_events(last_id)
    if not events:
        print("No new events.")
        return

    print(f"Found {len(events)} new events.")
    
    # 4. Process in batches (simple concat for now)
    # Limit to last 50 events to avoid massive context
    batch_text = ""
    last_processed_id = last_id
    
    for evt in events[-50:]: 
        content = evt.get('content', '') or evt.get('text', '') or getattr(evt, 'message', '')
        if not content and 'metadata' in evt:
            content = str(evt['metadata'])
            
        date = evt.get('ts') or evt.get('date', '')
        batch_text += f"[{date}] {content}\n"
        last_processed_id = evt['id']
        
    if not batch_text.strip():
        print("No text content to analyze.")
        state["last_event_id"] = last_processed_id
        save_json(STATE_FILE, state)
        return

    # 5. Extract & Update
    key_manager = KeyManager()
    extraction = extract_entities(batch_text, key_manager)
    
    if extraction:
        update_graph(graph, extraction)
        save_json(GRAPH_FILE, graph)
        print("Graph saved.")
    else:
        print("LLM returned no extraction.")
        
    # 6. Save State
    state["last_event_id"] = last_processed_id
    save_json(STATE_FILE, state)
    print("Done.")

if __name__ == "__main__":
    main()
