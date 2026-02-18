# 📜 CommitKim Project Rules & Guidelines

이 문서는 **CommitKim Project Hub**의 구조와 운영 규칙을 정의합니다.
새로운 기능이나 폴더를 추가할 때 이 규칙을 준수하여 프로젝트의 무결성을 유지해야 합니다.

---

## 1. 📂 디렉토리 구조 및 역할

프로젝트 루트의 각 폴더는 명확한 역할을 가지고 있습니다.

| 폴더명 | 설명 | 비고 |
| :--- | :--- | :--- |
| **`Dashboard`** | 전체 프로젝트의 **시각화 허브** 및 **공용 가상환경** 위치. | `venv` 폴더 포함 |
| **`Summariser`** | 뉴스 수집 및 요약 로직을 담당하는 핵심 모듈. | Gemini API 사용 |
| **`Slot machine`** | 독립적인 웹 게임 프로젝트. | HTML/JS/CSS |
| **`docs`** | **GitHub Pages 배포 폴더**. 빌드된 결과물이 여기에 저장됨. | **수동 수정 금지** |
| **`tests`** | 프로젝트 전체의 테스트 스크립트 모음. | 배포 전 필수 통과 |
| **`Auto trader`** | (진행 중) 자동 매매 관련 모듈. | |

---

## 2. ⚙️ 핵심 시스템 규칙 (Core System Rules)

### 2.1. 공용 가상환경 (Shared Virtual Environment)
- 모든 Python 프로젝트(`Dashboard`, `Summariser`, 등)는 **`Dashboard/venv`** 를 공용 가상환경으로 사용합니다.
- 새로운 패키지 설치 시:
  ```bash
  Dashboard\venv\Scripts\pip install 패키지명
  Dashboard\venv\Scripts\pip freeze > requirements.txt
  ```

### 2.2. 설정 관리 (Configuration)
- **전역 설정**: 루트의 `config.py`에서 관리합니다. (스케줄 시간, 배포 URL 등)
- **비밀 키**: `.env` 파일에서 관리하며, Git에 커밋하지 않습니다.
  - 필수 키: `GEMINI_API_KEY`, `KAKAO_REST_API_KEY`, `GITHUB_TOKEN` 등

### 2.3. 배포 (Deployment)
- **GitHub Pages**: `docs/` 폴더의 내용을 정적 웹사이트로 배포합니다.
### 2.3. 배포 (Deployment & Automation Pipeline)
- **GitHub Pages**: `docs/` 폴더의 내용을 정적 웹사이트로 배포합니다.
- **자동화 파이프라인 (Automated Pipeline)**:
  모든 모듈은 **[실행] -> [결과 생성] -> [전체 빌드/테스트/배포]** 순서로 동작합니다.

  1. **Summariser (뉴스 요약 모듈)**
     - **스케줄**: 09:00 (Morning), 18:30 (Evening)
     - **프로세스**: 
       1. YouTube 뉴스 수집 및 Gemini 요약 생성 -> `data/news/`에 JSON 저장.
       2. 로컬 리포트 페이지 생성 (`docs/reports/`).
       3. **`Canary Build`**: `build_test_deploy.bat auto` 호출.
          - 메인 대시보드 갱신 -> 테스트 -> GitHub 배포.
     - **알림**: 배포된 링크를 포함하여 카카오톡 전송.

  2. **Auto Trader (자동 매매 모듈 - 개발 중)**
     - **스케줄**: 10분 간격
     - **프로세스**: 
       1. 시세 확인 및 매매 로직 수행.
       2. 트레이딩 현황 데이터 갱신.
       3. **`Canary Build`**: `build_test_deploy.bat auto` 호출.
          - 메인 대시보드 갱신 -> 테스트 -> GitHub 배포.

  3. **통합 빌드 & 배포 (`build_test_deploy.bat`)**
     - **Build**: `Dashboard/builder.py`를 실행하여 모든 데이터(뉴스, 트레이딩 등)를 통합한 `index.html` 생성.
     - **Test**: `tests/run_all_tests.bat`로 전체 무결성 검증.
     - **Deploy**: 검증 통과 시 `Dashboard/deploy.py`로 GitHub Push.

### 2.4. 스케줄링 (Decentralized Scheduling)
- **독립적 스케줄링**: 각 모듈은 자신의 실행 주기를 관리하는 `register_schedule.bat`를 가집니다.
- **스케줄러 정리**: 루트의 `cleanup_all_tasks.bat`를 실행하면 등록된 모든 프로젝트 스케줄을 삭제할 수 있습니다.
- **프로젝트 루트 역할**: 스케줄링을 직접 관리하지 않으며, `build_test_deploy.bat`를 통해 통합 빌드/테스트/배포 도구를 제공합니다.

---

## 3. 👩‍💻 개발 가이드라인 (Development Guidelines)

### 3.1. 새로운 컴포넌트/폴더 추가 시
새로운 기능을 위해 폴더를 생성할 때는 다음 규칙을 따릅니다:

1. **독립성 유지**: 다른 모듈과 의존성을 최소화하고, 자체적인 실행 스크립트(`automation.bat` 등)를 가져야 합니다.
2. **공용 환경 사용**: 디스크 공간 절약을 위해 **`Dashboard/venv`** 를 공용으로 사용합니다. (필요 시 분리 가능)
3. **빌드 통합**: 결과물이 웹에 게시되어야 한다면, 해당 모듈이 `docs/` 내의 적절한 위치로 결과물을 복사하도록 해야 합니다.
4. **테스트 추가**: `tests/` 폴더에 해당 컴포넌트의 테스트 스크립트를 추가합니다.

### 3.2. 파일 명명 규칙 (Naming Conventions)
- **Python**: `snake_case` (예: `data_collector.py`)
- **HTML/CSS/JS**: `kebab-case` 또는 `camelCase` (일관성 유지)
- **배치 스크립트**: `snake_case` (예: `run_test.bat`)

### 3.3. 테스트 (Testing)
- 코드를 변경하거나 추가한 후에는 반드시 **전체 테스트**를 수행해야 합니다.
  ```cmd
  tests\run_all_tests.bat
  ```
- 테스트가 통과하지 않은 상태에서 `deploy.bat`를 실행하지 마십시오.

---

## 4. 🚨 주의사항 (Caveats)

- **`docs/` 폴더 수동 수정 금지**: 빌드 시 덮어씌워지므로, 원본 소스(`Dashboard/templates`, `Summariser/templates` 등)를 수정해야 합니다.
- **API Key 노출 주의**: 코드를 공유하거나 커밋할 때 `.env` 파일이 포함되지 않도록 `.gitignore`를 확인하세요.
