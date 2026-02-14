import json
import subprocess
import os
import re
import psycopg2
from extract_graph import extract_context_graph, get_or_create_node, create_edge, PG_DSN
from key_manager import KeyManager

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

def import_history():
    print("Starting Import...")
    # Always refresh chats
    if os.path.exists("chats.json"): os.remove("chats.json")
    
    print("Fetching chats list...")
    subprocess.run("tg chats --json > chats.json", shell=True)

    with open("chats.json", "r") as f:
        chats = parse_json_output(f.read()) or []

    manager = KeyManager()
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()

    print(f"Found {len(chats)} chats.")
    
    for i, chat in enumerate(chats):
        name = chat.get('name') or chat.get('title')
        if not name: continue
        
        if chat.get('type') != 'user': continue
        
        print(f"[{i+1}/{len(chats)}] Processing: {name}")
        
        # Ensure Interaction
        try:
            me_id = get_or_create_node(cursor, 'Actor', 'Valekk_17', 'User', manager)
            partner_id = get_or_create_node(cursor, 'Actor', name, 'Chat Partner', manager)
            create_edge(cursor, me_id, partner_id, 'INTERACTED_WITH')
            conn.commit()
        except Exception as e:
            print(f"Error creating edge: {e}")

        # Read messages
        try:
            res = subprocess.run(["tg", "read", name, "-n", "30", "--json"], capture_output=True, text=True)
            data = parse_json_output(res.stdout)
            messages = data.get('messages', []) if isinstance(data, dict) else (data or [])
        except: continue
            
        full_text = "\n".join([m.get('text', '') or m.get('message', '') for m in messages])
        if not full_text: 
            print(f"  No text.")
            continue
        
        # Extract
        print(f"  Extracting from {len(full_text)} chars...")
        data = extract_context_graph(full_text, manager)
        
        # Save
        if not data:
            print("  Extraction returned empty.")
            continue

        for a in data.get("actors", []):
            aid = get_or_create_node(cursor, 'Actor', a['name'], a.get('description'), manager)
            
        for t in data.get("topics", []):
            tid = get_or_create_node(cursor, 'Topic', t['name'], t.get('description'), manager)

        for f in data.get("facts", []):
            sid = get_or_create_node(cursor, 'Concept', f['subject'], manager=manager)
            tid = get_or_create_node(cursor, 'Concept', f['object'], manager=manager)
            create_edge(cursor, sid, tid, f['predicate'])

        conn.commit()
        print("  Saved.")

    conn.close()
    print("Import Done.")

if __name__ == "__main__":
    import_history()
