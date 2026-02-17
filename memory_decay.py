import os
import math
from datetime import date, datetime

GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"
ARCHIVE_FILE = "/root/.openclaw/workspace/memory/.archive/archive_decay.md"

TYPE_WEIGHTS = {
    "decision": 15,
    "metric": 10,
    "promise": 8,
    "plan": 5
}

def calculate_score(line, entity_type):
    # Parse date
    # Format: ... | Date: YYYY-MM-DD ...
    # Or Target: ...
    item_date = date.today()
    
    if "Date:" in line:
        try:
            d_str = line.split("Date:")[1].split("|")[0].strip()
            item_date = datetime.strptime(d_str, "%Y-%m-%d").date()
        except: pass
    elif "Target:" in line:
        try:
            d_str = line.split("Target:")[1].split("|")[0].strip()
            if d_str.lower() != "none":
                item_date = datetime.strptime(d_str, "%Y-%m-%d").date()
        except: pass
    elif "Deadline:" in line:
        try:
            d_str = line.split("Deadline:")[1].split("|")[0].strip()
            if d_str.lower() != "none":
                item_date = datetime.strptime(d_str[:10], "%Y-%m-%d").date()
        except: pass

    age_days = (date.today() - item_date).days
    
    # Logic from Squish:
    # Base 50 + Type + Recency
    # Recency: 30 * (0.5 ^ (age / 30))
    
    recency = 30 * (0.5 ** (age_days / 30.0))
    if age_days < 0: recency = 30 # Future tasks
    
    type_score = TYPE_WEIGHTS.get(entity_type.lower(), 0)
    
    score = 50 + type_score + recency
    
    # User flags? (Pinned/Protected) - Not implemented yet.
    
    return score, age_days

def run_decay():
    if not os.path.exists(GRAPH_FILE): return

    with open(GRAPH_FILE) as f:
        lines = f.readlines()
        
    new_lines = []
    archived_lines = []
    
    current_section = None
    
    for line in lines:
        if line.startswith("## "):
            current_section = line.strip()[3:].lower() # "plans", "promises"
            new_lines.append(line)
            continue
            
        if not line.startswith("- "):
            new_lines.append(line)
            continue
            
        # Analyze item
        if current_section and current_section in ["plans", "promises", "decisions", "metrics"]:
             # Calculate score
             # Strip status? "- [active] ..."
             entity_type = current_section[:-1] # plan, promise
             score, age = calculate_score(line, entity_type)
             
             # Threshold: < 40?
             # Base 50. So if very old (recency -> 0), score -> 50 + type.
             # Squish uses "Access Frequency" too. I don't have it.
             # So items NEVER decay below 50?
             # Wait, Squish decays ONLY if access is low.
             # If I lack access data, I should rely on AGE more.
             # I'll penalize age more heavily.
             # Decay: -0.5 per day?
             
             # Modified Logic for Static Files:
             # If Age > 90 days AND Type != Decision -> Archive.
             # Decisions keep value 15. Score = 65.
             # Plans keep value 5. Score = 55.
             
             # If I strictly follow Squish logic, they stick around forever (Score > 0).
             # But `getLowImportanceMemories` filters `maxImportance = 30`.
             # How does it drop below 30?
             # Base score is 50.
             # Maybe Base decays? No.
             # Ah, `calculateImportance` clamps.
             # Maybe `accessFrequency` is critical?
             
             # I will use a simpler rule for now:
             # If Age > 60 days AND not Decision -> Archive.
             
             if age > 60 and entity_type != "decision":
                 archived_lines.append(line.strip() + f" | Archived: Age {age}d\n")
             else:
                 new_lines.append(line)
        else:
            new_lines.append(line)
            
    if archived_lines:
        # Write back graph
        with open(GRAPH_FILE, "w") as f:
            f.writelines(new_lines)
            
        # Append to archive
        os.makedirs(os.path.dirname(ARCHIVE_FILE), exist_ok=True)
        with open(ARCHIVE_FILE, "a") as f:
            f.write(f"\n## Decay Run {date.today().isoformat()}\n")
            f.writelines(archived_lines)
            
        print(f"Decayed {len(archived_lines)} old items.")
    else:
        print("No items decayed.")

if __name__ == "__main__":
    run_decay()
