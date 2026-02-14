# CommitKim 프로젝트 허브 📂

제 개인 프로젝트 모노레포에 오신 것을 환영합니다! 이 저장소는 다양한 개발 프로젝트를 관리하며, [메인 대시보드](https://commitkim.github.io)에서 한눈에 확인할 수 있습니다.

## 📂 프로젝트 목록

### 1. [대시보드 (Dashboard)](./Dashboard)
모든 프로젝트의 데이터를 모아 보여주는 중앙 허브 역할을 합니다.
- **기술 스택**: Python (Builder), Jinja2, TailwindCSS

### 2. [뉴스 요약 봇 (Summariser)](./Summariser)
매일 아침 유튜브 경제 뉴스(한국경제신문 모닝루틴)를 수집하고, AI(Gemini)로 요약하여 카카오톡으로 전송합니다.
- **기술 스택**: Python, YouTube API, Google Gemini, Kakao API

### 3. [슬롯 머신 (Slot Machine)](./Slot%20machine)
웹 브라우저에서 즐길 수 있는 간단한 슬롯 머신 게임입니다.
- **기술 스택**: HTML, CSS, JavaScript

## 🚀 배포 (Deployment)
이 프로젝트는 GitHub Pages를 통해 자동으로 배포됩니다.
`Dashboard`가 빌드되면 `Project/docs/` 폴더에 정적 사이트가 생성되고, 이 폴더가 호스팅됩니다.

### 수동 배포
프로젝트 루트에서 아래 스크립트를 실행하세요:
```bash
deploy.bat
```

## 🤖 자동화 (Automation)
매일 아침 9시에 뉴스 수집, 대시보드 업데이트, 배포를 자동으로 수행합니다.

### 1. 스케줄 등록
한 번만 실행하면 됩니다. (관리자 권한 필요)
```bash
setup_schedule.bat
```
이 스크립트는 기존의 `Summariser` 단독 스케줄을 삭제하고, 전체 통합 스케줄을 등록합니다.

### 2. 동작 방식 (`scheduled_job.bat`)
1.  **동적 실행**: 각 폴더(`Summariser`, `Dashboard`)의 `automation.bat`을 찾아 실행합니다.
2.  **Git Sync**: 변경된 모든 데이터를 커밋하고 GitHub에 푸시합니다.

## 📂 주요 스크립트 설명
| 파일명 | 설명 | 실행 시점 |
| :--- | :--- | :--- |
| **`deploy.bat`** | 수동 배포 스크립트. 수정 사항을 바로 반영하고 싶을 때 사용합니다. | 수동 실행 |
| **`setup_schedule.bat`** | 자동화 스케줄 등록 스크립트. `config.py`의 시간을 읽어 작업을 예약합니다. | 최초 1회 |
| **`scheduled_job.bat`** | 실제 자동화 로직이 담긴 스크립트. 스케줄러에 의해 매일 아침 실행됩니다. | 매일 아침 (자동) |
| **`config.py`** | 프로젝트 전체 설정 파일 (스케줄 시간 등). | 설정 변경 시 |
## 🧪 테스트 (Testing)
기능이 정상적으로 동작하는지 확인하려면 아래 스크립트를 실행하세요.

| 파일명 | 설명 |
| :--- | :--- |
| **`test_summariser.bat`** | 뉴스 수집 및 AI 요약 기능을 테스트합니다. (실제 Gemini API 호출) |
| **`test_dashboard.bat`** | 대시보드 사이트(HTML)가 정상적으로 빌드되는지 테스트합니다. |
| **`run_all_tests.bat`** | 위 두 가지 테스트를 순차적으로 모두 실행합니다. |

---
