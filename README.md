# CommitKim Project Hub 📂

## 🤖 Auto Trader
**Gemini 2.0 Flash**를 활용한 업비트(Upbit) 자동 매매 봇입니다.
- **안전 제일**: 자본 보존을 최우선으로 하는 보수적인 알고리즘 탑재.
- **스마트 분석**: RSI, MACD, 볼린저 밴드 등 기술적 지표를 AI가 종합 분석.
- **자동화**: Windows 작업 스케줄러를 통해 24시간 자동 거래.
- **대시보드**: [Trading Status](docs/trade.html) 페이지에서 실시간 자산 및 거래 내역 확인 가능.

👉 [자세히 보기](Auto%20trader/README.md)

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

### 자동 배포 파이프라인 (Automated Pipeline)
각 모듈이 스케줄에 따라 실행된 후, 자동으로 **통합 빌드 → 테스트 → 배포** 과정을 트리거합니다.

1. **Summariser** (`register_schedule.bat`)
   - **Morning**: 매일 09:00 / **Evening**: 매일 18:30
   - **Flow**: [뉴스 수집/요약] → [로컬 저장] → [**전체 사이트 빌드 & 배포**] → [카톡 전송]

2. **Auto Trader** (`register_schedule.bat`)
   - **Frequency**: 10분 간격
   - **Flow**: [시세 확인/매매] → [**전체 사이트 빌드 & 배포**]

### 통합 파이프라인 (Build, Test & Deploy)
어떤 모듈이 실행되든 마지막에는 **Root Project**의 파이프라인을 거칩니다:
1. **Build**: `Dashboard/builder.py` (최신 데이터 반영)
2. **Test**: `tests/run_all_tests.bat` (무결성 검증)
3. **Deploy**: `Dashboard/deploy.py` (GitHub Pages Push)

### 수동 배포 및 관리
- `build_test_deploy.bat`: 수동으로 전체 사이트 빌드, 테스트, 배포를 일괄 실행합니다.
- `cleanup_all_tasks.bat`: 로컬에 등록된 모든 작업 스케줄을 삭제합니다.

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
