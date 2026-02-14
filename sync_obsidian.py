import os
import psycopg2
import yaml
import re

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
VAULT_DIR = "/root/.openclaw/workspace"
ENTITIES_DIR = os.path.join(VAULT_DIR, "Entities")

def clean_filename(s):
    return re.sub(r'[^\w\s-]', '', s).strip()

def sync():
    if not os.path.exists(ENTITIES_DIR):
        os.makedirs(ENTITIES_DIR)

    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    # Get all nodes
    cursor.execute("SELECT id, label, name, description FROM graph_nodes")
    nodes = cursor.fetchall()
    
    print(f"Syncing {len(nodes)} nodes to Obsidian...")
    
    for node in nodes:
        nid, label, name, desc = node
        
        # Create folder for Label (e.g., Entities/Actor)
        label_dir = os.path.join(ENTITIES_DIR, label)
        if not os.path.exists(label_dir):
            os.makedirs(label_dir)
            
        filename = f"{clean_filename(name)}.md"
        filepath = os.path.join(label_dir, filename)
        
        # Get relationships
        cursor.execute("""
            SELECT r.relation, t.name 
            FROM graph_edges r 
            JOIN graph_nodes t ON r.target_id = t.id 
            WHERE r.source_id = %s
        """, (nid,))
        outgoing = cursor.fetchall()
        
        cursor.execute("""
            SELECT r.relation, s.name 
            FROM graph_edges r 
            JOIN graph_nodes s ON r.source_id = s.id 
            WHERE r.target_id = %s
        """, (nid,))
        incoming = cursor.fetchall()

        # Frontmatter
        frontmatter = {
            "id": str(nid),
            "type": label,
            "tags": [label],
            "aliases": [name]
        }
        
        content = f"---\n{yaml.dump(frontmatter)}---\n\n# {name}\n\n{desc or ''}\n\n## Relationships\n"
        
        if outgoing:
            content += "### Outgoing\n"
            for rel, target in outgoing:
                content += f"- **{rel}** -> [[{target}]]\n"
                
        if incoming:
            content += "\n### Incoming\n"
            for rel, source in incoming:
                content += f"- [[{source}]] -> **{rel}**\n"

        with open(filepath, "w") as f:
            f.write(content)
            
    conn.close()
    print("Obsidian Sync Complete.")

if __name__ == "__main__":
    sync()
