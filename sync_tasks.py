import os
import re
from datetime import datetime

MEMORY_DIR = "/root/.openclaw/workspace/memory"
GRAPH_FILE = os.path.join(MEMORY_DIR, "context_graph.md")
TASKS_DIR = os.path.join(MEMORY_DIR, "Tasks")
INBOX_FILE = os.path.join(TASKS_DIR, "Day.md")

os.makedirs(TASKS_DIR, exist_ok=True)

def get_all_task_files():
    files = []
    for f in os.listdir(TASKS_DIR):
        if f.endswith(".md"):
            files.append(os.path.join(TASKS_DIR, f))
    return files

def sync():
    if not os.path.exists(GRAPH_FILE): return

    # 1. Read User Changes (Completed)
    completed_contents = set()
    existing_contents = set()
    
    task_files = get_all_task_files()
    files_to_clean = {}

    for tf in task_files:
        with open(tf) as f:
            lines = f.readlines()
        
        kept_lines = []
        file_changed = False

        for line in lines:
            line_s = line.strip()
            if line_s.startswith("- [x]"):
                content = line_s[5:].strip()
                completed_contents.add(content)
                file_changed = True
            else:
                if line_s.startswith("- [ ]"):
                    content = line_s[5:].strip()
                    existing_contents.add(content)
                kept_lines.append(line)
        
        if file_changed:
            files_to_clean[tf] = kept_lines

    # Apply cleanup
    for tf, lines in files_to_clean.items():
        with open(tf, "w") as f:
            f.writelines(lines)
        print(f"Cleaned completed tasks from {os.path.basename(tf)}")

    # 2. Update Graph (Mark completed)
    if completed_contents:
        with open(GRAPH_FILE) as f: lines = f.readlines()
        new_lines = []
        updated_count = 0
        for line in lines:
            if "[active]" in line or "[pending]" in line:
                clean = line.strip()[2:]
                parts = clean.split('|')
                status_content = parts[0].strip()
                content = re.sub(r'^\[.*?\] ', '', status_content).strip()
                
                if content in completed_contents:
                    line = line.replace("[active]", "[completed]").replace("[pending]", "[completed]")
                    updated_count += 1
            new_lines.append(line)
            
        if updated_count > 0:
            with open(GRAPH_FILE, "w") as f: f.writelines(new_lines)
            print(f"Synced {updated_count} completed tasks from Obsidian")

    # 3. Add New Tasks (Inbox)
    with open(GRAPH_FILE) as f: lines = f.readlines()
    
    new_tasks = []
    for line in lines:
        if "[active]" in line or "[pending]" in line:
            clean = line.strip()[2:]
            parts = clean.split('|')
            status_content = parts[0].strip()
            content = re.sub(r'^\[.*?\] ', '', status_content).strip()
            
            if content not in existing_contents and content not in completed_contents:
                actor = ""
                for p in parts[1:]:
                    if "Actor:" in p: actor = p.split("Actor:")[1].strip()
                    if "From:" in p: 
                        from_p = p.split("From:")[1].strip()
                        if "->" in from_p: actor = from_p.split("->")[0].strip()
                        else: actor = from_p
                
                actor = re.sub(r' \(ID: .*?\)', '', actor)
                new_tasks.append((actor, content))

    if new_tasks:
        with open(INBOX_FILE, "a") as f:
            f.write(f"\n\n### New ({datetime.now().strftime('%H:%M')})\n")
            for actor, task in new_tasks:
                prefix = f"**{actor}**: " if actor and actor != "Valekk_17" else ""
                f.write(f"- [ ] {prefix}{task}\n")
        print(f"Added {len(new_tasks)} new tasks to {INBOX_FILE}")

if __name__ == "__main__":
    sync()
