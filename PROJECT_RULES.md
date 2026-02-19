# 📜 CommitKim Project Rules & Guidelines (v2.0)

이 문서는 **CommitKim Project Hub**의 구조와 운영 규칙을 정의합니다.

---

## 1. 📂 디렉토리 구조 및 역할

```
commitkim/
├── core/               # 공유 인프라 — 설정, 로깅, 에러, 스케줄러
├── modules/            # 비즈니스 로직 — 모듈간 의존 없음
│   ├── news_briefing/  # 뉴스 수집 / AI 요약
│   ├── crypto_trader/  # 암호화폐 자동매매
│   ├── messenger/      # 카카오톡 전송
│   └── site_builder/   # 정적 사이트 빌드 + Git 배포
├── apps/               # CLI 진입점 + 파이프라인 오케스트레이션
├── config/             # YAML 설정 파일 (base, dev, prod, test)
├── scripts/            # 운영 스크립트 (register_all.py 등)
├── tests/              # pytest 기반 테스트
├── docs/               # ⚠️ 자동 생성 — 직접 수정 금지
├── Slot machine/       # 독립 웹 게임 (HTML/JS/CSS)
└── .github/workflows/  # CI/CD
```

### 계층 규칙 (Dependency Rule)

```
core  →  modules  →  apps
```

- `core/` : 외부 의존 없음. 다른 모든 계층에서 import 가능
- `modules/` : `core/`만 import 가능. 모듈끼리 서로 import 금지
- `apps/` : `core/` + `modules/` import 가능. 최종 조합만 담당

---

## 2. ⚙️ 핵심 시스템 규칙

### 2.1. 설정 관리 (Configuration)
```
config/base.yaml     # 공통 기본값
config/dev.yaml      # 개발 오버라이드
config/prod.yaml     # 운영 오버라이드
.env                 # 시크릿 (절대 커밋 금지)
```

- 설정 접근: `Config.instance().get("news_briefing.modes.morning.keyword")`
- 시크릿 접근: `Config.instance().get_secret("GEMINI_API_KEY")`
- 환경 선택: `COMMITKIM_ENV=dev` 또는 `--env dev` CLI 플래그

### 2.2. 가상환경
- 모든 Python 코드는 `Dashboard/venv` 공용 가상환경 사용
- 의존성 관리: `pyproject.toml`

### 2.3. 배포 (Deployment)
- `docs/` 폴더가 GitHub Pages 루트
- 수동: `python -m apps.cli deploy`
- 자동: GitHub Actions (`deploy.yml`) → CI 통과 시 자동 배포

### 2.4. 스케줄링 (Centralized)
- 모든 주기 작업은 `core/scheduler/registry.py`에 등록
- 등록/조회/삭제: `python -m apps.cli schedule --install/--list/--remove`
- OS에 맞는 백엔드가 자동 선택됨 (Windows Task Scheduler / cron)

---

## 3. 👩‍💻 개발 가이드라인

### 3.1. 새로운 모듈 추가
1. `modules/모듈명/` 디렉토리 생성
2. `core.config`와 `core.logger`만 import
3. 다른 모듈 직접 import 금지 (앱 레이어에서 조합)
4. `jobs.py`에 스케줄 정의 추가
5. `tests/test_모듈명.py` 테스트 작성

### 3.2. 파일 명명 규칙
- **Python**: `snake_case` (예: `news_briefing.py`)
- **HTML/CSS/JS**: `kebab-case` 또는 `camelCase`
- **YAML 설정 키**: `snake_case` (예: `youtube_channel_id`)

### 3.3. 에러 처리
- 외부 API 호출: `@retry(max_retries=3)` 사용
- 독립 실행 함수: `@isolated()` 사용 (실패해도 시스템 중단 방지)

### 3.4. 테스트
```bash
python -m pytest tests/ -v     # 전체 테스트
python -m pytest tests/ -k "config"  # 특정 테스트만
```

---

## 4. 🤖 자동화 파이프라인

| 시간 | CLI 명령 | 동작 |
|------|---------|------|
| 09:00 (평일) | `run news --mode morning` | 아침 뉴스 → AI 요약 → 카카오톡 → 빌드 → 배포 |
| 18:30 (평일) | `run news --mode evening` | 저녁 뉴스 → AI 요약 → 카카오톡 → 빌드 → 배포 |
| 매시 정각 | `run trader` | 코인 분석 → 매매 → 대시보드 업데이트 → 배포 |

---

## 5. 🚨 주의사항

- **`docs/` 폴더 수동 수정 금지** — 빌드 시 덮어씌워짐
- **API Key 노출 주의** — `.env`는 `.gitignore`에 등록되어 있지만 항상 확인
- **모듈간 직접 import 금지** — 반드시 `apps/` 레이어에서만 조합
