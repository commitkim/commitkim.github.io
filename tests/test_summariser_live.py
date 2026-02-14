"""
Summariser Live Integration Test
- Runs the full pipeline with ACTUAL network calls (YouTube RSS, Helper, Gemini).
- Validates video fetching logic using 'This Week Monday' as the target date.
- Uses temporary directories for output to protect production data.
"""
import os
import sys
import shutil
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import patch

# Project root setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Summariser'))
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

import config
from modules import collector, summarizer, generator

def get_mondays_date():
    """Returns the date string (YYYY-MM-DD) of the Monday of the current week."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime("%Y-%m-%d")

def run_live_test():
    target_date = get_mondays_date()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_data_dir = os.path.join(temp_dir, 'data')
        temp_docs_dir = os.path.join(temp_dir, 'docs')
        os.makedirs(temp_data_dir)
        os.makedirs(temp_docs_dir)
        
        print(f"\n{'='*50}")
        print(f"🧪 Summariser LIVE Integration Test")
        print(f"📅 Target Date (This Week's Monday): {target_date}")
        print(f"📂 Temp Dir: {temp_dir}")
        print(f"{'='*50}")

        # Patch config paths only (No network mocking!)
        with patch('config.DATA_DIR', temp_data_dir), \
             patch('config.DOCS_DIR', temp_docs_dir):
            
            # 1. Fetch RSS Feed (Real Network Call)
            print("\n📡 Step 1: Fetching YouTube RSS Feed (Real)...")
            
            # Use collector to find videos, but we need to modify logic slightly 
            # to verify against 'target_date' instead of 'today'.
            # Since collector.find_todays_videos is hardcoded for TODAY,
            # we will inspect the RSS feed manually here similar to collector logic
            # but looking for Monday's video.
            
            import requests
            import xml.etree.ElementTree as ET
            
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={config.YOUTUBE_CHANNEL_ID}"
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0'
                }
                response = requests.get(feed_url, headers=headers, timeout=15)
                if response.status_code != 200:
                    print(f"❌ RSS Request Failed: {response.status_code}")
                    sys.exit(1)
                    
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
                
                target_video = None
                
                print(f"  🔍 Searching for video from {target_date}...")
                
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns).text
                    video_id = entry.find('yt:videoId', ns).text
                    published = entry.find('atom:published', ns).text
                    
                    # Date parsing logic with KST conversion (UTC+9)
                    try:
                        dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S+00:00")
                        kst_dt = dt + timedelta(hours=9)
                        video_date_kst = kst_dt.strftime("%Y-%m-%d")
                    except Exception:
                        video_date_kst = published.split('T')[0] # Fallback
                    
                    print(f"  - Found: [{video_date_kst}] {title} (Raw: {published})")
                    
                    # Strictly check keyword AND date
                    if config.SEARCH_KEYWORD not in title:
                        continue

                    if video_date_kst == target_date:
                         print(f"  ✅ Match Found! {title}")
                         target_video = (video_id, title, video_date_kst)
                         break
                
                if not target_video:
                    print(f"⚠️ Could not find video for Monday ({target_date}).")
                    print("  (This is expected if today is Monday and video isn't up, or if it's too long ago for RSS)")
                    print("  ⚠️ Proceeding with LATEST video for functionality test instead.")
                    
                    # Fallback to latest
                    entry = root.find('atom:entry', ns)
                    title = entry.find('atom:title', ns).text
                    video_id = entry.find('yt:videoId', ns).text
                    target_video = (video_id, title, "LATEST_FALLBACK")

                video_id, title, date = target_video
                
                # 2. Extract Transcript (Real Call)
                print(f"\n📝 Step 2: Extracting Transcript for {video_id}...")
                transcript = collector.extract_transcript(video_id)
                if not transcript:
                    print("❌ Transcript extraction failed.")
                    sys.exit(1)
                print(f"  ✅ Success ({len(transcript)} chars)")

                # 3. Summarize (Real Gemini Call)
                print(f"\n🤖 Step 3: Generating Summary (Real Gemini API)...")
                summary = summarizer.summarize(transcript, video_id)
                if not summary:
                    print("❌ Gemini summary failed.")
                    sys.exit(1)
                print("  ✅ Success")

                # 4. Build
                print(f"\n🔨 Step 4: Building Site...")
                
                data = {
                    "video_id": video_id,
                    "video_title": title,
                    "video_date": date,
                    "video_url": f"https://youtube.com/watch?v={video_id}",
                    "main_topics": summary.get("main_topics", []),
                    "market_summary": summary.get("market_summary", {}),
                    "key_insights": summary.get("key_insights", []),
                    "kakao_summary": summary.get("kakao_summary", ""),
                    "web_report": summary.get("web_report", ""),
                    "created_at": datetime.now().isoformat(),
                    "is_test": True 
                }
                
                filepath = os.path.join(config.DATA_DIR, f"{date}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                generator.build_all()
                
                if os.path.exists(os.path.join(config.DOCS_DIR, 'index.html')):
                    print("\n✅ LIVE Test Completed Successfully!")
                else:
                    print("\n❌ Build failed (index.html missing)")
                    sys.exit(1)

            except Exception as e:
                print(f"\n❌ Test Failed: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

if __name__ == "__main__":
    run_live_test()
