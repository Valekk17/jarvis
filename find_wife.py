import json
import re

def search_chat():
    with open("chats.json", "r") as f:
        # Simple parse or robust? Use robust if needed.
        # Assuming chats.json is clean from last run or needs re-fetching?
        # I'll re-fetch to be safe if file is old or empty.
        pass
        
    # Re-fetch
    # subprocess.run("tg chats --json > chats.json", shell=True)
    # Just read what we have or re-fetch.
    
    # Let's search in file content directly for "Arisha" or "Ариша" or "Wife"
    # Or "Мой Мир"
    with open("chats.json", "r") as f:
        content = f.read()
        
    targets = ["Arisha", "Ариша", "Мой Мир", "Wife", "Жена"]
    for t in targets:
        if t in content:
            print(f"Found candidate: {t}")
            # Find the full JSON object?
            
if __name__ == "__main__":
    search_chat()
