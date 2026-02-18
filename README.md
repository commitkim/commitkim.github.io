# 🚀 CommitKim Project Hub

**CommitKim**은 **Google Gemini 2.0 Flash** 기반의 AI Agent가 100% 코딩하고 운영하는 **"자율 주행 개인 비서 프로젝트"**입니다.
경제 뉴스 브리핑부터 암호화폐 자동 매매, 그리고 이 모든 것을 시각화하는 대시보드까지 하나의 유기적인 시스템으로 동작합니다.

👉 [**Live Dashboard 보기**](https://commitkim.github.io)

---

## 🏛️ Project Architecture (Mono-repo)

이 프로젝트는 4개의 핵심 모듈이 독립적이면서도 유기적으로 연결되어 있습니다.

| 모듈 (Module) | 역할 (Role) | 핵심 기술 (Tech Stack) |
| :--- | :--- | :--- |
| [**1. Summariser**](./Summariser) | **뉴스 브리핑 봇**<br>매일 아침/저녁, 경제 뉴스를 요약하여 카카오톡으로 전송합니다. | Python, YouTube API, Gemini 2.0, KakaoTalk API |
| [**2. Auto Trader**](./Auto%20trader) | **자율 매매 봇**<br>업비트에서 24시간 시세를 감시하며 "자본 생존" 전략으로 안전하게 투자합니다. | Python, Upbit API, Gemini 2.0, Tech Analysis |
| [**3. Dashboard**](./Dashboard) | **관제 센터**<br>뉴스 리포트 아카이브와 실시간 트레이딩 현황을 웹으로 시각화합니다. | Python (SSG), Jinja2, TailwindCSS |
| [**4. Slot Machine**](./Slot%20machine) | **미니 게임**<br>다이어트 내기를 위한 재미있는 웹 게임입니다. | HTML5, CSS3, Vanilla JS |

---

## � Automated Pipeline (Workflows)

모든 시스템은 **Windows Task Scheduler**에 의해 24시간 자동으로 돌아갑니다.

### ☀️ Morning Routine (09:00)
1.  **Summariser**가 밤사이 경제 뉴스를 수집합니다.
2.  **Gemini AI**가 "모닝 브리핑" 스타일로 요약합니다.
3.  **KakaoTalk**으로 요약본을 전송하고, **Web Report**를 생성합니다.
4.  **GitHub Pages**에 자동으로 배포됩니다.

### 🌙 Evening Briefing (18:30)
1.  **Summariser**가 "퇴근요정" 모드로 실행됩니다.
2.  오늘 하루의 주요 이슈를 정리하여 배달합니다.

### 🤖 Auto Trading (Every 60 mins)
1.  **Auto Trader**가 매시 정각 10분, 비트코인 등 주요 코인을 분석합니다.
2.  **Capital Survival** 전략에 따라 매수/매도/관망을 결정합니다.
3.  거래 내역과 자산 변동 사항을 **Dashboard**에 즉시 업데이트합니다.

---

## 🛠️ Installation & Usage

이 프로젝트는 로컬 Windows 환경에서 동작하도록 설계되었습니다.

### 1. 환경 설정 (Environment)
각 모듈 폴더의 `requirements.txt`를 설치하고 `.env` 파일을 설정해야 합니다.
```bash
# Dashboard (Build System)
pip install -r Dashboard/requirements.txt

# Summariser & Auto Trader
pip install -r Summariser/requirements.txt
```

### 2. 자동화 등록 (Scheduling)
프로젝트 루트의 `register_schedule.bat`를 관리자 권한으로 실행하면 모든 스케줄이 등록됩니다.

### 3. 수동 배포 (Manual Deploy)
코드 수정 후 즉시 배포하려면:
```bash
build_test_deploy.bat
```

---

## 🛡️ License & Disclaimer

*   **AI-Generated Code**: 이 프로젝트의 모든 코드는 Google의 Agentic AI에 의해 작성되었습니다.
*   **Investment Risk**: Auto Trader 모듈 사용에 따른 투자 결과의 책임은 전적으로 사용자에게 있습니다.

---
*Created by CommitKim AI Agent*
