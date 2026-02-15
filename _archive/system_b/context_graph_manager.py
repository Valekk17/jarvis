import json
import os
import time
import uuid
from datetime import datetime
import google.generativeai as genai
from key_manager import KeyManager

# Configuration
WORKSPACE_DIR = "/root/.openclaw/workspace"
ACTIVITY_FILE = os.path.join(WORKSPACE_DIR, "activity_graph.jsonl")
PLAYBOOKS_FILE = os.path.join(WORKSPACE_DIR, "playbooks.md")
CONTEXT_GRAPH_FILE = os.path.join(WORKSPACE_DIR, "context_graph.json")
STATE_FILE = os.path.join(WORKSPACE_DIR, "context_manager_state.json")

MIN_ACTIVITIES_FOR_ANALYSIS = 1

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return None
    return None

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_activities():
    activities = []
    if not os.path.exists(ACTIVITY_FILE):
        return []
        
    with open(ACTIVITY_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                activities.append(json.loads(line))
            except: continue
    return activities

def generate_playbooks(activities, key_manager):
    """Use LLM to analyze activities and generate Playbooks."""
    if not activities: return None
    
    # Contextualize for LLM
    text_log = ""
    for act in activities[-50:]: # Analyze last 50 activities
        text_log += f"- [{act.get('start_ts', '')}] {act.get('title', '')}: {act.get('summary', '')} (Project: {act.get('project')})\n"
        
    models = ['models/gemini-2.5-flash', 'models/gemini-1.5-flash']
    
    prompt = f"""
    You are the Strategic Architect of an AI Agent (OpenClaw).
    Analyze the recent User Activities to detect recurring patterns, habits, or workflows.
    
    Data:
    {text_log}
    
    Task:
    1. Identify recurring patterns (e.g., "Morning Check-in", "Weekly Review", "Specific Project Work").
    2. Formalize these into "Playbooks" — structured instructions for the Agent.
    3. Output the result in robust Markdown format.
    
    Format:
    # Agent Playbooks
    
    ## [Pattern Name]
    **Trigger:** [When does this happen?]
    **Frequency:** [Daily/Weekly/Ad-hoc]
    **Goal:** [What is the user trying to achieve?]
    
    ### Workflow
    1. [Step 1]
    2. [Step 2]
    
    ### Agent Actions
    - [What should the agent do proactively?]
    
    ... (repeat for other patterns)
    """
    
    for model_name in models:
        try:
            key = key_manager.get_key()
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"LLM Error ({model_name}): {e}")
            key_manager.rotate()
            continue
            
    return None

def main():
    print(f"Context Graph Manager started at {datetime.now()}")
    
    # Load state
    state = load_json(STATE_FILE) or {"last_run": None}
    
    # Load activities
    activities = load_activities()
    print(f"Loaded {len(activities)} activities.")
    
    if len(activities) < MIN_ACTIVITIES_FOR_ANALYSIS:
        print(f"Not enough activities for pattern analysis ({len(activities)}/{MIN_ACTIVITIES_FOR_ANALYSIS}). Skipping.")
        return

    # Generate Playbooks
    print("Analyzing patterns via LLM...")
    key_manager = KeyManager()
    playbooks_md = generate_playbooks(activities, key_manager)
    
    if playbooks_md:
        # Save Playbooks
        with open(PLAYBOOKS_FILE, 'w', encoding='utf-8') as f:
            f.write(playbooks_md)
        print(f"Updated {PLAYBOOKS_FILE}")
        
        # Save State
        state["last_run"] = datetime.now().isoformat()
        state["analyzed_count"] = len(activities)
        save_json(STATE_FILE, state)
    else:
        print("Failed to generate playbooks.")

    print("Done.")

if __name__ == "__main__":
    main()
