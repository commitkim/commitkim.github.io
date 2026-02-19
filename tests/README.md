# tests/ — 테스트

pytest 기반 테스트 모음입니다.

## 실행

```bash
# 전체 테스트
python -m pytest tests/ -v

# 특정 모듈만
python -m pytest tests/test_core_config.py -v

# 키워드 필터
python -m pytest tests/ -k "retry" -v
```

## 테스트 파일

| 파일 | 대상 |
|------|------|
| `test_core_config.py` | YAML 설정 로딩, 환경 오버라이드, 시크릿 |
| `test_core_errors.py` | 예외 계층, @isolated, @retry |
| `test_core_logger.py` | 로거 팩토리, 핸들러, 파일 출력 |
| `test_core_scheduler.py` | 잡 레지스트리, 태그 필터, 비활성화 |
| `test_autotrader_strategy.py` | 매매 전략 유닛 테스트 |
