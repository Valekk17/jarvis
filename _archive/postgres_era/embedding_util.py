import google.generativeai as genai
from key_manager import KeyManager

EMBEDDING_MODEL = "models/gemini-embedding-001"

def get_embedding(text, manager):
    # Retry logic
    max_retries = len(manager.keys) * 2
    for attempt in range(max_retries):
        key = manager.get_key()
        genai.configure(api_key=key)
        
        try:
            text = text.replace("\n", " ")
            if "004" in EMBEDDING_MODEL:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document",
                    title="Embedding of chunk",
                    output_dimensionality=768
                )
            else:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document",
                    title="Embedding of chunk"
                )
            return result['embedding']
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "ResourceExhausted" in str(e):
                # print(f"Error (429) rotating...")
                manager.rotate()
                continue
            else:
                print(f"Non-Quota Error: {e}")
                if attempt > 1: return []
                continue
    print("Max retries for embedding.")
    return []
