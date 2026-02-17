import os

GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"

def cleanup():
    if not os.path.exists(GRAPH_FILE): return
    with open(GRAPH_FILE) as f: lines = f.readlines()
    
    new_lines = []
    current_section = None
    deleted = 0
    
    for line in lines:
        if line.startswith("## "):
            current_section = line.strip()[3:].lower()
            new_lines.append(line)
            continue
            
        if current_section == "decisions" and line.startswith("- "):
            deleted += 1
            continue
        else:
            new_lines.append(line)
            
    with open(GRAPH_FILE, "w") as f:
        f.writelines(new_lines)
    print(f"Deleted {deleted} decisions.")

if __name__ == "__main__":
    cleanup()
