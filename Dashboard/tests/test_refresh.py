"""
카카오톡 토큰 갱신 테스트
- 현재 리프레시 토큰으로 액세스 토큰 갱신이 되는지 확인
"""
import os
import sys
import json

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from modules import kakao

print("🔄 토큰 갱신 테스트 시작...")

# 1. 현재 토큰 확인
try:
    with open("kakao_tokens.json", "r") as f:
        old_tokens = json.load(f)
        print(f"📂 현재 저장된 리프레시 토큰: {old_tokens.get('refresh_token', '')[:10]}...")
except FileNotFoundError:
    print("❌ kakao_tokens.json 파일이 없습니다.")
    print("👉 setup_kakao.bat을 실행해서 먼저 인증하세요.")
    exit()

# 2. 토큰 유효성 검사 (자동 갱신 포함)
is_valid = kakao.validate_token()

if is_valid:
    print("\n✅ 토큰이 유효합니다! (자동 갱신 포함)")
else:
    print("\n❌ 토큰이 유효하지 않습니다.")
    print("👉 setup_kakao.bat을 실행해서 다시 로그인하세요.")
