import os
import json
import re
import sys

# ... imports from gemini_cli/key_manager
try:
    from google import genai
    from google.genai import types
    USE_NEW_API = True
except ImportError:
    import google.generativeai as genai
    USE_NEW_API = False

sys.path.insert(0, "/root/.openclaw/workspace")
from key_manager import KeyManager

MEMORY_DIR = "/root/.openclaw/workspace/memory"
GRAPH_FILE = os.path.join(MEMORY_DIR, "context_graph.md")
TASKS_DIR = os.path.join(MEMORY_DIR, "Tasks")

os.makedirs(TASKS_DIR, exist_ok=True)

def reorganize():
    if not os.path.exists(GRAPH_FILE): return
    with open(GRAPH_FILE) as f: lines = f.readlines()
    
    tasks = []
    for line in lines:
        if "[active]" in line or "[pending]" in line:
            clean = line.strip()[2:] # remove '- '
            parts = clean.split('|')
            status_content = parts[0].strip()
            content = re.sub(r'^\[.*?\] ', '', status_content).strip()
            tasks.append(content)
            
    if not tasks:
        print("No tasks to organize.")
        return

    print(f"Organizing {len(tasks)} tasks...")

    prompt = f"""You are a Personal Task Manager.
Categorize the following list of tasks into 3 lists:
1. **Day** (Urgent, Quick, Today, Routine).
2. **Month** (Projects, Medium-term, Buying things).
3. **Global** (Long-term goals, Life events, Strategic).

Tasks:
{json.dumps(tasks)}

OUTPUT JSON:
{{
  "Day": ["task1", ...],
  "Month": ["task2", ...],
  "Global": ["task3", ...]
}}
"""
    
    manager = KeyManager()
    max_retries = 10
    
    for attempt in range(max_retries):
        key = manager.get_key()
        try:
            if USE_NEW_API:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                result = response.text
            else:
                genai.configure(api_key=key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                result = response.text
                
            # Parse
            if "```" in result:
                 result = result.split("```")[1].replace("json", "").strip()
            
            try:
                data = json.loads(result)
            except:
                data = None
            
            if data:
                for category in ["Day", "Month", "Global"]:
                    file_path = os.path.join(TASKS_DIR, f"{category}.md")
                    with open(file_path, "w") as f:
                        f.write(f"# {category} Tasks\n\n")
                        for t in data.get(category, []):
                            f.write(f"- [ ] {t}\n")
                    print(f"Wrote {file_path}")
                return
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "permission_denied" in str(e).lower():
                manager.rotate()
                continue
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    reorganize()
