# 📈 모닝루틴 경제 브리핑

> **🌐 웹사이트**: [https://commitkim.github.io](https://commitkim.github.io/)

YouTube 경제 뉴스(한국경제신문 모닝루틴)를 AI가 분석하여 카카오톡 요약 + 웹 리포트를 자동 생성하는 봇입니다.

### 🤖 Built with AI
코드 설계부터 구현, 디버깅까지 대부분의 개발 과정에서 AI의 도움을 받았습니다.
- **Claude Opus 4.6 Thinking** (Antigravity) — 프로젝트 전반의 아키텍처 설계, 코드 구현, 디버깅을 주도적으로 담당
- **Gemini 3 Pro High** (Antigravity) — 아키텍처 설계, 구현 및 디버깅 보조
- **Gemini 3 Flash** — 매일 경제 유튜브 영상을 요약·분석하는 AI 엔진

## 🏗️ 아키텍처

```
평일 09:00 (Windows Task Scheduler)
    → YouTube RSS에서 오늘자 영상 검색
    → 자막 추출 & Gemini 듀얼 요약 생성
    → JSON 저장 (data/YYYY-MM-DD.json)
    → Jinja2 → HTML 정적 사이트 빌드 (docs/)
    → Git push → GitHub Pages 배포
    → 카카오톡 메시지 전송 (🌐 자세히보기 → 웹 리포트)
```

## 📂 프로젝트 구조

```
Summariser/
├── main.py                 # 7단계 파이프라인 오케스트레이터
├── config.py               # 설정 중앙 관리
├── modules/
│   ├── collector.py        # YouTube RSS 수집 + 자막 추출
│   ├── summarizer.py       # Gemini 듀얼 요약 (카톡 + 웹)
│   ├── kakao.py            # 카카오톡 토큰 관리 & 메시지 전송
│   ├── generator.py        # Jinja2 → HTML 빌드
│   └── deployer.py         # Git 자동 배포
├── templates/              # Jinja2 HTML 템플릿
├── data/                   # 일별 요약 JSON
├── docs/                   # GitHub Pages 정적 사이트 (빌드 결과)
├── tests/                  # 테스트 스크립트
├── run_auto.bat            # 스케줄러용 실행 스크립트
├── register_schedule.bat   # Windows 작업 스케줄러 등록
├── setup_kakao.bat         # 카카오 인증 설정
└── requirements.txt
```

## 🚀 실행 방법

```bash
python main.py run              # 전체 파이프라인 실행
python main.py run --no-deploy  # Git push 제외
python main.py build            # HTML 빌드만
python main.py setup            # 카카오 인증 설정
```

## ⚙️ 설정 (.env)

```
GEMINI_API_KEY=...
KAKAO_REST_API_KEY=...
KAKAO_CLIENT_SECRET=...
GITHUB_TOKEN=ghp_...
GITHUB_REPO_URL=https://github.com/username/repo.git
GIT_EXECUTABLE=C:\Program Files\Git\cmd\git.exe
```
