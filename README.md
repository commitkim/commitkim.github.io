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

### 배포 방법
프로젝트 루트에서 아래 스크립트를 실행하세요:
```bash
deploy.bat
```
이 스크립트는 다음 작업을 수행합니다:
1. 대시보드 빌드 (최신 데이터 집계)
2. 모든 변경 사항 커밋
3. GitHub 원격 저장소로 푸시
