import psycopg2
from key_manager import KeyManager
from embedding_util import get_embedding
from extract_graph import get_or_create_node

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"

def test():
    manager = KeyManager()
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    # 1. Create Alexander
    print("Creating 'Alexander'...")
    id1 = get_or_create_node(cursor, 'Actor', 'Alexander', 'The Great', manager)
    conn.commit()
    print(f"Created ID: {id1}")
    
    # 2. Try creating Sasha
    print("Creating 'Sasha' (Should merge)...")
    id2 = get_or_create_node(cursor, 'Actor', 'Sasha', 'Diminutive', manager)
    conn.commit()
    print(f"Result ID: {id2}")
    
    # Debug Similarity
    emb1 = get_embedding('Alexander', manager)
    emb2 = get_embedding('Sasha', manager)
    cursor.execute("SELECT 1 - (%s::vector <=> %s::vector)", (emb1, emb2))
    print(f"Direct Similarity: {cursor.fetchone()[0]}")
    
    if id1 == id2:
        print("SUCCESS: Merged!")
    else:
        print("FAILURE: Created new node.")
        
    conn.close()

if __name__ == "__main__":
    test()
