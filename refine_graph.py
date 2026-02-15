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

    prompt = f"""You are a Knowledge Graph Maintainer.
Clean up the following Context Graph (Markdown).

TASKS:
1. **Deduplicate**: Remove semantically identical items (e.g. "call grandma" vs "Call Grandma Galya"). Keep the most detailed one.
2. **Remove Noise**: Delete vague, expired, or useless entries (e.g. "say", "will say", "fill something", "go home", "come").
3. **Add Relations**: In ## Actors section, add a "Relations" field if implied by context (e.g. Arisha is Wife of Valekk).
4. **Normalize**: Ensure Actor names are consistent (Valekk_17, Arisha).
5. **Format**: Keep exactly the same Markdown sections and line format.

Input Graph:
{content}

Output strictly the cleaned Markdown. No comments.
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
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"Key exhausted ({model_name}). Rotating...")
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
