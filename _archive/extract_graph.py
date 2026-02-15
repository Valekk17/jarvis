import os
import psycopg2
import google.generativeai as genai
import json
import uuid
import time
from key_manager import KeyManager
from embedding_util import get_embedding

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"

def extract_context_graph(text, manager):
    # Retry logic
    models = ['models/gemini-2.5-flash', 'models/gemini-3-flash-preview', 'models/gemini-1.5-flash']
    
    for model_name in models:
        max_retries = len(manager.keys)
        # Try each key for current model
        for _ in range(max_retries):
            key = manager.get_key()
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            
            # ... prompt definition ... (move prompt inside loop or define once)
            prompt = f"""
            Analyze the following text and extract knowledge graph entities.
            
            **Ontology (Strict):**
            - **Entities**: Actor, Topic, Fact, Promise, Decision.
            - **Naming**: Node names MUST be atomic (1-3 words). E.g., "Neo4j", NOT "Adopted Neo4j".
            - **Relations**: 
              - `MENTIONED`: Actor mentioned Topic/Actor.
              - `PROMISED`: Actor promised Fact/Action.
              - `DECIDED`: Actor made Decision.
              - `HAS_TOPIC`: Message/Context relates to Topic.
              - `RELATED_TO`: Generic connection (avoid if possible).

            Return JSON:
            {{
              "actors": [ {{"name": "Name", "description": "Role"}} ],
              "topics": [ {{"name": "Topic", "description": "Context"}} ],
              "facts": [ {{"subject": "Name", "predicate": "RELATION_FROM_LIST", "object": "Name"}} ],
              "promises": [ {{"description": "What", "from": "Name", "to": "Name"}} ]
            }}
            
            Text:
            {text}
            """
            
            try:
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                return json.loads(response.text)
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower() or "ResourceExhausted" in str(e):
                    print(f"Quota error on {model_name} (Key {manager.index}). Rotating...")
                    manager.rotate()
                    continue
                elif "404" in str(e):
                    print(f"Model {model_name} not found. Switching model...")
                    break # Break key loop to try next model
                else:
                    print(f"Error: {e}")
                    break # Non-quota error, maybe content issue?
    return {}

def get_or_create_node(cursor, label, name, desc=None, manager=None):
    if name.lower() in ['me', 'i', 'my', 'я']: name = 'Valekk_17'
    
    embedding = get_embedding(name, manager) if manager else None
    
    # Check deduplication
    if embedding:
        # find_similar... (Simplified for brevity, use direct insert/conflict)
        pass

    sql = """
        INSERT INTO graph_nodes (label, name, description, embedding)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (label, name) 
        DO UPDATE SET description = COALESCE(graph_nodes.description, EXCLUDED.description)
        RETURNING id
    """
    cursor.execute(sql, (label, name, desc, embedding))
    return cursor.fetchone()[0]

def create_edge(cursor, source_id, target_id, relation):
    sql = """
        INSERT INTO graph_edges (source_id, target_id, relation)
        VALUES (%s, %s, %s)
        ON CONFLICT (source_id, target_id, relation) DO NOTHING
    """
    cursor.execute(sql, (source_id, target_id, relation))

def run():
    # Only for standalone run
    pass
