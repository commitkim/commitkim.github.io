"""
테스트 스크립트: 어제 날짜로 고정하여 전체 파이프라인 실행
- 수집 → 요약 → 저장 → 빌드 (카카오/배포는 생략)
"""
import os
import sys
import json
from datetime import datetime, timedelta

# 프로젝트 루트를 기준으로 import (tests/ 에서 상위로)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["PYTHONIOENCODING"] = "utf-8"

from dotenv import load_dotenv
load_dotenv()

import config
from modules import collector, summarizer, generator


def run_test():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    yesterday_dash = f"{yesterday[:4]}-{yesterday[4:6]}-{yesterday[6:]}"
    
    print(f"\n{'='*50}")
    print(f"🧪 테스트 모드: {yesterday_dash} (어제) 날짜로 실행")
    print(f"{'='*50}")
    
    # ── 1. 어제자 영상 검색 ──
    print(f"\n📡 Step 1: 어제({yesterday_dash}) 영상 검색...")
    
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={config.YOUTUBE_CHANNEL_ID}"
    import requests
    import xml.etree.ElementTree as ET
    import re
    
    response = requests.get(url, timeout=15)
    root = ET.fromstring(response.content)
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015'
    }
    
    entries = root.findall('atom:entry', ns)
    candidates = []
    
    for entry in entries:
        title_elem = entry.find('atom:title', ns)
        if title_elem is None:
            continue
        title = title_elem.text
        if config.SEARCH_KEYWORD not in title:
            continue
        
        # 어제 날짜 매칭
        if yesterday in title:
            video_id = entry.find('yt:videoId', ns).text
            candidates.append((video_id, title, yesterday_dash))
            print(f"  ✅ 어제자 영상 발견: {title}")
    
    if not candidates:
        print(f"  ❌ 어제({yesterday_dash}) 영상을 찾을 수 없습니다.")
        return
    
    # ── 2. 자막 추출 ──
    print(f"\n📝 Step 2: 자막 추출...")
    target_video = None
    target_transcript = None
    
    for video_id, title, date in candidates:
        print(f"  🔍 시도: {title}")
        transcript = collector.extract_transcript(video_id)
        if transcript:
            print(f"  ✅ 자막 추출 성공! ({len(transcript)}자)")
            target_video = (video_id, title, date)
            target_transcript = transcript
            break
        else:
            print("  ❌ 자막 없음")
    
    if not target_video:
        print("❌ 자막을 가져오지 못했습니다.")
        return
    
    video_id, title, date = target_video
    
    # ── 3. Gemini 요약 ──
    print(f"\n🤖 Step 3: Gemini 듀얼 요약 생성...")
    summary = summarizer.summarize(target_transcript, video_id)
    if not summary:
        print("❌ 요약 생성 실패")
        return
    
    # ── 4. JSON 저장 ──
    print(f"\n💾 Step 4: JSON 저장...")
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
        "created_at": datetime.now().isoformat()
    }
    
    filepath = os.path.join(config.DATA_DIR, f"{date}.json")
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 저장 완료: {filepath}")
    
    # ── 5. HTML 빌드 ──
    print(f"\n🔨 Step 5: HTML 빌드...")
    generator.build_all()
    
    # ── 결과 출력 ──
    print(f"\n{'='*50}")
    print("🧪 테스트 결과 요약")
    print(f"{'='*50}")
    print(f"  📅 날짜: {date}")
    print(f"  📺 영상: {title}")
    print(f"  🏷️ 주제: {', '.join(summary.get('main_topics', []))}")
    print(f"\n📱 카카오 메시지 미리보기:")
    print(f"{'─'*40}")
    print(summary.get('kakao_summary', '(없음)'))
    print(f"{'─'*40}")
    print(f"\n✅ docs/index.html 을 브라우저에서 열어 확인하세요!")


if __name__ == "__main__":
    run_test()
