import json
import psycopg2

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"

def export_json():
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, label, name, description FROM graph_nodes")
    nodes = [{"id": str(r[0]), "group": r[1], "name": r[2], "desc": r[3]} for r in cursor.fetchall()]
    
    cursor.execute("SELECT source_id, target_id, relation FROM graph_edges")
    links = [{"source": str(r[0]), "target": str(r[1]), "value": 1, "label": r[2]} for r in cursor.fetchall()]
    
    data = {"nodes": nodes, "links": links}
    
    with open("/root/.openclaw/workspace/graph_data.json", "w") as f:
        json.dump(data, f)
    
    conn.close()

if __name__ == "__main__":
    export_json()
