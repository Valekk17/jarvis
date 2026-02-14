#!/usr/bin/env python3
"""
JARVIS: Full context compression + semantic search + self-awareness
Extracts all facts from conversation history, adds JARVIS capabilities to graph,
implements embedding-based semantic search.
"""
import json
import uuid
import psycopg2
import numpy as np
from datetime import date

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
TODAY = date.today().isoformat()

def ensure_embeddings_table():
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS entity_embeddings (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        content TEXT NOT NULL,
        embedding vector(3072),
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    # Semantic search index
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_embeddings_cosine 
    ON entity_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)
    """)
    conn.commit()
    conn.close()
    print("✓ Embeddings table ready")

def add_jarvis_to_graph():
    """Add JARVIS as an actor with capabilities, skills, tools."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    # JARVIS as actor
    cur.execute("""
        INSERT INTO actors (id, canonical_name, aliases, role, context) 
        VALUES ('actor-jarvis', 'JARVIS', ARRAY['Джарвис','jarvis','бот','bot','assistant'], 'system',
                'Personal AI Operating System. Model: Claude Opus 4.6 + Gemini. Platform: OpenClaw.')
        ON CONFLICT (id) DO UPDATE SET context=EXCLUDED.context
    """)
    
    # JARVIS capabilities as nodes in graph_nodes for visualization
    capabilities = [
        ("cap-voice", "Skill", "Voice Processing", "Whisper transcription (base model), voice command recognition"),
        ("cap-telegram", "Skill", "Telegram Integration", "Read/send messages, read chats, search contacts"),
        ("cap-graph", "Skill", "Context Graph", "Entity extraction, semantic search, relationship mapping"),
        ("cap-cron", "Skill", "Proactive Tasks", "Cron jobs, heartbeat checks, reminders, scheduled actions"),
        ("cap-web", "Skill", "Web Access", "Search (Brave), fetch pages, browser automation"),
        ("cap-code", "Skill", "Code Execution", "Python, bash, Docker, PostgreSQL, file management"),
        ("cap-memory", "Skill", "Memory System", "Long-term memory, daily logs, entity registry"),
        ("cap-tts", "Skill", "Text-to-Speech", "Voice synthesis for responses"),
    ]
    
    for cap_id, label, name, desc in capabilities:
        cur.execute("""
            INSERT INTO graph_nodes (label, name, description) VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (label, name, desc))
    
    conn.commit()
    conn.close()
    print(f"✓ JARVIS + {len(capabilities)} capabilities added")

def compress_session_context():
    """Extract ALL facts, plans, decisions from today's session into structured entities."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    # Facts extracted from full conversation context (manual extraction — more reliable than LLM for known data)
    
    # === METRICS ===
    metrics = [
        ("metric-preg", "actor-arisha", "pregnancy_weeks", 12.3, "weeks", "Arisha pregnancy ~12.3 weeks"),
        ("metric-ins-ded", "actor-arisha", "insurance_monthly_deduction", 500, "RUB", "списание по полису 500 руб"),
        ("metric-ins-sum", "actor-arisha", "insurance_total_sum", 150000, "RUB", "Страховая сумма 150000₽"),
        ("metric-ins-pct", "actor-arisha", "insurance_cashback_pct", 20, "%", "20% кэшбэка на страховку"),
        ("metric-phone-bat", "actor-arisha", "phone_battery", 20, "%", "батарея 20%"),
        ("metric-income", "actor-owner", "income_mentioned", 3000, "RUB", "доход 3000 руб"),
        ("metric-mrot", "actor-owner", "income_threshold_mrot", 8, "МРОТ", "порог 8 МРОТ"),
    ]
    
    for mid, actor, name, value, unit, quote in metrics:
        cur.execute("""
            INSERT INTO metrics (id, actor_id, name, value, unit, metric_date, source_quote, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0.9)
            ON CONFLICT (id) DO UPDATE SET value=EXCLUDED.value, metric_date=EXCLUDED.metric_date
        """, (mid, actor, name, value, unit, TODAY, quote))
    
    # === PROMISES ===
    promises = [
        ("promise-deo", "actor-owner", "actor-arisha", "order deodorants", None, "pending", "заказать дезодоранты"),
        ("promise-ins", "actor-arisha", "actor-owner", "insurance will be free", None, "pending", "страховка будет бесплатной"),
        ("promise-leha", "actor-leha-kosenko", "actor-owner", "send report", None, "pending", "обещал скинуть отчет до пятницы"),
    ]
    
    for pid, fr, to, content, deadline, status, quote in promises:
        cur.execute("""
            INSERT INTO promises (id, from_actor, to_actor, content, deadline, status, source_quote, source_date, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0.9)
            ON CONFLICT (id) DO UPDATE SET status=EXCLUDED.status
        """, (pid, fr, to, content, deadline, status, quote, TODAY))
    
    # === DECISIONS ===
    decisions = [
        ("dec-postgres", ["actor-owner"], "Use PostgreSQL in Docker for graph storage", "chosen over Neo4j", "Агент решил что PostgreSQL эффективнее"),
        ("dec-english", ["actor-owner"], "All internal JARVIS files in English (saves ~30% tokens)", "token economy", "сделай все файлы на английском"),
        ("dec-gemini-embed", ["actor-owner"], "Use Gemini Embeddings (gemini-embedding-001)", "semantic search", "Adopted Google Gemini Embeddings"),
        ("dec-markdown", ["actor-owner"], "Context graph in markdown files + PostgreSQL", "not Neo4j", "Build context graph using markdown files"),
        ("dec-claude", ["actor-owner"], "Switch to Claude Opus 4.6 as primary model", "better reasoning", "модель Claude Opus 4.6"),
        ("dec-cyb-os", ["actor-owner"], "Adopt cybOS architecture for JARVIS", "structured memory", "cybOS и Граф Контекста"),
    ]
    
    for did, actors, content, context, quote in decisions:
        cur.execute("""
            INSERT INTO decisions (id, actors, content, context, decision_date, source_quote, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, 0.9)
            ON CONFLICT (id) DO UPDATE SET content=EXCLUDED.content
        """, (did, actors, content, context, TODAY, quote))
    
    # === PLANS ===
    plans = [
        ("plan-postgres", "actor-owner", "PostgreSQL in Docker for graph + visualization", None, "active", "PostgreSQL граф — хранение сущностей"),
        ("plan-obsidian", "actor-owner", "Integrate Obsidian vault for voice→transcription→notes", None, "active", "Obsidian — Голос → транскрипция → заметка"),
        ("plan-baby", "actor-arisha", "Baby due before September 2026", "2026-09-01", "active", "ребенок родится до сентября"),
        ("plan-support", "actor-arisha", "Write to insurance support", None, "active", "написать в поддержку"),
        ("plan-collage", "actor-owner", "Make photo collage and send to everyone", None, "active", "сделать коллаж из фотографий"),
        ("plan-appeal", "actor-owner", "Submit appeal", None, "active", "подать апелляцию"),
        ("plan-mcp", "actor-owner", "Wrap graph as MCP Server for agent access", None, "active", "обернуть граф как MCP Server"),
        ("plan-semantic", "actor-owner", "Implement semantic search over dialogs", None, "active", "Семантический поиск по диалогам"),
    ]
    
    for pid, actor, content, target, status, quote in plans:
        cur.execute("""
            INSERT INTO plans (id, actor_id, content, target_date, status, source_quote, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, 0.9)
            ON CONFLICT (id) DO UPDATE SET content=EXCLUDED.content, status=EXCLUDED.status
        """, (pid, actor, content, target, status, quote))
    
    # === ACTOR UPDATES ===
    cur.execute("""UPDATE actors SET context='wife, pregnant ~12.3 weeks, chat Мой Мир❤️, insurance issues, priority contact' 
                   WHERE id='actor-arisha'""")
    cur.execute("""UPDATE actors SET context='military serviceman, Serpukhov, building JARVIS bot, income ~3000 RUB mentioned'
                   WHERE id='actor-owner'""")
    cur.execute("""UPDATE actors SET last_seen=%s WHERE id IN ('actor-owner','actor-arisha','actor-leha-kosenko')""", (TODAY,))
    
    conn.commit()
    conn.close()
    print(f"✓ Compressed: {len(metrics)} metrics, {len(promises)} promises, {len(decisions)} decisions, {len(plans)} plans")

def export_full_graph():
    """Export comprehensive graph with all entity types."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    nodes = []
    links = []
    id_map = {}
    idx = 0
    
    # Actors
    cur.execute("SELECT id, canonical_name, role, context, last_seen FROM actors")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[1], "group": "Actor", "role": row[2] or "", 
                       "context": row[3] or "", "last_seen": str(row[4]) if row[4] else ""})
        id_map[row[0]] = idx
        idx += 1
    
    # Promises
    cur.execute("SELECT id, from_actor, to_actor, content, status, confidence, source_quote FROM promises")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[3], "group": "Promise", "status": row[4], 
                       "confidence": row[5], "source_quote": row[6] or ""})
        pidx = idx
        id_map[row[0]] = idx
        idx += 1
        # Link from_actor → promise
        for aid, aidx in id_map.items():
            if aid == row[1]:
                links.append({"source": aidx, "target": pidx, "relation": "PROMISED"})
            if aid == row[2]:
                links.append({"source": pidx, "target": aidx, "relation": "TO"})
    
    # Decisions
    cur.execute("SELECT id, content, context, confidence, source_quote FROM decisions")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[1][:50], "group": "Decision", 
                       "context": row[2] or "", "confidence": row[3], "source_quote": row[4] or ""})
        didx = idx
        id_map[row[0]] = idx
        idx += 1
        # Link to owner
        if "actor-owner" in id_map:
            links.append({"source": id_map["actor-owner"], "target": didx, "relation": "DECIDED"})
    
    # Metrics
    cur.execute("SELECT id, actor_id, name, value, unit, confidence, source_quote FROM metrics")
    for row in cur.fetchall():
        label = f"{row[2]}: {row[3]} {row[4]}"
        nodes.append({"id": idx, "name": label[:50], "group": "Metric", 
                       "confidence": row[5], "source_quote": row[6] or ""})
        midx = idx
        id_map[row[0]] = idx
        idx += 1
        # Link to actor
        if row[1] and row[1] in id_map:
            links.append({"source": id_map[row[1]], "target": midx, "relation": "MEASURED"})
    
    # Plans
    cur.execute("SELECT id, actor_id, content, status, confidence, source_quote FROM plans")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[2][:50], "group": "Plan", "status": row[3], 
                       "confidence": row[4], "source_quote": row[5] or ""})
        plidx = idx
        id_map[row[0]] = idx
        idx += 1
        if row[1] and row[1] in id_map:
            links.append({"source": id_map[row[1]], "target": plidx, "relation": "PLANS"})
    
    # JARVIS capabilities (from graph_nodes with label='Skill')
    cur.execute("SELECT name, description FROM graph_nodes WHERE label='Skill'")
    jarvis_idx = id_map.get("actor-jarvis")
    for row in cur.fetchall():
        nodes.append({"id": idx, "name": row[0], "group": "Skill", "context": row[1] or ""})
        if jarvis_idx is not None:
            links.append({"source": jarvis_idx, "target": idx, "relation": "HAS_SKILL"})
        idx += 1
    
    # KNOWS relationships between actors
    if "actor-owner" in id_map and "actor-arisha" in id_map:
        links.append({"source": id_map["actor-owner"], "target": id_map["actor-arisha"], "relation": "SPOUSE"})
    if "actor-owner" in id_map and "actor-evgeniya" in id_map:
        links.append({"source": id_map["actor-owner"], "target": id_map["actor-evgeniya"], "relation": "SON_OF"})
    if "actor-owner" in id_map and "actor-andrey" in id_map:
        links.append({"source": id_map["actor-owner"], "target": id_map["actor-andrey"], "relation": "BROTHER"})
    if "actor-owner" in id_map and "actor-leha-kosenko" in id_map:
        links.append({"source": id_map["actor-owner"], "target": id_map["actor-leha-kosenko"], "relation": "FRIEND"})
    if "actor-owner" in id_map and jarvis_idx is not None:
        links.append({"source": id_map["actor-owner"], "target": jarvis_idx, "relation": "OWNS"})
    
    conn.close()
    
    graph = {"nodes": nodes, "links": links}
    with open("/root/.openclaw/workspace/graph_data.json", "w") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Exported: {len(nodes)} nodes, {len(links)} edges")
    return len(nodes), len(links)

def build_embeddings():
    """Generate embeddings for all entities for semantic search."""
    import google.generativeai as genai
    from key_manager import KeyManager
    
    manager = KeyManager()
    key = manager.get_key()
    genai.configure(api_key=key)
    
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    
    # Collect all entities
    entities = []
    
    cur.execute("SELECT id, canonical_name, context FROM actors")
    for row in cur.fetchall():
        entities.append(("actor", row[0], f"Actor: {row[1]}. {row[2] or ''}"))
    
    cur.execute("SELECT id, content, source_quote FROM promises")
    for row in cur.fetchall():
        entities.append(("promise", row[0], f"Promise: {row[1]}. Quote: {row[2] or ''}"))
    
    cur.execute("SELECT id, content, source_quote FROM decisions")
    for row in cur.fetchall():
        entities.append(("decision", row[0], f"Decision: {row[1]}. Quote: {row[2] or ''}"))
    
    cur.execute("SELECT id, name, value, unit FROM metrics")
    for row in cur.fetchall():
        entities.append(("metric", row[0], f"Metric: {row[1]} = {row[2]} {row[3]}"))
    
    cur.execute("SELECT id, content, source_quote FROM plans")
    for row in cur.fetchall():
        entities.append(("plan", row[0], f"Plan: {row[1]}. Quote: {row[2] or ''}"))
    
    print(f"  Generating embeddings for {len(entities)} entities...")
    
    # Batch embed
    texts = [e[2] for e in entities]
    
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=texts,
            task_type="RETRIEVAL_DOCUMENT"
        )
        embeddings = result['embedding']
        
        for i, (etype, eid, content) in enumerate(entities):
            emb = embeddings[i]
            cur.execute("""
                INSERT INTO entity_embeddings (id, entity_type, content, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET embedding=EXCLUDED.embedding, content=EXCLUDED.content
            """, (eid, etype, content, emb))
        
        conn.commit()
        print(f"✓ Embedded {len(entities)} entities")
    except Exception as e:
        print(f"❌ Embedding error: {e}")
    
    conn.close()

def semantic_search(query, top_k=5):
    """Search graph entities semantically."""
    import google.generativeai as genai
    from key_manager import KeyManager
    
    manager = KeyManager()
    genai.configure(api_key=manager.get_key())
    
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=query,
        task_type="RETRIEVAL_QUERY"
    )
    query_emb = result['embedding']
    
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, entity_type, content, 1 - (embedding <=> %s::vector) as similarity
        FROM entity_embeddings
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (query_emb, query_emb, top_k))
    
    results = []
    for row in cur.fetchall():
        results.append({"id": row[0], "type": row[1], "content": row[2], "similarity": round(row[3], 3)})
    
    conn.close()
    return results


if __name__ == "__main__":
    print("🚀 JARVIS: Full Context Compression")
    print("=" * 40)
    
    # Step 1: Ensure schema
    ensure_embeddings_table()
    
    # Step 2: Add JARVIS to graph
    add_jarvis_to_graph()
    
    # Step 3: Compress all session context into DB
    compress_session_context()
    
    # Step 4: Export graph
    n, e = export_full_graph()
    
    # Step 5: Build embeddings for semantic search
    build_embeddings()
    
    # Step 6: Test semantic search
    print("\n--- Semantic Search Test ---")
    results = semantic_search("что обещала жена?")
    for r in results:
        print(f"  [{r['similarity']}] {r['type']}: {r['content']}")
    
    print(f"\n🏆 Done! Graph: {n} nodes, {e} edges")
