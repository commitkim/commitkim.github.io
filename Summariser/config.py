
# -----------------------------------------------------------------------------
# ⚙️ AI 뉴스 요약 어시스턴트 설정 파일 (v2 - Static Site Generator)
# -----------------------------------------------------------------------------

import os
from dotenv import load_dotenv

# =============================================================================
# 📂 프로젝트 경로
# =============================================================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# .env 파일 로드
# .env 파일 로드 (Project 루트)
load_dotenv(os.path.join(PROJECT_DIR, "../.env"))

DATA_DIR = os.path.abspath(os.path.join(PROJECT_DIR, "../Dashboard/data/news"))
# HTML/JSON 출력 경로 (Project/docs/summariser)
DOCS_DIR = os.path.abspath(os.path.join(PROJECT_DIR, "../docs/summariser"))
TEMPLATES_DIR = os.path.join(PROJECT_DIR, "templates")

# =============================================================================
# 🔑 API 키 및 인증
# =============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = "http://localhost"

# =============================================================================
# 🐙 GitHub 설정 (배포 자동화)
# =============================================================================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "")  # 예: https://github.com/username/Summariser.git
GIT_EXECUTABLE = os.getenv("GIT_EXECUTABLE", "git")  # Git 경로 (PATH에 없을 경우)
GITHUB_PAGES_URL = os.getenv("GITHUB_PAGES_URL", "https://commitkim.github.io")  # GitHub Pages 주소

# =============================================================================
# 📺 유튜브 수집 설정
# =============================================================================
YOUTUBE_CHANNEL_ID = "UCGCGxsbmG_9nincyI7xypow"
SEARCH_KEYWORD = "모닝루틴"

# =============================================================================
# 🤖 AI 설정
# =============================================================================
GEMINI_MODEL = "gemini-2.0-flash"

# =============================================================================
# 📁 파일 경로
# =============================================================================
KAKAO_TOKEN_FILE = os.path.join(PROJECT_DIR, "kakao_tokens.json")


