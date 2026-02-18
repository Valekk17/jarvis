#!/usr/bin/env python3
"""
JARVIS Unified Context Graph System
====================================
Single entry point for all graph operations.
Source of truth: PostgreSQL + jarvis/memory/*.md

Commands:
  python jarvis_system.py collect    — Collect from Telegram + extract entities
  python jarvis_system.py search Q   — Semantic search
  python jarvis_system.py status     — Graph health report
  python jarvis_system.py export     — Export for D3 visualization
  python jarvis_system.py rebuild-md — Rebuild all md files from DB
  python jarvis_system.py decay      — Apply temporal decay to stale data
"""

import sys
import os
import json
import psycopg2
from datetime import date, datetime

WORKSPACE = "/root/.openclaw/workspace"
JARVIS_DIR = os.path.join(WORKSPACE, "jarvis")
PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
TODAY = date.today().isoformat()

# Actor resolution map
ACTOR_MAP = {
    "valekk": "actor-owner", "valekk_17": "actor-owner", "я": "actor-owner",
    "me": "actor-owner", "valek": "actor-owner",
    "arisha": "actor-arisha", "ариша": "actor-arisha", "жена": "actor-arisha",
    "wife": "actor-arisha", "мой мир❤️": "actor-arisha", "мой мир": "actor-arisha",
    "leha": "actor-leha-kosenko", "леха": "actor-leha-kosenko", "лёха": "actor-leha-kosenko",
    "alexey kosenko": "actor-leha-kosenko", "косенко": "actor-leha-kosenko",
    "мама": "actor-evgeniya", "evgeniya": "actor-evgeniya",
    "андрей": "actor-andrey", "брат": "actor-andrey",
}

def resolve_actor(name):
    return ACTOR_MAP.get(name.lower().strip(), name)


def cmd_status():
    """Graph health report with temporal decay."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    today = date.today()

    print("🏆 JARVIS Context Graph — Status")
    print("━" * 35)

    totals = {}
    for table in ['actors', 'promises', 'decisions', 'metrics', 'plans']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        totals[table] = cur.fetchone()[0]
        print(f"  {table:12s}: {totals[table]}")

    cur.execute("SELECT COUNT(*) FROM entity_embeddings")
    emb = cur.fetchone()[0]
    print(f"  {'embeddings':12s}: {emb}")

    # Active promises
    cur.execute("SELECT COUNT(*) FROM promises WHERE status='pending'")
    active = cur.fetchone()[0]
    print(f"\n📝 Active Promises: {active}")

    # Stale metrics (>90 days)
    cur.execute("SELECT COUNT(*) FROM metrics WHERE metric_date < CURRENT_DATE - INTERVAL '90 days'")
    stale = cur.fetchone()[0]
    if stale > 0:
        print(f"⚠️  Stale Metrics (>90d): {stale}")

    # Overdue promises
    cur.execute("SELECT id, content, deadline FROM promises WHERE status='pending' AND deadline IS NOT NULL AND deadline::date < CURRENT_DATE")
    overdue = cur.fetchall()
    if overdue:
        print(f"\n🔴 Overdue Promises:")
        for p in overdue:
            print(f"  - {p[1]} (deadline: {p[2]})")

    conn.close()
    print(f"\n✓ Graph healthy. Total entities: {sum(totals.values())}")


def cmd_search(query):
    """Semantic search via pgvector."""
    # Import here to avoid loading heavy deps for other commands
    from embedding_util import get_embedding
    from key_manager import KeyManager
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()

    manager = KeyManager()
    embedding = get_embedding(query, manager)
    if not embedding:
        print("❌ Failed to generate embedding")
        return

    cur.execute("""
        SELECT entity_type, id, content, 
               1 - (embedding <=> %s::vector) as similarity
        FROM entity_embeddings
        WHERE 1 - (embedding <=> %s::vector) > 0.5
        ORDER BY embedding <=> %s::vector
        LIMIT 10
    """, (str(embedding), str(embedding), str(embedding)))

    results = cur.fetchall()
    if not results:
        print("No results found.")
        return

    print(f"🔍 Results for: \"{query}\"")
    print("━" * 40)
    for r in results:
        print(f"  [{r[3]:.3f}] {r[0]}: {r[2][:80]}")

    conn.close()


def cmd_rebuild_md():
    """Rebuild all jarvis/memory/*.md files from PostgreSQL."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()

    # Promises
    cur.execute("SELECT id, from_actor, to_actor, content, deadline, status, source_quote, source_date, confidence FROM promises ORDER BY status, id")
    rows = cur.fetchall()
    md = "# Promises\n\n"
    for r in rows:
        md += f"## {r[0]}\n- from: {r[1]}\n- to: {r[2]}\n- content: {r[3]}\n- deadline: {r[4] or 'null'}\n- status: {r[5]}\n- source_quote: \"{r[6]}\"\n- source_date: {r[7]}\n- confidence: {r[8]}\n\n"
    with open(os.path.join(JARVIS_DIR, "memory/promises.md"), "w") as f:
        f.write(md)
    print(f"  ✓ promises.md ({len(rows)} entries)")

    # Decisions
    cur.execute("SELECT id, content, decision_date, source_quote, confidence FROM decisions ORDER BY id")
    rows = cur.fetchall()
    md = "# Decisions\n\n"
    for r in rows:
        md += f"## {r[0]}\n- content: {r[1]}\n- date: {r[2]}\n- source_quote: \"{r[3]}\"\n- confidence: {r[4]}\n\n"
    with open(os.path.join(JARVIS_DIR, "memory/decisions.md"), "w") as f:
        f.write(md)
    print(f"  ✓ decisions.md ({len(rows)} entries)")

    # Metrics
    cur.execute("SELECT id, name, value, unit, metric_date, confidence FROM metrics ORDER BY metric_date DESC")
    rows = cur.fetchall()
    md = "# Metrics\n\n"
    for r in rows:
        days_old = (date.today() - r[4]).days if r[4] else 0
        decay = r[5] / (1 + days_old / 90)
        status = "✓" if decay > 0.5 else "⚠ stale"
        md += f"## {r[0]}\n- name: {r[1]}\n- value: {r[2]} {r[3]}\n- date: {r[4]}\n- confidence: {r[5]}\n- decayed_conf: {decay:.2f} ({status})\n\n"
    with open(os.path.join(JARVIS_DIR, "memory/metrics.md"), "w") as f:
        f.write(md)
    print(f"  ✓ metrics.md ({len(rows)} entries)")

    # Plans
    cur.execute("SELECT id, content, status, source_quote, target_date, confidence FROM plans ORDER BY status, id")
    rows = cur.fetchall()
    md = "# Plans\n\n"
    for r in rows:
        md += f"## {r[0]}\n- content: {r[1]}\n- status: {r[2]}\n- source_quote: \"{r[3]}\"\n- target_date: {r[4] or 'null'}\n- confidence: {r[5]}\n\n"
    with open(os.path.join(JARVIS_DIR, "memory/plans.md"), "w") as f:
        f.write(md)
    print(f"  ✓ plans.md ({len(rows)} entries)")

    # Actors
    cur.execute("SELECT id, canonical_name, aliases, role, context FROM actors ORDER BY id")
    rows = cur.fetchall()
    md = "# Actor Registry\n\n"
    for r in rows:
        md += f"## {r[0]}\n- canonical_name: {r[1]}\n- aliases: {r[2]}\n- role: {r[3]}\n- context: {r[4]}\n\n"
    with open(os.path.join(JARVIS_DIR, "memory/actors.md"), "w") as f:
        f.write(md)
    print(f"  ✓ actors.md ({len(rows)} entries)")

    conn.close()
    print("✓ All md files rebuilt from DB")


def cmd_decay():
    """Apply temporal decay: expire old promises, flag stale metrics."""
    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()

    # Expire promises with passed deadlines
    cur.execute("""
        UPDATE promises SET status='expired' 
        WHERE status='pending' AND deadline IS NOT NULL AND deadline::date < CURRENT_DATE
        RETURNING id, content
    """)
    expired = cur.fetchall()
    for e in expired:
        print(f"  ⏰ Expired: {e[1]}")

    # Flag stale metrics (>365 days)
    cur.execute("""
        DELETE FROM metrics 
        WHERE metric_date < CURRENT_DATE - INTERVAL '365 days'
        RETURNING name
    """)
    deleted = cur.fetchall()
    for d in deleted:
        print(f"  🗑️ Removed stale metric: {d[0]}")

    conn.commit()
    conn.close()

    if not expired and not deleted:
        print("  ✓ No decay needed")


def cmd_export():
    """Export graph for D3 visualization."""
    os.system(f"cd {WORKSPACE} && python3 export_d3.py")


def cmd_collect():
    """Run the collector."""
    os.system(f"cd {WORKSPACE} && .venv/bin/python collector_cron.py")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "status":
        cmd_status()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: jarvis_system.py search <query>")
            sys.exit(1)
        cmd_search(" ".join(sys.argv[2:]))
    elif cmd == "rebuild-md":
        cmd_rebuild_md()
    elif cmd == "decay":
        cmd_decay()
    elif cmd == "export":
        cmd_export()
    elif cmd == "collect":
        cmd_collect()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
