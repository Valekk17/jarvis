import os
import psycopg2
import psycopg2.extras
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid

# Configuration
PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
API_KEY = os.getenv("GOOGLE_API_KEY")
MEMORY_FILE = "/root/.openclaw/workspace/MEMORY.md"

if not API_KEY:
    print("Error: GOOGLE_API_KEY not found in environment.")
    exit(1)

genai.configure(api_key=API_KEY)

# Use 'models/embedding-001' or 'models/text-embedding-004'
EMBEDDING_MODEL = "models/gemini-embedding-001" 

def get_embedding(text):
    text = text.replace("\n", " ")
    # output_dimensionality=768 is default for 004, but let's be explicit if needed.
    # embedding-001 is 768 too.
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document",
        title="Embedding of chunk",
        output_dimensionality=768
    )
    return result['embedding']

def ingest_memory():
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
        try:
            embedding = get_embedding(chunk)
            
            # Check dimension
            if len(embedding) != 768:
                print(f"Warning: Expected 768 dim, got {len(embedding)}")
                continue

            # Insert into DB
            sql = """
                INSERT INTO memory_chunks (id, content, embedding, metadata)
                VALUES (%s, %s, %s, %s)
            """
            metadata = {"source": "MEMORY.md", "chunk_index": i}
            cursor.execute(sql, (str(uuid.uuid4()), chunk, embedding, psycopg2.extras.Json(metadata)))
        except Exception as e:
            print(f"Error embedding chunk {i}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Ingestion Complete.")

if __name__ == "__main__":
    ingest_memory()
