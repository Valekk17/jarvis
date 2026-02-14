import os
import time
import shutil
import psycopg2
from extract_graph import extract_context_graph, get_or_create_node, create_edge, PG_DSN
from key_manager import KeyManager

INBOX_DIR = "/root/.openclaw/workspace/cybos_data/inbox"
PROCESSED_DIR = "/root/.openclaw/workspace/cybos_data/processed"

def process_file(filepath):
    print(f"Indexing: {filepath}")
    with open(filepath, "r") as f:
        text = f.read()
    
    manager = KeyManager()
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    # Extract
    data = extract_context_graph(text, manager)
    
    # Save
    for a in data.get("actors", []):
        get_or_create_node(cursor, 'Actor', a['name'], a.get('description'), manager)
    for t in data.get("topics", []):
        get_or_create_node(cursor, 'Topic', t['name'], t.get('description'), manager)
    for f in data.get("facts", []):
        sid = get_or_create_node(cursor, 'Concept', f['subject'], manager=manager)
        tid = get_or_create_node(cursor, 'Concept', f['object'], manager=manager)
        create_edge(cursor, sid, tid, f['predicate'])
        
    conn.commit()
    conn.close()
    
    # Move to processed
    filename = os.path.basename(filepath)
    shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))
    print(f"Moved {filename} to processed.")

def watch():
    print("Indexer Started...")
    while True:
        for filename in os.listdir(INBOX_DIR):
            if filename.endswith(".md"):
                filepath = os.path.join(INBOX_DIR, filename)
                try:
                    process_file(filepath)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        time.sleep(10)

if __name__ == "__main__":
    watch()
