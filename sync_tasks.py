import os
import re
from datetime import datetime

MEMORY_DIR = "/root/.openclaw/workspace/memory"
GRAPH_FILE = os.path.join(MEMORY_DIR, "context_graph.md")
TASKS_FILE = os.path.join(MEMORY_DIR, "Tasks.md")

def sync():
    if not os.path.exists(GRAPH_FILE): return

    # 1. Read User Changes from Tasks.md
    completed_contents = set()
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f:
            for line in f:
                if line.strip().startswith("- [x]"):
                    # Extract content
                    content = line.strip()[5:].strip() # remove "- [x] "
                    completed_contents.add(content)
    
    # 2. Update Graph
    if completed_contents:
        with open(GRAPH_FILE) as f:
            lines = f.readlines()
        
        new_lines = []
        updated_count = 0
        for line in lines:
            # Check if this line matches a completed task
            # Line format: - [active] Content | ...
            if "[active]" in line or "[pending]" in line:
                # Extract content part
                clean = line.strip()[2:] # remove '- '
                parts = clean.split('|')
                content_part = parts[0].strip()
                content = re.sub(r'^\[.*?\] ', '', content_part).strip()
                
                if content in completed_contents:
                    # Mark as completed
                    line = line.replace("[active]", "[completed]").replace("[pending]", "[completed]")
                    updated_count += 1
            
            new_lines.append(line)
            
        if updated_count > 0:
            with open(GRAPH_FILE, "w") as f:
                f.writelines(new_lines)
            print(f"Synced {updated_count} completed tasks from Tasks.md")

    # 3. Regenerate Tasks.md (User View)
    # Re-read graph (it might have updates from collector too)
    with open(GRAPH_FILE) as f:
        lines = f.readlines()

    tasks_by_actor = {}
    
    for line in lines:
        if "[active]" in line or "[pending]" in line:
            clean = line.strip()[2:]
            parts = clean.split('|')
            status_content = parts[0].strip()
            content = re.sub(r'^\[.*?\] ', '', status_content).strip()
            
            actor = "Other"
            for p in parts[1:]:
                if "Actor:" in p:
                    actor = p.split("Actor:")[1].strip()
                    actor = re.sub(r' \(ID: .*?\)', '', actor)
                    break
                if "From:" in p:
                     from_part = p.split("From:")[1].strip()
                     if "->" in from_part: actor = from_part.split("->")[0].strip()
                     else: actor = from_part
                     actor = re.sub(r' \(ID: .*?\)', '', actor)
                     break
            
            if actor not in tasks_by_actor: tasks_by_actor[actor] = []
            tasks_by_actor[actor].append(content)

    with open(TASKS_FILE, "w") as f:
        f.write(f"# 📋 Active Tasks\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        actors = sorted(tasks_by_actor.keys())
        if "Valekk_17" in actors:
            actors.remove("Valekk_17")
            actors.insert(0, "Valekk_17")
        
        for actor in actors:
            name = actor
            if name == "Valekk_17": name = "Me (Valekk)"
            if name == "Evgeniya Kovalkova": name = "Mom"
            if name == "Andrey Kovalkov": name = "Brother"
            if name == "Alexey Kosenko": name = "Leha"
            
            f.write(f"## {name}\n")
            for task in tasks_by_actor[actor]:
                f.write(f"- [ ] {task}\n")
            f.write("\n")

if __name__ == "__main__":
    sync()
