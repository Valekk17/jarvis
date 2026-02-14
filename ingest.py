import os
import psycopg2
import psycopg2.extras
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
import time
from key_manager import KeyManager

# Configuration
PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
MEMORY_FILE = "/root/.openclaw/workspace/MEMORY.md"

# Use 'models/gemini-embedding-001' or 'models/text-embedding-004'
EMBEDDING_MODEL = "models/gemini-embedding-001" 

def get_embedding(text, manager):
    # Retry logic
    max_retries = len(manager.keys) * 2
    for attempt in range(max_retries):
        key = manager.get_key()
        genai.configure(api_key=key)
        
        try:
            text = text.replace("\n", " ")
            # output_dimensionality only for 004
            if "004" in EMBEDDING_MODEL:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document",
                    title="Embedding of chunk",
                    output_dimensionality=768
                )
            else:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document",
                    title="Embedding of chunk"
                )
            return result['embedding']
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "ResourceExhausted" in str(e):
                print(f"Error (429/Quota) with key index {manager.index}: {e}. Rotating...")
                manager.rotate()
                continue
            else:
                print(f"Non-Quota Error: {e}")
                if attempt > 1: return []
                continue
    return []

def ingest_memory():
    manager = KeyManager()
    
    # 1. Connect to Postgres
    try:
        conn = psycopg2.connect(PG_DSN)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Postgres Connection Error: {e}")
        return

    # 2. Read File
    if not os.path.exists(MEMORY_FILE):
        print(f"File not found: {MEMORY_FILE}")
        return
    
    with open(MEMORY_FILE, "r") as f:
        text = f.read()

    # 3. Split Text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(text)
    print(f"Found {len(chunks)} chunks.")

    # 4. Process Chunks
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        embedding = get_embedding(chunk, manager)
        
        if not embedding:
            print(f"Skipping chunk {i} due to embedding failure.")
            continue
            
        # Check dimension (should be 768 for gemini-embedding-001)
        if len(embedding) != 768:
            print(f"Warning: Expected 768 dim, got {len(embedding)}")
            continue

        # Insert into DB
        sql = """
            INSERT INTO memory_chunks (id, content, embedding, metadata)
            VALUES (%s, %s, %s, %s)
        """
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        metadata = {"source": "MEMORY.md", "chunk_index": i, "created_at": timestamp}
        cursor.execute(sql, (str(uuid.uuid4()), chunk, embedding, psycopg2.extras.Json(metadata)))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Ingestion Complete.")

if __name__ == "__main__":
    ingest_memory()
