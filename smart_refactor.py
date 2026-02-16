import os
import json
import re
import sys
import time

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

def refactor():
    if not os.path.exists(GRAPH_FILE): return
    with open(GRAPH_FILE) as f: lines = f.readlines()
    
    tasks = []
    # Extract existing tasks from graph
    for line in lines:
        if "[active]" in line or "[pending]" in line:
            clean = line.strip()[2:] 
            parts = clean.split('|')
            status_content = parts[0].strip()
            content = re.sub(r'^\[.*?\] ', '', status_content).strip()
            # Find Actor
            actor = ""
            for p in parts[1:]:
                if "Actor:" in p:
                    actor = p.split("Actor:")[1].strip()
                    actor = re.sub(r' \(ID: .*?\)', '', actor)
            if actor:
                content = f"{content} (Actor: {actor})"
            tasks.append(content)

    prompt = f"""You are JARVIS Task Manager.
Cleanup and Organize the following tasks.

INPUT TASKS:
{json.dumps(tasks)}

INSTRUCTIONS:
1. **Remove Completed**: Delete "выбирать модель Claude Opus 4.6" (User checked it).
2. **Remove Useless/Stupid**: Delete tasks that are:
   - Technical noise ("check background", "login google", "reset settings").
   - Vague ("fill something", "do things").
   - Outdated ("send code").
3. **Merge**: Combine similar tasks (e.g. "Buy car" and "Car purchase").
4. **Classify**: Sort into 3 lists:
   - **Day**: Urgent, Today, Routine.
   - **Month**: Projects, Purchases, Appointments.
   - **Global**: Life Goals, Strategy, Long-term.

OUTPUT JSON:
{{
  "Day": ["task1", ...],
  "Month": ["task2", ...],
  "Global": ["task3", ...]
}}
"""

    manager = KeyManager()
    max_retries = 10
    model_name = "gemini-2.5-pro"
    
    for attempt in range(max_retries):
        key = manager.get_key()
        try:
            if USE_NEW_API:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                result = response.text
            else:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                result = response.text
            
            if "```" in result:
                 result = result.split("```")[1].replace("json", "").strip()
            
            try:
                data = json.loads(result)
            except:
                data = None
            
            if data:
                # Write to files
                for category in ["Day", "Month", "Global"]:
                    file_path = os.path.join(TASKS_DIR, f"{category}.md")
                    with open(file_path, "w") as f:
                        f.write(f"# {category} Tasks\n\n")
                        for t in data.get(category, []):
                            f.write(f"- [ ] {t}\n")
                    print(f"Wrote {file_path}")
                
                # Update Graph (Filter out deleted)
                # We need to rewrite context_graph.md removing tasks that are NOT in the new lists.
                # This ensures graph matches the cleaned view.
                
                valid_tasks = set()
                for cat in data:
                    for t in data[cat]:
                        # Remove (Actor: ...) suffix for matching
                        clean_t = t.split(" (Actor:")[0].strip()
                        valid_tasks.add(clean_t)
                
                # Rewrite Graph
                new_graph_lines = []
                for line in lines:
                    keep = True
                    if "[active]" in line or "[pending]" in line:
                         clean = line.strip()[2:]
                         parts = clean.split('|')
                         content_part = parts[0].strip()
                         content = re.sub(r'^\[.*?\] ', '', content_part).strip()
                         
                         # Fuzzy match? Or exact?
                         # LLM might have rephrased "Buy car" -> "Purchase car".
                         # If so, exact match fails.
                         # This is risky. If LLM rephrased, we lose the link to original graph line (and metadata).
                         # But user wants "Clean".
                         # I will try to match *contains* or keep loosely.
                         # Actually, if LLM merged tasks, I should trust LLM output.
                         # But graph has metadata (Quote, ID).
                         # Maybe I should just KEEP valid ones and DELETE known bad ones?
                         # Or replace graph plans with NEW plans?
                         # If I replace, I lose metadata.
                         
                         # User prioritizes "Clean List".
                         # I will DELETE all old Plans from graph and ADD new Plans from LLM list?
                         # This resets metadata but ensures sync.
                         # Or just keep Graph as "Raw" and only update Task files?
                         # User said "Remove them from graph too".
                         
                         # I will keep the line IF it vaguely matches any valid task.
                         # Or just mark deleted ones as [abandoned]?
                         # Let's try to filter based on keyword overlap.
                         
                         match_found = False
                         for vt in valid_tasks:
                             if vt in content or content in vt:
                                 match_found = True
                                 break
                         if not match_found:
                             keep = False
                    
                    if keep:
                        new_graph_lines.append(line)
                
                with open(GRAPH_FILE, "w") as f:
                    f.writelines(new_graph_lines)
                print("Graph cleaned.")

                return

        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "permission_denied" in str(e).lower():
                print(f"Key issue ({model_name}). Rotating...")
                manager.rotate()
                if attempt > 2: model_name = "gemini-2.5-flash"
                time.sleep(2)
                continue
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    refactor()
