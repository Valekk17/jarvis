import re
import json

def parse():
    with open("chats.json", "r") as f:
        content = f.read()
        
    print(f"Content length: {len(content)}")
    print(f"First 100 chars: {content[:100]}")
    
    clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', content)
    print(f"Cleaned first 100: {clean[:100]}")
    
    # Try simple find
    start = clean.find('[\n  {')
    if start == -1: start = clean.find('[ {')
    print(f"Start index: {start}")
    
    if start != -1:
        end = clean.rfind(']') + 1
        json_str = clean[start:end]
        try:
            data = json.loads(json_str)
            print(f"Parsed {len(data)} items.")
        except Exception as e:
            print(f"Parse error: {e}")

if __name__ == "__main__":
    parse()
