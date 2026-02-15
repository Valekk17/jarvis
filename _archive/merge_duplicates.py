import psycopg2
import time

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"

def merge():
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    print("Fetching all nodes...")
    cursor.execute("SELECT id, name, label FROM graph_nodes WHERE embedding IS NOT NULL")
    nodes = cursor.fetchall()
    
    merged_count = 0
    
    print(f"Checking {len(nodes)} nodes for duplicates...")
    
    for i, node in enumerate(nodes):
        nid, name, label = node
        
        # Check if node still exists (might be merged already)
        cursor.execute("SELECT 1 FROM graph_nodes WHERE id = %s", (nid,))
        if not cursor.fetchone():
            continue
            
        # Find similar
        sql = """
            SELECT id, name, 1 - (embedding <=> (SELECT embedding FROM graph_nodes WHERE id = %s)) as sim
            FROM graph_nodes
            WHERE id != %s AND label = %s AND embedding IS NOT NULL
            ORDER BY embedding <=> (SELECT embedding FROM graph_nodes WHERE id = %s)
            LIMIT 5
        """
        cursor.execute(sql, (nid, nid, label, nid))
        candidates = cursor.fetchall()
        
        for cand in candidates:
            cid, cname, sim = cand
            if sim > 0.90: # Careful threshold
                print(f"Merging '{cname}' -> '{name}' (Sim: {sim:.4f})")
                
                # Handle Source Conflicts
                cursor.execute("""
                    DELETE FROM graph_edges e1 
                    WHERE source_id = %s 
                    AND EXISTS (SELECT 1 FROM graph_edges e2 WHERE e2.source_id = %s AND e2.target_id = e1.target_id AND e2.relation = e1.relation)
                """, (cid, nid))
                cursor.execute("UPDATE graph_edges SET source_id = %s WHERE source_id = %s", (nid, cid))

                # Handle Target Conflicts
                cursor.execute("""
                    DELETE FROM graph_edges e1 
                    WHERE target_id = %s 
                    AND EXISTS (SELECT 1 FROM graph_edges e2 WHERE e2.target_id = %s AND e2.source_id = e1.source_id AND e2.relation = e1.relation)
                """, (cid, nid))
                cursor.execute("UPDATE graph_edges SET target_id = %s WHERE target_id = %s", (nid, cid))
                
                # Delete Duplicate
                cursor.execute("DELETE FROM graph_nodes WHERE id = %s", (cid,))
                merged_count += 1
                conn.commit()
    
    conn.close()
    print(f"Merged {merged_count} duplicates.")

if __name__ == "__main__":
    merge()
