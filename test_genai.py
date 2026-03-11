import sys
import logging
logging.basicConfig(level=logging.DEBUG)

from core.config import Config
Config(env="prod")

from google import genai
from google.genai import types
from modules.news_briefing.collector import extract_transcript
from modules.news_briefing.summarizer import DUAL_SUMMARY_PROMPT

video_id = "7pxnKA6VgtM"
transcript = extract_transcript(video_id)
print(f"Transcript length: {len(transcript)}")

cfg = Config.instance()
client = genai.Client(api_key=cfg.get_secret("GEMINI_API_KEY"))

prompt = DUAL_SUMMARY_PROMPT.format(
    video_url=f"https://www.youtube.com/watch?v={video_id}",
    transcript=transcript
)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    with open("raw_response.txt", "w", encoding="utf-8") as f:
        f.write(str(response.text))
    print("Saved response to raw_response.txt")
except Exception as e:
    print(f"Failed: {e}")
