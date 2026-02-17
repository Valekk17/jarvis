import os

PRINCIPLES_FILE = "/root/.openclaw/workspace/memory/Principles.md"
GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"

def restore():
    if not os.path.exists(PRINCIPLES_FILE): return
    
    with open(PRINCIPLES_FILE) as f:
        lines = f.readlines()
        
    graph_lines = ["\n## Decisions\n"]
    
    current_category = "General"
    
    for line in lines:
        line = line.strip()
        if line.startswith("## "):
            current_category = line[3:] # Family, Personal
        elif line.startswith("- [ ] "):
            content = line[6:]
            # Create graph entry
            # - Content | Actor: Valekk_17 | Relations: Category
            # To cluster them, we can link them to a "Principles" node in visualization
            # But in file, we store as Decision.
            
            # We'll use a special tag or just text.
            # "Category" acts as context.
            
            actor = "Valekk_17"
            if "Family" in current_category:
                actor = "Family" # Link to Family node
            
            graph_lines.append(f"- {content} | Actor: {actor} | Type: Principle\n")
            
    with open(GRAPH_FILE, "a") as f:
        f.writelines(graph_lines)
        
    print("Restored principles to graph.")

if __name__ == "__main__":
    restore()
