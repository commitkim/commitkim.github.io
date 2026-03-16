import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from core.logger import get_logger

Config(env='dev')
from modules.news_briefing import collector, summarizer

video_id = 'KUsqAI-lI1Q'
print(f"Starting transcript extraction for {video_id}...", flush=True)
transcript = collector.extract_transcript(video_id)
print(f"Transcript length: {len(transcript)}", flush=True)

print("Starting summarizer...", flush=True)

from google.genai import types
client = summarizer._get_client()
cfg = Config.instance()
model = cfg.get("ai.model", "gemini-2.5-flash")

video_url = f"https://www.youtube.com/watch?v={video_id}"
prompt = summarizer.DUAL_SUMMARY_PROMPT.format(
    video_url=video_url,
    transcript=transcript
)

try:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=8192,
        )
    )
    
    # Check finish reason
    candidates = response.candidates
    if candidates:
        print(f"Finish Reason: {candidates[0].finish_reason}")
    
    print(f"Usage Metadata: {response.usage_metadata}")
    
    raw_text = response.text
    print(f"Response received. Length: {len(raw_text)}")
    with open('gemini_morning_response.txt', 'w', encoding='utf-8') as f:
        f.write(raw_text)
    print("RAW RESPONSE saved to gemini_morning_response.txt")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
