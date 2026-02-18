import json
import re

with open('raw.txt', 'r') as f:
    content = f.read()

start = content.find('{')
end = content.rfind('}') + 1
json_str = content[start:end]

try:
    data = json.loads(json_str)
    msgs = [m.get('text', '') for m in data.get('messages', []) if m.get('isOutgoing') and m.get('text')]
    
    keywords = ['люблю', 'love', 'обожаю', 'скучаю', 'родная', 'счастье']
    love_msgs = [t for t in msgs if any(k in t.lower() for k in keywords)]
    
    print("Found Love Messages:")
    for m in love_msgs[:15]:
        print(f"- {m}")
        
except Exception as e:
    print(e)
