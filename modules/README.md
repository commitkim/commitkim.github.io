# modules/ — 비즈니스 로직

각 모듈은 독립적으로 동작하며, `core/`만 의존합니다.
모듈간 직접 import는 금지 — `apps/` 레이어에서 조합합니다.

| 모듈 | 원본 | 역할 |
|------|------|------|
| `news_briefing/` | Summariser | YouTube 뉴스 수집 + Gemini AI 요약 |
| `crypto_trader/` | Auto trader | 업비트 자동매매 (Capital Survival 전략) |
| `messenger/` | 중복 제거 | 카카오톡 메시지 전송 |
| `site_builder/` | Dashboard | 정적 사이트 빌드 + Git 배포 |
