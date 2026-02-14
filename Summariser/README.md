# AI News Summariser 🤖

**매일 아침, 경제 뉴스를 AI가 요약해줍니다.**
*This project is generated and maintained by Google's Agentic AI.*

---

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
├── automation.bat          # 통합 자동화 실행 스크립트 (Scheduled Job용)
├── register_schedule.bat   # Windows 작업 스케줄러 등록
├── setup_kakao.bat         # 카카오 인증 설정
└── requirements.txt
```

## 🚀 실행 방법

### 자동 실행 (전체 파이프라인)
프로젝트 루트의 통합 스케줄러(`scheduled_job.bat`)에 의해 실행되지만, 개별 테스트를 원할 경우:
```bash
automation.bat
```

### 수동 실행 (상세 옵션)
공용 가상환경(`Dashboard/venv`)을 사용하여 실행합니다.
```bash
..\Dashboard\venv\Scripts\python main.py run              # 전체 파이프라인 실행
..\Dashboard\venv\Scripts\python main.py run --no-deploy  # Git push 제외
..\Dashboard\venv\Scripts\python main.py build            # HTML 빌드만
..\Dashboard\venv\Scripts\python main.py setup            # 카카오 인증 설정
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

## 🧪 테스트

```bash
..\tests\test_summariser.bat   # Mock 테스트 (안전)
..\tests\test_live.bat         # Live 테스트 (실제 API 호출)
```
