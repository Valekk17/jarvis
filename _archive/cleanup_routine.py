import os

GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"
TASKS_FILE = "/root/.openclaw/workspace/memory/Tasks.md"

NOISE_KEYWORDS = [
    "поспать", "поесть", "столовую", "монеточку", "сделать дела", 
    "работать без обеда", "написать как закончит", "2 мин", "через 2 минуты"
]

def cleanup():
    if not os.path.exists(GRAPH_FILE): return
    
    # 1. Get checked tasks
    checked = set()
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f:
            for line in f:
                if "- [x]" in line:
                    content = line.strip()[5:].strip()
                    checked.add(content)

    print(f"Checked tasks: {len(checked)}")

    with open(GRAPH_FILE) as f:
        lines = f.readlines()
        
    new_lines = []
    deleted_count = 0
    
    for line in lines:
        keep = True
        
        # Check against checked
        for c in checked:
            if c in line:
                keep = False
                break
        
        # Check against keywords
        if keep:
            line_lower = line.lower()
            for kw in NOISE_KEYWORDS:
                if kw in line_lower:
                    keep = False
                    break
        
        if keep:
            new_lines.append(line)
        else:
            deleted_count += 1
            # print(f"Deleted: {line.strip()}")

    with open(GRAPH_FILE, "w") as f:
        f.writelines(new_lines)
        
    print(f"Cleanup done. Deleted {deleted_count} items (Checked + Similar Routine).")

if __name__ == "__main__":
    cleanup()
