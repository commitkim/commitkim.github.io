# core/ — 공유 인프라

모든 모듈이 공통으로 사용하는 기반 코드입니다.

| 파일 | 역할 |
|------|------|
| `config.py` | YAML 기반 계층 설정 로더 (base → env → .env) |
| `logger.py` | 통합 로깅 팩토리 (콘솔 + 파일 로테이션) |
| `errors.py` | 커스텀 예외 + `@isolated` + `@retry` 데코레이터 |
| `scheduler/` | 스케줄러 레지스트리 + OS별 백엔드 (Windows/cron/process) |

## 사용법

```python
from core.config import Config
from core.logger import get_logger
from core.errors import isolated, retry

cfg = Config.instance()
log = get_logger("my_module")

api_key = cfg.get_secret("GEMINI_API_KEY")
model = cfg.get("ai.model", "gemini-2.5-flash")
```
