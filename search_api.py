import os
import psycopg2
import google.generativeai as genai
from neo4j import GraphDatabase
import json

# Configuration
PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "jarvis_neo4j_password")
API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=API_KEY)

def get_embedding(text):
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
        output_dimensionality=768
    )
    return result['embedding']

def search(query):
    print(f"Searching for: '{query}'")
    
    # 1. Generate Embedding
    embedding = get_embedding(query)
    
    # 2. Vector Search (Postgres)
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    sql = """
        SELECT content, metadata, 1 - (embedding <=> %s::vector) as similarity
        FROM memory_chunks
        ORDER BY embedding <=> %s::vector
        LIMIT 3
    """
    cursor.execute(sql, (embedding, embedding))
    chunks = cursor.fetchall()
    conn.close()
    
    print("\n--- Semantic Results ---")
    for row in chunks:
        print(f"[Score: {row[2]:.4f}] {row[0][:100]}...")

    # 3. Graph Search (Neo4j)
    # Simple keyword match or vector match on nodes?
    # Let's do simple keyword match on nodes for now.
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        cypher = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($search_text) OR toLower(n.description) CONTAINS toLower($search_text)
        RETURN n.name, n.description, labels(n)
        LIMIT 5
        """
        result = session.run(cypher, search_text=query)
        print("\n--- Graph Results ---")
        for record in result:
            print(f"[{record['labels(n)'][0]}] {record['n.name']}: {record['n.description']}")
    driver.close()

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "strategic objectives"
    search(query)
