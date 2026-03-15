import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.config import Config
Config(env='dev')

from modules.news_briefing import collector, summarizer

print("Extracting transcript...")
transcript = collector.extract_transcript('AqTw9Q3oe9w')

video_url = f"https://www.youtube.com/watch?v=AqTw9Q3oe9w"
prompt = summarizer.DUAL_SUMMARY_PROMPT.format(
    video_url=video_url,
    transcript=transcript
)

client = summarizer._get_client()
from google.genai import types
cfg = Config.instance()
model = cfg.get("ai.model", "gemini-2.5-flash")

print(f"Calling Gemini ({model})...")
try:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    raw_text = response.text
    print(f"Response received. Length: {len(raw_text)}")
    with open('gemini_response.txt', 'w', encoding='utf-8') as f:
        f.write(raw_text)
    print("RAW RESPONSE saved to gemini_response.txt")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
