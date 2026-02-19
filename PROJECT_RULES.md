# 📜 CommitKim Project Rules & Guidelines (v3.0)

이 문서는 **CommitKim Project Hub**의 구조, 운영 규칙, 개발 가이드를 정의합니다.
AI Agent에게 이 문서를 학습시키면 새로운 모듈을 규칙에 맞게 추가할 수 있습니다.

---

## 1. 📂 디렉토리 구조 및 역할

```
commitkim/
├── core/                  # 공유 인프라 — 설정, 로깅, 에러, 스케줄러
│   ├── config.py          # 계층형 YAML 설정 로더 (싱글턴)
│   ├── logger.py          # 표준 로거
│   ├── errors.py          # @retry, @isolated 데코레이터
│   └── scheduler/         # OS별 스케줄러 백엔드 + 공용 레지스트리
│       ├── registry.py    # JobDefinition, SchedulerRegistry
│       └── backends/      # windows.py / cron.py / process.py
├── modules/               # 비즈니스 로직 — 모듈간 의존 없음
│   ├── news_briefing/     # 뉴스 수집 / AI 요약
│   ├── crypto_trader/     # 암호화폐 자동매매
│   ├── messenger/         # 카카오톡 전송
│   └── site_builder/      # 정적 사이트 빌드 + Git 배포
├── apps/                  # CLI 진입점 + 파이프라인 오케스트레이션
│   └── cli.py             # 모든 명령의 단일 진입점
├── config/                # YAML 설정 파일 (base, dev, prod, test)
├── scripts/               # 운영 보조 스크립트
├── tests/                 # pytest 기반 테스트
├── data/                  # 런타임 데이터 (git-tracked)
│   ├── news/              # 뉴스 데이터 {mode}/{date}.json
│   └── trade/             # 매매 상태 status.json
├── docs/                  # ⚠️ 자동 생성 — 직접 수정 금지
└── .github/workflows/     # CI/CD
```

### 계층 규칙 (Dependency Rule)

```
core  →  modules  →  apps
```

| 계층 | import 가능 | import 금지 |
|------|-------------|-------------|
| `core/` | 표준 라이브러리, 외부 패키지 | modules, apps |
| `modules/` | core, 표준/외부 라이브러리 | 다른 modules, apps |
| `apps/` | core, modules, 모두 | — |

---

## 2. ⚙️ 핵심 시스템 규칙

### 2.1. 설정 관리 (Configuration)

```
config/base.yaml     # 공통 기본값
config/dev.yaml      # 개발 오버라이드
config/prod.yaml     # 운영 오버라이드
config/test.yaml     # 테스트 오버라이드
.env                 # 시크릿 (절대 커밋 금지)
```

```python
# ✅ 올바른 설정 접근 방법
from core.config import Config
cfg = Config.instance()                              # 싱글턴 — 반드시 instance() 사용
model = cfg.get("ai.model")                          # YAML 키 접근 (dot notation)
api_key = cfg.get_secret("GEMINI_API_KEY")           # .env 시크릿 접근

# ❌ 금지 — 새 인스턴스 생성
cfg = Config()   # 싱글턴을 깨뜨림, 절대 사용 금지
```

환경 선택: `COMMITKIM_ENV=dev` 또는 `--env dev` CLI 플래그

### 2.2. 가상환경 및 의존성

- 의존성 관리: **`pyproject.toml`** (requirements.txt 사용 금지)
- 가상환경: 프로젝트 루트에서 `pip install -e ".[dev]"` 또는 `pip install pyyaml python-dotenv …`
- 새 패키지 추가 시: `pyproject.toml`의 `[project.dependencies]` 또는 `[project.optional-dependencies]` 섹션에 추가

### 2.3. 배포 (Deployment)

- `docs/` 폴더가 GitHub Pages 루트
- 수동: `python -m apps.cli deploy`
- 자동: GitHub Actions → CI 통과 시 자동 배포

**⚠️ `docs/` 내 파일 직접 수정 금지** — 다음 빌드에서 완전히 덮어씌워짐

### 2.4. 스케줄링 (Centralized)

- 모든 주기 작업은 `modules/{module}/jobs.py`에서 `JobDefinition`으로 정의
- `core/scheduler/registry.py`의 `SchedulerRegistry`에 등록
- OS에 맞는 백엔드 자동 선택 (Windows Task Scheduler / cron / process)

```python
# ✅ jobs.py 작성 예시
from core.scheduler.registry import JobDefinition
from core.config import Config

def register_jobs(registry):
    cfg = Config.instance()   # ← 반드시 instance() 사용
    enabled = cfg.get("my_module.schedule_enabled", False)

    registry.register(JobDefinition(
        name="my_module_daily",        # 유일한 ID (snake_case)
        description="모듈 설명",
        schedule="0 9 * * 1-5",       # cron 5필드 표현식
        command="apps.cli run my_module",  # ← 'python -m' 제외 (backend가 자동 추가)
        tags=["my_module"],
        enabled=enabled,
    ))
```

**명령어**: `python -m apps.cli schedule --install | --list | --remove`

---

## 3. 👩‍💻 새로운 모듈 추가 체크리스트

> AI Agent에게 이 섹션을 학습시키면 새 모듈을 규칙에 맞게 추가할 수 있습니다.

### Step 1: 디렉토리 생성

```
modules/my_module/
├── __init__.py    # Public API export
├── jobs.py        # 스케줄 정의 (register_jobs 함수 필수)
└── engine.py      # 핵심 비즈니스 로직
```

### Step 2: `__init__.py` 작성

```python
"""my_module — 모듈 설명"""
from .engine import MyEngine
__all__ = ["MyEngine"]
```

### Step 3: `jobs.py` 작성 (위 2.4 예시 참고)

- `register_jobs(registry)` 함수 반드시 구현
- `command` 필드는 `"apps.cli ..."` 형식 (`python -m` 제외 — backend가 자동 추가)
- `Config.instance()` 사용 (절대 `Config()` 금지)

### Step 4: `config/base.yaml`에 설정 섹션 추가

```yaml
my_module:
  schedule_enabled: false   # 기본 비활성화
  # 모듈 전용 설정 추가
```

### Step 5: `apps/cli.py`에 CLI 명령 연결

```python
# run my_module
my_parser = run_sub.add_parser("my_module", help="Run my module")
my_parser.set_defaults(func=_run_my_module)
```

### Step 6: `apps/cli.py`의 `_schedule()` 함수에 jobs 등록

```python
from modules.my_module.jobs import register_jobs as register_my_module
register_my_module(registry)
```

### Step 7: GitHub Actions workflow 추가 (필요시)

`.github/workflows/my_module.yml` 생성:
- `on.schedule` 또는 `on.workflow_dispatch` 트리거
- `COMMITKIM_ENV: prod` 환경 변수
- `python -m apps.cli run my_module` 실행
- 배포 필요 시 `python -m apps.cli build` + git push 단계 추가

### Step 8: 테스트 작성

```
tests/test_my_module.py
```

- 외부 API 호출 전부 `unittest.mock.patch`로 mock
- `monkeypatch.setenv("COMMITKIM_ENV", "test")` 설정
- CI(`ci.yml`)에서 통과 가능해야 함

---

## 4. 🎨 UI/UX 규칙 (사이트 빌더)

### 4.1. 페이지 목록

| Page | URL | 설명 |
|------|-----|------|
| 메인 대시보드 | `/` (index.html) | 전체 현황 요약: 뉴스 최신 요약 + 매매 로그 상단 5개 |
| 뉴스 상세 | `/news/{date}.html` | 특정 날짜의 뉴스 전문 (웹 리포트) |
| 매매 기록 | `/trade.html` | 전체 매매 로그 (종목, 시간, 이유, 수익률) |

### 4.2. 레이아웃 규칙 (index.html / 메인 대시보드)

```
┌─────────────────────────────────────────┐
│  Header: 프로젝트명 + GitHub 링크 아이콘  │
├───────────────┬─────────────────────────┤
│   Sidebar     │   Main Content          │
│               │                         │
│  ■ 최신 뉴스   │  📰 뉴스 카드 (날짜별)   │
│    (날짜 목록)  │  🤖 매매 로그 (최근 5개) │
│  ■ 매매 현황   │                         │
│    (링크)      │                         │
└───────────────┴─────────────────────────┘
```

**사이드바 규칙**:
- 뉴스 섹션: 최근 7일치 날짜 목록 (클릭 시 해당 뉴스 상세 페이지로 이동)
- 매매 현황: `/trade.html` 링크
- 활성 페이지 항목은 강조 표시
- **⛔ 모듈 간 직접 이동 금지**: 사이드바에는 모든 모듈 링크를 노출하지만, 뉴스 상세(/news/*.html)나 매매 기록(/trade.html)에서 다른 기능 페이지로 직접 이동하는 내부 링크를 만들면 안 됩니다. 모든 이동은 메인 대시보드(`/`)를 경유해야 합니다.

**메인 콘텐츠 규칙**:
- 뉴스 카드: 날짜, 제목, kakao_summary (3줄 요약), 상세보기 링크
- 매매 로그: 코인 티커(Upbit 차트 링크), 액션(BUY/SELL/HOLD), 이유
- 로드 순서: 최신이 위

### 4.3. 색상 / 디자인 토큰

- 테마: 다크 모드 기반
- 액션 색상: BUY=녹색, SELL=빨강, HOLD=회색
- 폰트: 시스템 기본 폰트 (한국어 호환)
- 반응형: 모바일에서는 사이드바 숨김

### 4.4. 문서 구조 (Documentation Structure)

문서는 `docs/` 폴더에 생성되며, GitHub Pages를 통해 배포됩니다.

- **Root (`docs/`)**: 프로젝트 전체 대시보드 (`index.html`) 및 공용 자산 (`static/`)
- **Module Specific**: 각 모듈은 `docs/<module_name>/` 하위에 자신의 문서를 생성해야 합니다.
  - 예: `docs/news_briefing/index.html`, `docs/crypto_trader/index.html`
- **Asset Links**: 공용 자산은 `../../static/` 경로로 접근합니다.


### 4.5. KakaoTalk 메시지 포맷

```
📰 {title_prefix}

{kakao_summary}   ← 3개 이하의 글머리 목록
\n
[카카오톡 채널 링크]
```

- 최대 길이: 1,000자 이내 (카카오 제한)
- 줄바꿈: `\n` 사용
- 이모지 허용 (UTF-8 인코딩 필수)

---

## 5. 🔄 자동화 파이프라인

| 시간 | CLI 명령 | 동작 | 실행 환경 |
|------|---------|------|-----------|
| 09:00 (평일) | `run news --mode morning` | 아침 뉴스 → AI 요약 → 카카오톡 → 빌드 → 배포 | GA + Local |
| 18:30 (평일) | `run news --mode evening` | 저녁 뉴스 → AI 요약 → 카카오톡 → 빌드 → 배포 | GA + Local |
| 매시 정각 | `run trader` | 코인 분석 → 매매 → 대시보드 업데이트 → 배포 | Local 전용* |

*Upbit IP 화이트리스트 제한으로 `trader`는 로컬에서만 정상 실행됨.
GitHub Actions의 `trader.yml`은 `workflow_dispatch` (수동)만 지원.

---

## 6. 🧪 테스트 규칙

```bash
python -m pytest tests/ -v          # 전체 테스트
python -m pytest tests/ -k "crypto" # 특정 모듈 테스트
```

> [!IMPORTANT]
> **Test before Deploy**: 수동 배포(`apps.cli deploy`) 시에만 전체 테스트가 먼저 실행됩니다. `run news` 및 `run trader`에 의한 자동 배포는 테스트를 건너뛰고 즉시 배포합니다.

### 테스트 파일 명명 규칙

| 대상 | 파일명 |
|------|--------|
| core.config | `tests/test_core_config.py` |
| core.scheduler | `tests/test_core_scheduler.py` |
| core.errors | `tests/test_core_errors.py` |
| modules.crypto_trader | `tests/test_crypto_trader.py` |
| modules.news_briefing | `tests/test_news_briefing.py` |
| modules.site_builder | `tests/test_site_builder.py` |
| 모든 jobs.py | `tests/test_module_jobs.py` |

### 테스트 작성 규칙

1. **외부 API 전부 mock** — pyupbit, genai, requests, YouTubeTranscriptApi
2. **`monkeypatch.setenv("COMMITKIM_ENV", "test")` 필수** — test.yaml 설정 적용
3. **`Config._instance = None` 리셋** — 테스트 간 싱글턴 격리
4. CI에서 추가 패키지 설치 없이 통과해야 함 (외부 패키지는 mock)

---

## 7. 🔒 보안 규칙

- **`.env` 파일은 절대 git commit 금지** — `.gitignore`에 등록 확인
- **`kakao_tokens.json` 절대 commit 금지** — `.gitignore`에 등록 확인
- API Key는 `.env` 또는 GitHub Secrets에만 보관
- `config/` YAML 파일에 시크릿 저장 금지
- `get_secret("KAKAO_REST_API_KEY")` 패턴만 사용

---

## 8. 📝 파일 명명 규칙

| 유형 | 규칙 | 예시 |
|------|------|------|
| Python 파일 | `snake_case` | `news_briefing.py` |
| HTML/CSS/JS | `kebab-case` | `trade-log.html` |
| YAML 설정 키 | `snake_case` | `youtube_channel_id` |
| JobDefinition.name | `{module}_{action}` | `news_morning` |
| 데이터 파일 | `{YYYY-MM-DD}.json` | `2026-02-19.json` |

---

## 9. 🚨 주의사항

- **`docs/` 폴더 수동 수정 금지** — 빌드 시 전체 덮어씌워짐
- **모듈간 직접 import 금지** — apps 레이어에서만 조합
- **`Config()` 직접 생성 금지** — 반드시 `Config.instance()` 사용
- **jobs.py의 command에 `python -m` 포함 금지** — backend가 자동 추가 (중복 시 실행 실패)

---

## 🚀 Quick Reference 명령어

| 목적 | 명령어 |
|------|--------|
| 아침 뉴스 실행 | `python -m apps.cli run news --mode morning` |
| 저녁 뉴스 실행 | `python -m apps.cli run news --mode evening` |
| 자동매매 실행 | `python -m apps.cli run trader` |
| 사이트 빌드 | `python -m apps.cli build` |
| 배포 | `python -m apps.cli deploy` |
| 스케줄 확인 | `python -m apps.cli schedule --list` |
| 스케줄 등록 | `python -m apps.cli schedule --install` |
| 스케줄 삭제 | `python -m apps.cli schedule --remove` |
| 카카오 인증 | `python -m apps.cli setup kakao` |
| 전체 테스트 | `python -m pytest tests/ -v` |
| Help | `python -m apps.cli --help` |
