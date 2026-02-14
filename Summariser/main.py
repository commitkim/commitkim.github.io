"""
YouTube 경제 뉴스 요약 → 정적 사이트 생성 → 카카오톡 전송 → GitHub Pages 배포

실행 방법:
    python main.py run              # 전체 파이프라인 실행
    python main.py run --no-deploy  # Git push 제외
    python main.py build            # HTML 빌드만 실행
    python main.py setup            # 카카오 인증 설정
"""

import os
import sys
import json
from datetime import datetime

import config
from modules import collector, summarizer, kakao, generator, deployer


def save_data(video_id, video_title, video_date, transcript, summary_json):
    """요약 결과를 data/YYYY-MM-DD.json으로 저장합니다."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    
    data = {
        "video_id": video_id,
        "video_title": video_title,
        "video_date": video_date,
        "video_url": f"https://youtube.com/watch?v={video_id}",
        "main_topics": summary_json.get("main_topics", []),
        "market_summary": summary_json.get("market_summary", {}),
        "key_insights": summary_json.get("key_insights", []),
        "kakao_summary": summary_json.get("kakao_summary", ""),
        "web_report": summary_json.get("web_report", ""),
        "created_at": datetime.now().isoformat()
    }
    
    filepath = os.path.join(config.DATA_DIR, f"{video_date}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 데이터 저장: data/{video_date}.json")
    return filepath


def run_daily_job(no_deploy=False):
    """전체 파이프라인을 실행합니다."""
    print(f"\n{'='*50}")
    print(f"🚀 작업 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # ── 1. YouTube 영상 수집 ──
    print("\n📡 Step 1: YouTube 영상 검색...")
    candidates = collector.find_todays_videos()
    if not candidates:
        print("❌ 오늘자 '모닝루틴' 영상을 찾을 수 없습니다.")
        return
    
    # ── 2. 자막 추출 ──
    print("\n📝 Step 2: 자막 추출...")
    target_video = None
    target_transcript = None
    
    for video_id, title, date in candidates:
        print(f"\n  🔍 시도: {title}")
        transcript = collector.extract_transcript(video_id)
        if transcript:
            print("  ✅ 자막 추출 성공!")
            target_video = (video_id, title, date)
            target_transcript = transcript
            break
        else:
            print("  ❌ 자막 없음. 다음 영상 시도...")
    
    if not target_video:
        print("\n❌ 모든 후보 영상에서 자막을 가져오지 못했습니다.")
        return
    
    video_id, title, date = target_video
    print(f"\n📺 선택된 영상: {title}")
    
    # ── 3. Gemini 듀얼 요약 ──
    print("\n🤖 Step 3: Gemini 듀얼 요약 생성...")
    summary = summarizer.summarize(target_transcript, video_id)
    if not summary:
        print("❌ 요약 생성 실패")
        return
    
    # ── 4. JSON 저장 ──
    print("\n💾 Step 4: JSON 데이터 저장...")
    save_data(video_id, title, date, target_transcript, summary)
    
    # ── 5. HTML 빌드 (Deprecated: Dashboard에서 처리) ──
    # print("\n🔨 Step 5: 정적 사이트 빌드...")
    # generator.build_all()
    
    # ── 6. Git 배포 (Deprecated: Dashboard에서 처리) ──
    # if no_deploy:
    #     print("\nℹ️ Step 6: --no-deploy 플래그로 Git push 생략")
    # else:
    #     print("\n🚀 Step 6: GitHub Pages 배포...")
    #     deployer.deploy(f"📰 뉴스 업데이트: {date}")
    
    # ── 7. 카카오톡 전송 (배포 완료 후 전송해야 링크가 유효함) ──
    print("\n📱 Step 7: 카카오톡 전송...")
    kakao_text = summary.get('kakao_summary', '')
    # 카카오 '자세히보기' 링크를 GitHub Pages 웹 리포트로 연결
    pages_url = config.GITHUB_PAGES_URL.rstrip('/')
    message = f"📰 [모닝루틴 요약]\n{date}\n\n{kakao_text}"
    kakao.send_message(message, link_url=pages_url)
    
    print(f"\n{'='*50}")
    print("✅ 전체 파이프라인 완료!")
    print(f"{'='*50}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            kakao.setup_auth()
        
        elif command == "run":
            no_deploy = "--no-deploy" in sys.argv
            run_daily_job(no_deploy=no_deploy)
        
        elif command == "build":
            print("🔨 HTML 빌드만 실행합니다...")
            generator.build_all()
        
        else:
            print(f"❌ 알 수 없는 명령: {command}")
            print("사용법: python main.py [setup|run|build]")
    else:
        print("사용법:")
        print("  python main.py setup         - 카카오 인증 설정")
        print("  python main.py run           - 전체 파이프라인 실행")
        print("  python main.py run --no-deploy  - Git push 없이 실행")
        print("  python main.py build         - HTML 빌드만 실행")
