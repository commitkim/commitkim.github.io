# 🤖 Upbit Auto Trader (CommitKim)

**Gemini 2.0 Flash** 기반의 지능형 암호화폐 자동 매매 봇입니다. Upbit API를 사용하여 시장 데이터를 수집하고, AI가 기술적 지표를 분석하여 안전하고 보수적인 투자를 수행합니다.

## ✨ 주요 기능

*   **AI 기반 분석**: Gemini 2.0 Flash 모델이 OHLCV 및 보조지표(RSI, MACD, BB 등)를 분석하여 매매 여부를 결정합니다.
*   **자본 보존 전략 (Capital Preservation)**:
    *   **투기 방지**: 확실한 상승 추세나 반등 신호가 없으면 `HOLD`를 유지합니다.
    *   **분할 매수**: 한 종목당 전체 자본의 20%만 투입합니다.
    *   **포트폴리오 제한**: 최대 3개 종목까지만 보유하여 리스크를 분산합니다.
*   **리스크 관리**:
    *   **손절매 (Stop Loss)**: -3% 도달 시 즉시 매도.
    *   **익절매 (Take Profit)**: +5% 도달 시 수익 실현.
    *   **신뢰도 점수**: AI의 확신(Confidence Score)이 80점 미만이면 매수하지 않습니다.
*   **상태 대시보드**: 거래 내역과 자산 현황을 웹 대시보드(`trade.html`)에서 실시간으로 확인할 수 있습니다.
*   **실행 로그**: `logs/` 폴더에 매일 실행 및 거래 내역이 기록됩니다.

## 🚀 시작하기

### 0. 사전 준비
*   Upbit 계정 및 API Key (Access/Secret)
*   Google Gemini API Key
*   `.env` 파일 설정:
    ```env
    UPBIT_ACCESS_KEY=your_key
    UPBIT_SECRET_KEY=your_key
    GEMINI_API_KEY=your_key
    ```

### 1. 설정 (Config)
`Auto trader/config.py`에서 트레이딩 전략을 상세하게 조정할 수 있습니다.
*   `COINS`: 거래할 코인 목록 (예: KRW-BTC, KRW-ETH)
*   `CAPITAL`: 투자 비율 및 최대 보유 개수
*   `RISK`: 손절/익절 비율
*   `TRADING`: 캔들 간격(interval) 및 스케줄

### 2. 실행
#### 수동 실행 (1회 루프)
```bash
python "Auto trader/main.py"
```
봇이 한 사이클을 돌며 시장을 분석하고 거래를 수행한 뒤 종료됩니다. (스케줄러 모드가 아님)

#### 스케줄러 등록 (자동 실행)
프로젝트 루트의 `register_schedule.bat`를 실행하면 윈도우 작업 스케줄러에 등록되어 24시간 자동으로 돌아갑니다.

---
**주의**: 투자의 책임은 전적으로 사용자에게 있습니다. 이 봇은 보조 도구일 뿐이며 수익을 보장하지 않습니다.
