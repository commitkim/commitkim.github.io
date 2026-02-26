import requests
import xml.etree.ElementTree as ET

r = requests.get("https://www.youtube.com/feeds/videos.xml?channel_id=UCGCGxsbmG_9nincyI7xypow")
root = ET.fromstring(r.content)
ns = {"atom":"http://www.w3.org/2005/Atom"}

for e in root.findall("atom:entry", ns):
    title = e.find("atom:title", ns).text
    print(repr(title))
    if "퇴근" in title:
        print("FOUND 퇴근!!!!!")
