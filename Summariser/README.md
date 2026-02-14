# AI News Summariser 🤖

**매일 아침, 경제 뉴스를 AI가 요약해줍니다.**
*This project is generated and maintained by Google's Agentic AI.*

---

## 🏗️ 아키텍처 (Dual Mode)

```
[오전 09:00] 모닝루틴 / [오후 18:30] 퇴근요정 (Windows Task Scheduler)
    → YouTube RSS에서 해당 모드 키워드(모닝루틴/퇴근요정) 영상 검색
    → 자막 추출 & Gemini 듀얼 요약 생성
    → JSON 저장 (data/morning 또는 data/evening 폴더에 일별 저장)
    → Jinja2 → HTML 정적 사이트 빌드 (docs/reports/모드/ 하위)
    → Git push → GitHub Pages 배포
    → 카카오톡 메시지 전송 (🌐 자세히보기 → 웹 리포트)
```

## 📂 프로젝트 구조

```
Summariser/
├── main.py                 # 모드(morning/evening) 기반 파이프라인 제어
├── config.py               # SEARCH_MODES 및 경로 설정
├── modules/
│   ├── collector.py        # 키워드 기반 영상 수집
│   ├── summarizer.py       # Gemini 듀얼 요약
│   ├── generator.py        # 모드별 디렉토리 빌드 및 내비게이션 생성
│   └── ...
├── templates/              # 모드별 섹션이 분리된 Jinja2 템플릿
├── data/                   
│   ├── morning/            # 아침 뉴스 데이터 (YYYY-MM-DD.json)
│   └── evening/            # 저녁 뉴스 데이터 (YYYY-MM-DD.json)
├── run_morning.bat         # [수동] 모닝루틴 즉시 실행
├── run_evening.bat         # [수동] 퇴근요정 즉시 실행
├── automation.bat          # 호출용 (mode 인자 필수)
├── register_schedule.bat   # 듀얼 작업 스케줄러 등록
└── ...
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
