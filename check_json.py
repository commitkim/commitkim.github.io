import json
import os

filename = 'gemini_morning_response.txt'
if not os.path.exists(filename):
    print(f"Error: {filename} not found")
    exit(1)

with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Content length: {len(content)}")
print(f"Last 100 characters: '{content[-100:]}'")

try:
    data = json.loads(content)
    print("SUCCESS: JSON is valid")
except json.JSONDecodeError as e:
    print(f"FAILURE: JSONDecodeError: {e}")
    # Print context around error
    start = max(0, e.pos - 50)
    end = min(len(content), e.pos + 50)
    print(f"Context: ...{content[start:e.pos]} >>>ERROR HERE<<< {content[e.pos:end]}...")
except Exception as e:
    print(f"ERROR: {e}")
