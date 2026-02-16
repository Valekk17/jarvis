import os
import sys
import json
import time

GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"

try:
    from google import genai
    from google.genai import types
    USE_NEW_API = True
except ImportError:
    import google.generativeai as genai
    USE_NEW_API = False

sys.path.insert(0, "/root/.openclaw/workspace")
from key_manager import KeyManager

def refine():
    if not os.path.exists(GRAPH_FILE):
        return

    with open(GRAPH_FILE) as f:
        content = f.read()

    prompt = f"""You are a strict Knowledge Graph Editor for JARVIS.
Refactor the following Markdown content.

RULES:
1. **Deduplicate Aggressively**: Merge items that mean the same thing (e.g., "call grandma", "Call Grandma Galya", "позвонить бабушке"). Keep the most detailed version.
2. **Remove Noise**: DELETE any item that is:
   - A status ("I am ready", "I am here", "arrived").
   - Vague ("solve problem", "do it", "fill something").
   - Expired/Old daily routine ("go home").
   - Duplicate of another item (even if phrasing differs).
3. **Enforce Relations**: Ensure EVERY Promise, Plan, Decision has an `| Actor: Name` or `| From: X -> Y` field.
   - If missing, infer from context (Valekk_17 is the default owner).
4. **Structure**: Keep sections: Actors, Promises, Decisions, Metrics, Plans.
5. **Format**:
   - Actors: `- **Name** | Role: ... | Relations: ...`
   - Others: `- [status] Content | Actor: Name | ...`

Input Graph:
{content}

Output ONLY the cleaned Markdown.
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
                
            # Validate result
            if "## Actors" in result:
                with open(GRAPH_FILE, 'w') as f:
                    f.write(result.strip())
                print("Graph refined successfully.")
                return
            else:
                print("Gemini returned invalid format.")
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "permission_denied" in err or "leaked" in err:
                print(f"Key issue ({model_name}). Rotating...")
                manager.rotate()
                # Switch to Flash if Pro fails too much
                if attempt > 2:
                    model_name = "gemini-2.5-flash"
                time.sleep(2)
                continue
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    refine()
