import subprocess
import json
import os
import psycopg2
from jarvis_extractor import extract
from key_manager import KeyManager

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
CHAT_NAME = "Мой Мир❤️"

def save_to_db(data):
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    # Save Actor Arisha
    cursor.execute("INSERT INTO graph_nodes (label, name, description) VALUES ('Actor', 'Arisha', 'Wife') ON CONFLICT DO NOTHING")
    cursor.execute("SELECT id FROM graph_nodes WHERE name = 'Arisha'")
    arisha_id = cursor.fetchone()[0]
    
    # Save extracted
    for p in data.get("promises", []):
        cursor.execute("INSERT INTO graph_nodes (label, name, description) VALUES ('Promise', %s, %s) RETURNING id", (p['content'], f"Status: {p['status']}"))
        pid = cursor.fetchone()[0]
        # Link from 'from' actor. If 'from' is Arisha, link Arisha.
        # If 'from' is Valekk, find Valekk ID.
        from_name = p.get('from', 'Unknown')
        if "Arisha" in from_name:
            src = arisha_id
        else:
            # Assume it's me or find by name
            cursor.execute("INSERT INTO graph_nodes (label, name) VALUES ('Actor', %s) ON CONFLICT DO NOTHING RETURNING id", (from_name,))
            res = cursor.fetchone()
            src = res[0] if res else None
            if not src:
                cursor.execute("SELECT id FROM graph_nodes WHERE name = %s", (from_name,))
                src = cursor.fetchone()[0]

        if src:
            cursor.execute("INSERT INTO graph_edges (source_id, target_id, relation) VALUES (%s, %s, 'PROMISED')", (src, pid))

    conn.commit()
    conn.close()

def process():
    print(f"Reading chat: {CHAT_NAME}...")
    res = subprocess.run(["tg", "read", CHAT_NAME, "-n", "500", "--json"], capture_output=True, text=True)
    
    output = res.stdout
    start = output.find('{')
    end = output.rfind('}') + 1
    
    if start == -1 or end == -1:
        print("Failed to read chat JSON")
        return
        
    try:
        data = json.loads(output[start:end])
        messages = data.get('messages', [])
    except:
        print("JSON parse error")
        return
        
    full_text = ""
    for m in messages:
        is_out = m.get('isOutgoing', False)
        sender = "Valekk" if is_out else "Arisha"
        text = m.get('text', '')
        if text:
            full_text += f"{sender}: {text}\n"

    print(f"Extracted {len(full_text)} chars with attribution. Analyzing...")
    
    result = extract(full_text)
    print("Extraction result:", json.dumps(result, indent=2, ensure_ascii=False))
    
    save_to_db(result)
    print("Saved to Graph.")

if __name__ == "__main__":
    process()
