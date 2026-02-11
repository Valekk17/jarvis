import os
import psycopg2
import google.generativeai as genai
from neo4j import GraphDatabase
import json
import time

# Configuration
PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "jarvis_neo4j_password")
API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

def extract_entities(text):
    prompt = f"""
    Extract knowledge graph entities and relationships from the following text.
    Return JSON format:
    {{
      "nodes": [
        {{"id": "unique_id", "label": "Person|Project|Concept|Event", "name": "Name", "description": "Short desc"}}
      ],
      "edges": [
        {{"source": "id_source", "target": "id_target", "relation": "RELATION_TYPE", "weight": 1.0}}
      ]
    }}
    Text: {text}
    """
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    try:
        return json.loads(response.text)
    except:
        return {"nodes": [], "edges": []}

def run():
    # 1. Connect PG
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    # 2. Connect Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
    # 3. Read Chunks
    cursor.execute("SELECT id, content FROM memory_chunks")
    rows = cursor.fetchall()
    print(f"Processing {len(rows)} chunks...")

    for row in rows:
        chunk_id, content = row
        print(f"Extracting from chunk {chunk_id}...")
        
        data = extract_entities(content)
        
        with driver.session() as session:
            # Create Nodes
            for node in data.get("nodes", []):
                cypher = f"""
                MERGE (n:{node['label']} {{id: $id}})
                SET n.name = $name, n.description = $desc
                """
                session.run(cypher, id=node['id'], name=node['name'], desc=node.get('description', ''))
            
            # Create Edges
            for edge in data.get("edges", []):
                cypher = f"""
                MATCH (s {{id: $source}}), (t {{id: $target}})
                MERGE (s)-[r:{edge['relation']}]->(t)
                SET r.weight = $weight
                """
                session.run(cypher, source=edge['source'], target=edge['target'], weight=edge.get('weight', 1.0))

    driver.close()
    conn.close()
    print("Graph Extraction Complete.")

if __name__ == "__main__":
    run()
