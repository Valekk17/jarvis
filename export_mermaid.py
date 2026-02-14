import psycopg2

PG_DSN = "postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db"

import base64

def export():
    conn = psycopg2.connect(PG_DSN)
    cursor = conn.cursor()
    
    mermaid = "graph TD\n"
    
    cursor.execute("SELECT id, label, name FROM graph_nodes LIMIT 50")
    rows = cursor.fetchall()
    nodes = {str(row[0]): row[2] for row in rows}
    
    for nid, name in nodes.items():
        clean_name = name.replace('"', '').replace('[', '').replace(']', '')
        nid_short = nid[:4]
        mermaid += f'    {nid_short}["{clean_name}"]\n'

    cursor.execute("SELECT source_id, target_id, relation FROM graph_edges LIMIT 50")
    edges = cursor.fetchall()
    
    for src, tgt, rel in edges:
        s = str(src)
        t = str(tgt)
        if s in nodes and t in nodes:
            src_short = s[:4]
            tgt_short = t[:4]
            mermaid += f'    {src_short} -->|{rel}| {tgt_short}\n'

    conn.close()
    
    encoded = base64.b64encode(mermaid.encode('utf-8')).decode('utf-8')
    url = f"https://mermaid.ink/img/{encoded}"
    print(f"Graph URL: {url}")

if __name__ == "__main__":
    export()
