import os
import re
from datetime import datetime

MEMORY_DIR = "/root/.openclaw/workspace/memory"
GRAPH_FILE = os.path.join(MEMORY_DIR, "context_graph.md")
TASKS_FILE = os.path.join(MEMORY_DIR, "Tasks.md")

def generate_view():
    if not os.path.exists(GRAPH_FILE):
        return

    with open(GRAPH_FILE) as f:
        lines = f.readlines()

    tasks_by_actor = {}
    
    for line in lines:
        if "[active]" in line or "[pending]" in line:
            # Parse
            # - [status] Content | Actor: ... | ...
            # Extract content
            clean = line.strip()[2:] # remove '- '
            parts = clean.split('|')
            status_content = parts[0].strip()
            
            # Remove status tag
            content = re.sub(r'^\[.*?\] ', '', status_content).strip()
            
            # Find Actor
            actor = "Other"
            for p in parts[1:]:
                if "Actor:" in p:
                    actor = p.split("Actor:")[1].strip()
                    # Remove ID
                    actor = re.sub(r' \(ID: .*?\)', '', actor)
                    break
                if "From:" in p:
                     # Promise: From X -> To Y
                     # Usually we group by "From" (who promised) or "To" (who benefits)?
                     # Or "Assigned to"?
                     # Let's use "From" as the actor responsible.
                     # Format: From: X -> To: Y
                     from_part = p.split("From:")[1].strip()
                     if "->" in from_part:
                         actor = from_part.split("->")[0].strip()
                     else:
                         actor = from_part
                     actor = re.sub(r' \(ID: .*?\)', '', actor)
                     break
            
            if actor not in tasks_by_actor:
                tasks_by_actor[actor] = []
            
            tasks_by_actor[actor].append(content)

    # Write Tasks.md
    with open(TASKS_FILE, "w") as f:
        f.write(f"# 📋 Active Tasks\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        
        # Sort actors (Valekk first)
        actors = sorted(tasks_by_actor.keys())
        # Move Valekk_17 to top
        if "Valekk_17" in actors:
            actors.remove("Valekk_17")
            actors.insert(0, "Valekk_17")
        
        for actor in actors:
            # Friendly name
            name = actor
            if name == "Valekk_17": name = "Me (Valekk)"
            if name == "Evgeniya Kovalkova": name = "Mom"
            if name == "Andrey Kovalkov": name = "Brother"
            if name == "Alexey Kosenko": name = "Leha"
            
            f.write(f"## {name}\n")
            for task in tasks_by_actor[actor]:
                f.write(f"- [ ] {task}\n")
            f.write("\n")
            
    print(f"Generated {TASKS_FILE}")

if __name__ == "__main__":
    generate_view()
