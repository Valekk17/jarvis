import os
import psycopg2
import google.generativeai as genai
from key_manager import KeyManager
from embedding_util import get_embedding

# Configuration
PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"

def search(query):
    manager = KeyManager()
    print(f"Searching for: '{query}'")
    
    # 1. Generate Embedding
    embedding = get_embedding(query, manager)
    if not embedding:
        print("Embedding failed.")
        return
    
    # 2. Vector Search (Postgres) with Temporal Decay
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    # Formula: Similarity * (1 / (1 + 0.1 * Days_Old))
    # Extract days from metadata->>'created_at'
    # Assume metadata->>'created_at' format is ISO string
    
    sql = """
        SELECT content, metadata, 
               (1 - (embedding <=> %s::vector)) as similarity,
               EXTRACT(DAY FROM (NOW() - (metadata->>'created_at')::timestamp)) as age_days,
               (1 - (embedding <=> %s::vector)) * (1.0 / (1.0 + 0.1 * GREATEST(0, EXTRACT(DAY FROM (NOW() - (metadata->>'created_at')::timestamp))))) as score
        FROM memory_chunks
        ORDER BY score DESC
        LIMIT 3
    """
    cursor.execute(sql, (embedding, embedding))
    chunks = cursor.fetchall()
    
    print("\n--- Semantic Results (Decayed) ---")
    for row in chunks:
        content = row[0]
        meta = row[1]
        sim = row[2]
        age = row[3]
        score = row[4]
        print(f"[Score: {score:.4f} | Sim: {sim:.4f} | Age: {age}d] {content[:100]}...")

    # 3. Graph Search (Graph Nodes) - Also Boost by Freshness?
    # graph_nodes has created_at column.
    
    print("\n--- Graph Results ---")
    # Search graph nodes with similar logic? Or just simple name match for now.
    # We moved graph to Postgres.
    
    # Text Search on Nodes
    cursor.execute("""
        SELECT label, name, description, created_at
        FROM graph_nodes
        WHERE name ILIKE %s OR description ILIKE %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (f"%{query}%", f"%{query}%"))
    
    nodes = cursor.fetchall()
    for n in nodes:
        print(f"[{n[0]}] {n[1]}: {n[2]} (Created: {n[3]})")

    conn.close()

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "strategic objectives"
    search(query)
