import sys
import logging
logging.basicConfig(level=logging.DEBUG)

from core.config import Config
Config(env="prod")

from modules.news_briefing.collector import extract_transcript
from modules.news_briefing.summarizer import summarize

video_id = "7pxnKA6VgtM"
transcript = extract_transcript(video_id)
print(f"Transcript length: {len(transcript)}")
res = summarize(transcript, video_id)
print("Result:", res)
