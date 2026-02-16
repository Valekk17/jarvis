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

    ontology_file = "/root/.openclaw/workspace/jarvis/ONTOLOGY.md"
    ontology = ""
    if os.path.exists(ontology_file):
        with open(ontology_file) as f: ontology = f.read()

    prompt = f"""You are the JARVIS Knowledge Graph Architect.
Your task: Re-validate and format every item in the Graph against the Strict Ontology.

ONTOLOGY RULES:
{ontology}

INSTRUCTIONS:
1. **Analyze** each item in the Input Graph.
2. **Discard** items with confidence < 0.7 or vague/noise (e.g. "be ready").
3. **Format** items strictly as Markdown list entries, but include ALL required fields from Ontology if available.
   - Actors: `- **Name** | Role: ... | Context: ...`
   - Plans: `- [status] Content | Actor: ... | Target Date: ... | Quote: ... | Confidence: ...`
   - Promises: `- [status] Content | From: ... -> To: ... | Quote: ... | Confidence: ...`
4. **Enforce** naming: "Valekk_17", "Arisha", etc.
5. **Deduplicate**.

INPUT GRAPH:
{content}

OUTPUT:
Refactored Markdown Graph.
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
