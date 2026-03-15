# 🚀 CommitKim Project Hub

**CommitKim**은 **Google Gemini AI** 기반의 개인 자동화 프로젝트입니다.
경제 뉴스 브리핑, 암호화폐 자동매매, 그리고 대시보드까지 하나의 시스템으로 동작합니다.

👉 [**Live Dashboard 보기**](https://commitkim.github.io)

---

## 🏛️ Architecture (v2.0)

```
commitkim/
├── core/               # 공유 인프라 (config, logger, errors, scheduler)
├── modules/            # 비즈니스 로직 (순수 파이썬, 모듈간 의존 없음)
│   ├── news_briefing/  # 뉴스 수집/요약 (was: Summariser)
│   ├── crypto_trader/  # 자동매매 (was: Auto trader)
│   ├── messenger/      # 카카오톡 전송 (중복 제거)
│   └── site_builder/   # 정적 사이트 빌드/배포 (was: Dashboard)
├── apps/               # CLI 진입점 + 오케스트레이션
├── config/             # YAML 설정 (base, dev, prod, test)
├── scripts/            # 운영 스크립트
├── tests/              # pytest 기반 테스트
├── docs/               # ⚠️ 자동 생성됨
│   ├── news_briefing/  # 뉴스 브리핑 문서
│   └── crypto_trader/  # 매매 현황 문서
└── .github/workflows/  # CI/CD (lint, test, deploy)
```

> ⚠️ **`docs/` 디렉토리는 자동 생성됩니다. 직접 수정하지 마세요.**
> `python -m apps.cli build` 명령으로 생성되며, 수동 편집 시 다음 빌드에서 덮어씌워집니다.

### 계층 구조 (Dependency Rule)

```
core  →  modules  →  apps
(의존 없음)  (core만 의존)  (modules + core 의존)
```


---

## 📜 Command Reference

프로젝트의 주요 명령어 목록입니다.

| Command | Description | Note |
| :--- | :--- | :--- |
| **`python -m apps.cli run news`** | 뉴스 브리핑 실행 | `--mode morning` or `evening` |
| **`python -m apps.cli run trader`** | 암호화폐 자동매매 실행 | 매시 정각 실행 권장 |
| **`python -m apps.cli build`** | 대시보드 사이트 빌드 | `docs/` 폴더 갱신 |
| **`python -m apps.cli deploy`** | GitHub Pages 배포 | `docs/` → `gh-pages` |
| **`python -m apps.cli schedule`** | 스케줄 관리 | `--install`, `--remove`, `--list` |
| `scripts/check_models.py` | Google Gemini 모델 확인 | 사용 가능한 모델 리스트 출력 |
| `data/trade/run_trader.bat` | 자동매매 간편 실행 | 윈도우용 배치 파일 |

더 자세한 옵션은 `python -m apps.cli --help`를 참고하세요.

---

## 🤖 Automated Pipeline

| 시간 | 모듈 | 동작 |
|------|------|------|
| ☀️ 09:00 (평일) | News Briefing | 아침 경제 뉴스 수집 → AI 요약 → 카카오톡 전송 |
| 🌙 18:30 (평일) | News Briefing | 퇴근요정 뉴스 브리핑 |
| 🤖 매시 정각 | Crypto Trader | 코인 분석 → Capital Survival 전략 매매 → 대시보드 업데이트 |

---

## 🛠️ Quick Start

### 1. 환경 설정

```bash
# .env 파일 생성 (API 키 설정)
cp .env.example .env
# .env 파일에 실제 API 키 입력

# 의존성 설치 (pyproject.toml 기준)
pip install -e .
# 또는 개발 의존성 포함
pip install -e ".[dev]"
```


```bash
# 뉴스 브리핑 실행
python -m apps.cli run news --mode morning

# 특정 날짜 뉴스 브리핑 실행
python -m apps.cli run news --mode morning --date 20260313


# 자동매매 실행
python -m apps.cli run trader

# 사이트 빌드
python -m apps.cli build

# GitHub Pages 배포
python -m apps.cli deploy

# 스케줄 확인/등록/삭제
python -m apps.cli schedule --list
python -m apps.cli schedule --install
python -m apps.cli schedule --remove

# 환경 지정
python -m apps.cli --env dev run trader

# 카카오톡 인증 설정
python -m apps.cli setup kakao
```

### 3. 테스트

```bash
python -m pytest tests/ -v
```

---

## 📁 Configuration

설정은 3단계로 병합됩니다:

1. `config/base.yaml` — 공통 기본값
2. `config/{env}.yaml` — 환경별 오버라이드 (dev/prod/test)
3. `.env` — API 키 (절대 커밋하지 않음)

환경 선택: `COMMITKIM_ENV=dev` 또는 `--env dev` CLI 플래그

---

## 🛡️ License & Disclaimer

- **AI-Generated Code**: 이 프로젝트의 코드는 AI Agent에 의해 작성되었습니다.
- **Investment Risk**: Auto Trader 사용에 따른 투자 결과의 책임은 사용자에게 있습니다.

---
*Created by CommitKim AI Agent*
