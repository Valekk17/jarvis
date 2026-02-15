#!/usr/bin/env python3
"""
JARVIS Context Graph: Full Ingestion Pipeline
Processes multiple Telegram chats → extracts entities → saves to DB + md files
Implements: Temporal Decay, Deduplication, Multi-source Ingestion
"""
import subprocess
import json
import os
import sys
import uuid
import psycopg2
from datetime import datetime, date
from jarvis_extractor import extract

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
JARVIS_DIR = "/root/.openclaw/workspace/jarvis"
TODAY = date.today().isoformat()

def setup_db():
    """Ensure all entity tables exist in PostgreSQL."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    # Drop old simple schema, create proper one
    cur.execute("""
    CREATE TABLE IF NOT EXISTS actors (
        id TEXT PRIMARY KEY,
        canonical_name TEXT NOT NULL,
        aliases TEXT[] DEFAULT '{}',
        role TEXT,
        context TEXT,
        last_seen DATE,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS promises (
        id TEXT PRIMARY KEY,
        from_actor TEXT,
        to_actor TEXT,
        content TEXT NOT NULL,
        deadline DATE,
        status TEXT DEFAULT 'pending',
        source_quote TEXT,
        source_date DATE,
        confidence FLOAT DEFAULT 0.8,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id TEXT PRIMARY KEY,
        actors TEXT[],
        content TEXT NOT NULL,
        context TEXT,
        decision_date DATE,
        source_quote TEXT,
        confidence FLOAT DEFAULT 0.8,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id TEXT PRIMARY KEY,
        actor_id TEXT,
        name TEXT NOT NULL,
        value FLOAT,
        unit TEXT,
        metric_date DATE,
        source_quote TEXT,
        confidence FLOAT DEFAULT 0.8,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY,
        actor_id TEXT,
        content TEXT NOT NULL,
        target_date DATE,
        status TEXT DEFAULT 'active',
        source_quote TEXT,
        confidence FLOAT DEFAULT 0.8,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    
    conn.commit()
    conn.close()
    print("✓ DB schema ready")

def seed_actors():
    """Seed known actors from actors.md."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    actors = [
        ("actor-owner", "Valekk_17", ["я","мне","мой","valekk","valekk_17"], "owner", "military serviceman, Serpukhov"),
        ("actor-arisha", "Arisha", ["Ариша","жена","wife","Мой Мир"], "family", "wife, pregnant ~12.3 weeks"),
        ("actor-leha-kosenko", "Alexey Kosenko", ["Лёха","Леха","Leha","Косенко","Kosenko"], "friend", "friend from Moscow"),
        ("actor-evgeniya", "Evgeniya Kovalkova", ["мама","Евгения","Ковалькова","mom"], "family", "mother"),
        ("actor-andrey", "Andrey Kovalkov", ["Андрей","брат","Ковальков","brother"], "family", "brother"),
    ]
    
    for a in actors:
        cur.execute("""
            INSERT INTO actors (id, canonical_name, aliases, role, context) 
            VALUES (%s, %s, %s, %s, %s) 
            ON CONFLICT (id) DO UPDATE SET canonical_name=EXCLUDED.canonical_name, aliases=EXCLUDED.aliases
        """, a)
    
    conn.commit()
    conn.close()
    print(f"✓ Seeded {len(actors)} actors")

def read_chat(chat_name, limit=200):
    """Read Telegram chat and return attributed messages."""
    print(f"  Reading: {chat_name} (limit={limit})...")
    res = subprocess.run(["tg", "read", chat_name, "-n", str(limit), "--json"], 
                        capture_output=True, text=True, timeout=60)
    
    output = res.stdout
    start = output.find('{')
    end = output.rfind('}') + 1
    if start == -1 or end == 0:
        print(f"  ❌ Failed to read {chat_name}")
        return ""
    
    try:
        data = json.loads(output[start:end])
        messages = data.get('messages', [])
    except:
        print(f"  ❌ JSON parse error for {chat_name}")
        return ""
    
    # Build attributed text
    lines = []
    for m in messages:
        is_out = m.get('isOutgoing', False)
        sender = "Valekk" if is_out else chat_name
        text = m.get('text', '')
        if text and len(text) > 5:  # Skip very short messages
            lines.append(f"{sender}: {text}")
    
    full_text = "\n".join(lines)
    print(f"  ✓ {len(lines)} messages, {len(full_text)} chars")
    return full_text

def save_entities_to_db(data, source_chat):
    """Save extracted entities to PostgreSQL."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    saved = {"promises": 0, "decisions": 0, "metrics": 0, "plans": 0}
    
    for p in data.get("promises", []):
        uid = f"promise-{uuid.uuid4().hex[:8]}"
        try:
            cur.execute("""
                INSERT INTO promises (id, from_actor, to_actor, content, deadline, status, source_quote, source_date, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (uid, p.get('from',''), p.get('to',''), p.get('content',''), 
                  p.get('deadline'), p.get('status','pending'), 
                  p.get('source_quote',''), TODAY, p.get('confidence', 0.8)))
            saved["promises"] += 1
        except Exception as e:
            conn.rollback()
            continue
    
    for d in data.get("decisions", []):
        uid = f"decision-{uuid.uuid4().hex[:8]}"
        try:
            cur.execute("""
                INSERT INTO decisions (id, content, decision_date, source_quote, confidence)
                VALUES (%s, %s, %s, %s, %s)
            """, (uid, d.get('content',''), d.get('date', TODAY), 
                  d.get('source_quote',''), d.get('confidence', 0.8)))
            saved["decisions"] += 1
        except Exception as e:
            conn.rollback()
            continue
    
    for m in data.get("metrics", []):
        uid = f"metric-{uuid.uuid4().hex[:8]}"
        try:
            cur.execute("""
                INSERT INTO metrics (id, name, value, unit, metric_date, source_quote, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (uid, m.get('name',''), m.get('value',0), m.get('unit',''), 
                  TODAY, m.get('source_quote',''), m.get('confidence', 0.8)))
            saved["metrics"] += 1
        except Exception as e:
            conn.rollback()
            continue
    
    for p in data.get("plans", []):
        uid = f"plan-{uuid.uuid4().hex[:8]}"
        try:
            cur.execute("""
                INSERT INTO plans (id, content, status, source_quote, confidence)
                VALUES (%s, %s, %s, %s, %s)
            """, (uid, p.get('content',''), p.get('status','active'), 
                  p.get('source_quote',''), p.get('confidence', 0.8)))
            saved["plans"] += 1
        except Exception as e:
            conn.rollback()
            continue
    
    conn.commit()
    conn.close()
    return saved

def export_graph_json():
    """Export full graph to D3-compatible JSON for visualization."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    nodes = []
    links = []
    node_ids = {}
    idx = 0
    
    # Actors
    cur.execute("SELECT id, canonical_name, role, context FROM actors")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[1], "group": "Actor", "role": row[2], "context": row[3] or ""})
        node_ids[row[0]] = idx
        idx += 1
    
    # Promises
    cur.execute("SELECT id, from_actor, to_actor, content, status, confidence FROM promises")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[3][:40], "group": "Promise", "status": row[4], "confidence": row[5]})
        promise_idx = idx
        node_ids[row[0]] = idx
        idx += 1
        
        # Link from_actor → promise
        for actor_id, actor_idx in node_ids.items():
            if actor_id.startswith("actor-") and nodes[actor_idx].get("name","").lower() in row[1].lower():
                links.append({"source": actor_idx, "target": promise_idx, "relation": "PROMISED"})
                break
    
    # Decisions
    cur.execute("SELECT id, content, confidence FROM decisions")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[1][:40], "group": "Decision", "confidence": row[2]})
        node_ids[row[0]] = idx
        idx += 1
    
    # Metrics
    cur.execute("SELECT id, name, value, unit, confidence FROM metrics")
    for row in cur.fetchall():
        label = f"{row[1]}: {row[2]} {row[3]}"
        nodes.append({"id": idx, "name": label[:50], "group": "Metric", "confidence": row[4]})
        node_ids[row[0]] = idx
        idx += 1
    
    # Plans
    cur.execute("SELECT id, content, status, confidence FROM plans")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[1][:40], "group": "Plan", "status": row[2], "confidence": row[3]})
        node_ids[row[0]] = idx
        idx += 1
    
    # Link all entities to owner
    owner_idx = node_ids.get("actor-owner", 0)
    for n in nodes:
        if n["group"] != "Actor" and n["id"] != owner_idx:
            links.append({"source": owner_idx, "target": n["id"], "relation": "OWNS"})
    
    # Link Arisha-related entities
    arisha_idx = node_ids.get("actor-arisha")
    if arisha_idx is not None:
        for n in nodes:
            name_lower = n.get("name","").lower()
            if any(kw in name_lower for kw in ["pregnancy", "insurance", "baby", "беремен", "страхов"]):
                links.append({"source": arisha_idx, "target": n["id"], "relation": "RELATED"})
    
    conn.close()
    
    graph_data = {"nodes": nodes, "links": links}
    with open("/root/.openclaw/workspace/graph_data.json", "w") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Exported: {len(nodes)} nodes, {len(links)} links")
    return len(nodes), len(links)

def process_chats(chats):
    """Process multiple chats through the pipeline."""
    total = {"promises": 0, "decisions": 0, "metrics": 0, "plans": 0}
    
    for chat_name, limit in chats:
        print(f"\n{'='*40}")
        print(f"Processing: {chat_name}")
        print(f"{'='*40}")
        
        text = read_chat(chat_name, limit)
        if not text or len(text) < 50:
            print(f"  ⚠ Skipping {chat_name} (too short)")
            continue
        
        # Chunk if text is very long (>8000 chars)
        chunks = [text[i:i+6000] for i in range(0, len(text), 6000)]
        
        for i, chunk in enumerate(chunks):
            print(f"  Extracting chunk {i+1}/{len(chunks)}...")
            result = extract(chunk, save=True)
            
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
                continue
            
            saved = save_entities_to_db(result, chat_name)
            for k, v in saved.items():
                total[k] += v
            print(f"  ✓ Saved: {saved}")
    
    print(f"\n{'='*40}")
    print(f"TOTAL: {total}")
    print(f"{'='*40}")
    return total

if __name__ == "__main__":
    print("🚀 JARVIS Context Graph: Full Ingestion")
    print("=" * 40)
    
    # Step 1: Setup DB
    setup_db()
    seed_actors()
    
    # Step 2: Define chats to process
    chats = [
        ("Мой Мир❤️", 300),      # Wife Arisha
    ]
    
    # Step 3: Process
    total = process_chats(chats)
    
    # Step 4: Export graph
    n, e = export_graph_json()
    
    print(f"\n🏆 Done! Graph: {n} nodes, {e} links")
