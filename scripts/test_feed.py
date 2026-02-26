import requests
import xml.etree.ElementTree as ET

r = requests.get("https://www.youtube.com/feeds/videos.xml?channel_id=UCGCGxsbmG_9nincyI7xypow")
root = ET.fromstring(r.content)
ns = {"atom":"http://www.w3.org/2005/Atom"}

print("--- Videos ---")
for e in root.findall("atom:entry", ns):
    title = e.find("atom:title", ns).text
    published = e.find("atom:published", ns).text
    
    # safely encode to ignore emojis and print to windows console
    safe_title = title.encode('ascii', 'ignore').decode('ascii')
    
    # but we can look for strings in the original title
    has_evening = "퇴근" in title
    has_evening2 = "요정" in title
    
    print(f"[{published}] {safe_title}")
    if has_evening or has_evening2:
        print(f"  -> FOUND KEYWORD IN: {title.encode('utf-8')}")

