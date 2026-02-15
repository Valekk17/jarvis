import os
import re
import json
import hashlib

GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"
STATE_FILE = "/root/.openclaw/workspace/memory/collector_state.json"

def content_hash(text):
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

def normalize_text(text):
    return text.strip().lower()

def fix():
    if not os.path.exists(GRAPH_FILE):
        print("No graph file")
        return

    with open(GRAPH_FILE) as f:
        content = f.read()

    lines = content.split('\n')
    new_sections = {}
    current_section = None
    seen_hashes = set()
    
    # Pre-load state hashes if available
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
            # We will rebuild state hashes from file content to be safe
            # seen_hashes = set(state.get("seen_hashes", [])) 
            pass

    unique_count = 0
    dupe_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('## '):
            current_section = line
            if current_section not in new_sections:
                new_sections[current_section] = []
            continue
            
        if line.startswith('# '):
            continue # Skip header
            
        if not current_section:
            continue

        if line.startswith('- '):
            # Extract core content for deduplication
            # Format: - [status] Content | ... OR - Content | ...
            # Clean md
            clean = line[2:] 
            
            # Extract content part before '|'
            content_part = clean.split('|')[0].strip()
            
            # Remove [status] 
            content_text = re.sub(r'^\[.*?\] ', '', content_part)
            content_text = content_text.replace('**', '')
            
            if "Metric" in current_section: # Special case for metrics
                 m = re.match(r'\*\*(.+?)\*\*: (.+?) \|', clean)
                 if m:
                     content_text = f"{m.group(1)}:{m.group(2)}" # Name:Value
            
            h = content_hash(content_text)
            
            if h in seen_hashes:
                dupe_count += 1
                continue
            
            seen_hashes.add(h)
            new_sections[current_section].append(line)
            unique_count += 1

    # Write back
    with open(GRAPH_FILE, 'w') as f:
        f.write("# Context Graph Entities\n\n")
        for section, items in new_sections.items():
            f.write(f"{section}\n")
            f.write('\n'.join(items))
            f.write('\n\n')
            
    # Update state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
    else:
        state = {}
    
    state["seen_hashes"] = list(seen_hashes)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

    print(f"Graph fixed. Unique: {unique_count}, Dupes removed: {dupe_count}")

if __name__ == "__main__":
    fix()
