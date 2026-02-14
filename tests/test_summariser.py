"""
테스트 스크립트: 어제/오늘 날짜 기준 전체 파이프라인 테스트
- 수집 → 요약 → 저장 → 빌드
- 카카오톡 전송은 제외 (비용/스팸 방지)
"""
import os
import sys
import json
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가 (tests/ -> Project/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Summariser 모듈 경로 추가 (Project/Summariser)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Summariser'))
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

import shutil
import tempfile
from unittest.mock import patch

import config
from modules import collector, summarizer, generator

import argparse

def run_test():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-ai', action='store_true', help='Skip actual Gemini API calls and use mock data')
    args = parser.parse_args()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_data_dir = os.path.join(temp_dir, 'data')
        temp_docs_dir = os.path.join(temp_dir, 'docs')
        os.makedirs(temp_data_dir)
        os.makedirs(temp_docs_dir)
        
        print(f"\n{'='*50}")
        print(f"🧪 Summariser Integration Test (Isolated)")
        if args.skip_ai:
             print(f"⏩ MODE: SKIP AI (Using Mock Summaries)")
        else:
             print(f"🤖 MODE: LIVE AI (Calling Gemini API)")
        print(f"📂 Temp Dir: {temp_dir}")
        print(f"{'='*50}")

        # Patch config paths AND mock requests.get for RSS
        with patch('config.DATA_DIR', temp_data_dir), \
             patch('config.DOCS_DIR', temp_docs_dir), \
             patch('requests.get') as mock_get:
            
            # ---------------------------------------------------------
            # 🛠️ MOCK SETUP (RSS Feed)
            # ---------------------------------------------------------
            # Mock RSS Response with a known VALID video (from 2026-02-13 Data)
            # This ensures the test passes even if local network blocks RSS.
            mock_rss_content = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
    <entry>
        <id>yt:video:bCpktl7dHv8</id>
        <yt:videoId>bCpktl7dHv8</yt:videoId>
        <title>한국경제신문 30분 만에 읽기 | 20260213🌞#모닝루틴 | 아침 8시 라이브</title>
        <link rel="alternate" href="https://www.youtube.com/watch?v=bCpktl7dHv8"/>
        <published>2026-02-13T08:00:00+00:00</published>
    </entry>
</feed>
"""
            # Configure mock to return success only for RSS url
            mock_response = sys.modules['unittest.mock'].MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_rss_content.encode('utf-8')
            mock_get.return_value = mock_response
            
            # 1. RSS 피드 가져오기
            print("\n📡 Step 1: 최근 영상 검색 (Mocked RSS)...")
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={config.YOUTUBE_CHANNEL_ID}"
            
            import requests
            import xml.etree.ElementTree as ET
            
            try:
                # This call will be intercepted by mock_get
                response = requests.get(feed_url, timeout=10)
                
                if response.status_code != 200:
                    print(f"❌ RSS 요청 실패: {response.status_code}")
                    sys.exit(1)
                    
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
                
                target_video = None
                
                # 가장 최근 영상 1개만 선택
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns).text
                    video_id = entry.find('yt:videoId', ns).text
                    published = entry.find('atom:published', ns).text
                    date_str = published.split('T')[0] # YYYY-MM-DD
                    
                    print(f"  🔍 검사 중: [{date_str}] {title}")
                    
                    if config.SEARCH_KEYWORD in title:
                        print(f"  ✅ 키워드 '{config.SEARCH_KEYWORD}' 매칭 성공!")
                        target_video = (video_id, title, date_str)
                        break
                
                if not target_video:
                    print(f"❌ '{config.SEARCH_KEYWORD}' 키워드가 포함된 최신 영상을 찾을 수 없습니다.")
                    sys.exit(1)

                video_id, title, date = target_video
                
                # 2. 자막 추출
                print(f"\n📝 Step 2: 자막 추출 시도 ({video_id})...")
                transcript = collector.extract_transcript(video_id)
                
                if not transcript:
                    print("❌ 자막을 가져올 수 없습니다. (테스트 중단)")
                    # Mock transcript if network fails?
                    # For now, let's assume transcript API works or fail if it doesn't.
                    sys.exit(1)
                
                print(f"  ✅ 자막 추출 성공 ({len(transcript)}자)")
                
                # 3. 요약 (테스트 옵션에 따라 분기)
                if args.skip_ai:
                    print(f"\n⏩ Step 3: AI 요약 생성 (SKIPPED - Mock 데이터 사용)...")
                    summary = {
                        "main_topics": ["테스트 주제 1", "테스트 주제 2"],
                        "market_summary": {"KOSPI": "2,500 (+1.2%)", "USD/KRW": "1,350 (-5)"},
                        "key_insights": ["인사이트 1: 이것은 테스트입니다.", "인사이트 2: 제미나이 호출을 건너뛰었습니다."],
                        "kakao_summary": "[MOCK] 오늘의 경제 뉴스 요약입니다.\n1. 테스트1\n2. 테스트2",
                        "web_report": "## [MOCK] 웹 리포트 상세\n- 테스트용 데이터입니다.\n- 실제 AI 호출이 발생하지 않았습니다."
                    }
                else:
                    print(f"\n🤖 Step 3: AI 요약 생성 (Gemini 호출)...")
                    summary = summarizer.summarize(transcript, video_id)
                
                if not summary:
                    print("❌ 요약 실패")
                    sys.exit(1)
                    
                # 4. 저장 및 빌드
                print(f"\n💾 Step 4: 결과 저장 및 사이트 빌드...")
                
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
                    
                print(f"  ✅ 데이터 저장됨: {filepath}")
                
                print(f"\n🔨 Step 5: 사이트 빌드...")
                generator.build_all()
                
                print(f"\n✅ 테스트 완료! 성공적으로 처리되었습니다.")
                
            except Exception as e:
                print(f"\n❌ 테스트 중 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

if __name__ == "__main__":
    run_test()
