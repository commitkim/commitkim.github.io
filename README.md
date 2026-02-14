# CommitKim Project Hub 📂

**AI-Powered Development Mono-repo**
*This project and all its documentation are generated and maintained by Google's Agentic AI.*

[메인 대시보드 바로가기](https://commitkim.github.io)

---

## 📂 프로젝트 목록

### 1. [대시보드 (Dashboard)](./Dashboard)
모든 프로젝트의 데이터를 시각화하는 중앙 허브입니다.
- **기술 스택**: Python (Static Site Generator), Jinja2, TailwindCSS
- **기능**: 뉴스 요약 아카이브, 슬롯머신 연동, 반응형 UI

### 2. [뉴스 요약 봇 (Summariser)](./Summariser)
매일 아침과 저녁, 경제 뉴스를 수집하고 AI로 요약하여 배달합니다.
- **기술 스택**: Python, YouTube API, **Google Gemini 2.0 Flash**, Kakao API
- **기능**: Morning(모닝루틴) & Evening(퇴근요정) 듀얼 모드 지원 → AI 요약 → 카카오톡 전송 → 웹 리포트 생성

### 3. [슬롯 머신 (Slot Machine)](./Slot%20machine)
다이어트 내기를 위한 웹 게임입니다.
- **기술 스택**: HTML5, CSS3, Vanilla JS
- **기능**: 웹 오디오 효과, 로컬 스토리지 데이터 저장, 반응형 디자인

---

## 🚀 배포 (Deployment)

이 프로젝트는 **GitHub Pages**를 통해 호스팅됩니다.
`Dashboard`와 `Summariser`가 생성한 정적 파일들이 `docs/` 폴더에 모이고, 이 폴더가 웹사이트로 배포됩니다.

### 자동 배포 (Daily Schedule)
Windows 작업 스케줄러를 통해 하루 두 번 실행됩니다:
1. **오전 09:00**: [모닝루틴] 아침 경제 뉴스 요약 및 배포
2. **오후 18:30**: [퇴근요정] 저녁 퇴근길 경제 뉴스 요약 및 배포

### 수동 배포 및 관리
- `deploy.bat`: 전체 테스트 및 빌드 후 배포 실행
- `cleanup_old_tasks.bat`: 구버전 단일 작업 스케줄러 정리

---

## 🧪 테스트 (Testing)

모든 변경 사항은 안전하게 테스트된 후 배포됩니다.

| 스크립트 | 설명 | 비고 |
| :--- | :--- | :--- |
| **`tests\run_all_tests.bat`** | **전체 테스트**. 배포 전 필수 통과 항목. | Mock 사용 (안전) |
| `tests\test_summariser.bat` | 뉴스 수집 및 요약 로직 검증. | Mock 사용 (안전) |
| `tests\test_dashboard.bat` | 대시보드 빌드 무결성 검증. | Temp 폴더 사용 |
| **`tests\test_live.bat`** | **실통합 테스트**. 실제 API 호출 포함. | **비용 발생 주의** |

---

## 🤖 AI Disclaimer
이 프로젝트의 코드, 문서, 아키텍처는 대부분 **AI Agent**에 의해 생성되었습니다.
- **Role**: Full Stack Developer & DevOps Engineer
- **Model**: Gemini 2.0 Pro Experimental / Flash
