import os

GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"

def cleanup():
    if not os.path.exists(GRAPH_FILE): return
    with open(GRAPH_FILE) as f: lines = f.readlines()
    
    new_lines = []
    
    for line in lines:
        # Mom Tasks
        if "Actor: Evgeniya Kovalkova" in line:
            if "V2RayTun" in line:
                line = line.replace("[active]", "[completed]").replace("[pending]", "[completed]")
                new_lines.append(line)
            else:
                continue # Delete others
        
        # Medical / Grandma
        elif "Medical Staff" in line or "лечить Бабулю" in line or "сделать снимок" in line:
            continue # Delete
            
        # JARVIS Tasks
        elif "Actor: JARVIS" in line:
            if any(k in line for k in [
                "Cron-based auto-collector",
                "Implement semantic search",
                "Integrate Obsidian",
                "Process all key Telegram chats",
                "Use Gemini 2.5 Pro",
                "voice_watcher.py"
            ]):
                line = line.replace("[active]", "[completed]").replace("[pending]", "[completed]")
            new_lines.append(line)
            
        else:
            new_lines.append(line)
            
    with open(GRAPH_FILE, "w") as f:
        f.writelines(new_lines)
    print("Cleanup done.")

if __name__ == "__main__":
    cleanup()
