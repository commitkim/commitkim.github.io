"""
Unit tests for modules.crypto_trader — CryptoEngine

All external dependencies (pyupbit, google.genai) are mocked.
Tests validate trading logic, market analysis, and data flow in isolation.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set minimal env vars so CryptoEngine.__init__ does not crash."""
    monkeypatch.setenv("UPBIT_ACCESS_KEY", "test_access")
    monkeypatch.setenv("UPBIT_SECRET_KEY", "test_secret")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini")
    monkeypatch.setenv("COMMITKIM_ENV", "test")


@pytest.fixture()
def engine():
    """Return a CryptoEngine with all I/O mocked."""
    mock_client = MagicMock()

    with patch("modules.crypto_trader.engine.pyupbit") as mock_upbit, \
         patch("modules.crypto_trader.engine._get_gemini_client", return_value=mock_client):

        mock_upbit.Upbit.return_value = MagicMock()

        from core.config import Config
        Config._instance = None
        import modules.crypto_trader.engine as eng_mod
        eng_mod._gemini_client = None  # reset lazy client

        from modules.crypto_trader.engine import CryptoEngine
        eng = CryptoEngine()
        eng._mock_client = mock_client
        yield eng  # yield keeps the patch active during the test


# ---------------------------------------------------------------------------
# Tests: analyze_market
# ---------------------------------------------------------------------------

class TestAnalyzeMarket:
    def test_returns_hold_when_model_is_none(self, engine):
        """If Gemini model is unavailable, HOLD is returned."""
        engine.model = None
        result = engine.analyze_market("KRW-BTC", MagicMock(), {}, 1_000_000)
        assert result["action"] == "HOLD"
        assert result["reason_code"] == "API_ERROR"

    def test_parses_valid_json_response(self, engine):
        """Gemini response with valid JSON should be parsed correctly."""
        decision = {
            "action": "BUY",
            "position_size_percent": 20,
            "stop_loss_percent": 0.02,
            "take_profit_percent": 0.05,
            "confidence": 0.82,
            "reason_code": "TREND_ALIGNMENT",
        }
        mock_resp = MagicMock()
        mock_resp.text = json.dumps(decision)
        engine._mock_client.models.generate_content.return_value = mock_resp

        import pandas as pd
        import numpy as np
        n = 240
        df = pd.DataFrame({
            "close": [100.0 + i for i in range(n)],
            "open": [99.0 + i for i in range(n)],
            "high": [102.0 + i for i in range(n)],
            "low": [98.0 + i for i in range(n)],
            "volume": [1000.0] * n,
        })
        close = df["close"]
        df["ma5"] = close.rolling(5).mean()
        df["ma20"] = close.rolling(20).mean()
        df["ma60"] = close.rolling(60).mean()
        std20 = close.rolling(20).std()
        df["bb_upper"] = df["ma20"] + std20 * 2
        df["bb_lower"] = df["ma20"] - std20 * 2
        df["bb_mid"] = df["ma20"]
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = exp12 - exp26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        result = engine.analyze_market("KRW-BTC", df, {}, 1_000_000)
        assert result["action"] == "BUY"
        assert result["confidence"] == 0.82

    def test_returns_hold_on_api_exception(self, engine):
        """If Gemini raises, fall back to HOLD safely."""
        engine._mock_client.models.generate_content.side_effect = RuntimeError("API down")

        import pandas as pd
        n = 240
        df = pd.DataFrame({
            "close": [100.0 + i for i in range(n)],
            "open": [99.0 + i for i in range(n)],
            "high": [102.0 + i for i in range(n)],
            "low": [98.0 + i for i in range(n)],
            "volume": [1000.0] * n,
        })
        close = df["close"]
        df["ma5"] = close.rolling(5).mean()
        df["ma20"] = close.rolling(20).mean()
        df["ma60"] = close.rolling(60).mean()
        std20 = close.rolling(20).std()
        df["bb_upper"] = df["ma20"] + std20 * 2
        df["bb_lower"] = df["ma20"] - std20 * 2
        df["bb_mid"] = df["ma20"]
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = exp12 - exp26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        result = engine.analyze_market("KRW-BTC", df, {}, 1_000_000)
        assert result["action"] == "HOLD"
        assert result["reason_code"] == "API_ERROR"


# ---------------------------------------------------------------------------
# Tests: execute_trade
# ---------------------------------------------------------------------------

class TestExecuteTrade:
    def test_buy_skipped_on_low_confidence(self, engine):
        """BUY with confidence < 0.65 should not call buy_market_order."""
        engine.upbit = MagicMock()
        decision = {"action": "BUY", "confidence": 0.5,
                    "position_size_percent": 20, "reason_code": "LOW_CONFIDENCE"}
        engine.execute_trade("KRW-BTC", decision, 100_000, {"krw_balance": 500_000, "coin_balance": 0}, 1_000_000)
        engine.upbit.buy_market_order.assert_not_called()

    def test_buy_executed_on_high_confidence(self, engine):
        """BUY with high confidence and sufficient funds should call buy_market_order."""
        engine.upbit = MagicMock()
        engine.get_held_coin_count = MagicMock(return_value=0)
        decision = {"action": "BUY", "confidence": 0.9,
                    "position_size_percent": 20, "reason_code": "TREND_ALIGNMENT"}
        balance = {"krw_balance": 1_000_000, "coin_balance": 0, "avg_buy_price": 0}
        engine.execute_trade("KRW-BTC", decision, 100_000, balance, 1_000_000)
        engine.upbit.buy_market_order.assert_called_once()

    def test_sell_executed_when_holding(self, engine):
        """SELL with non-trivial coin balance should call sell_market_order."""
        engine.upbit = MagicMock()
        decision = {"action": "SELL", "confidence": 0.9, "reason_code": "TAKE_PROFIT"}
        balance = {"krw_balance": 0, "coin_balance": 0.01, "avg_buy_price": 80_000_000}
        # coin_balance * price = 0.01 * 100_000_000 = 1_000_000 > 5000
        engine.execute_trade("KRW-BTC", decision, 100_000_000, balance, 1_000_000)
        engine.upbit.sell_market_order.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: get_korean_reason
# ---------------------------------------------------------------------------

class TestGetKoreanReason:
    def test_known_code_returns_translation(self, engine):
        result = engine.get_korean_reason("LOSS_CUT")
        assert "[LOSS]" in result

    def test_unknown_code_returns_code_itself(self, engine):
        result = engine.get_korean_reason("SOME_UNKNOWN_CODE")
        assert result == "SOME_UNKNOWN_CODE"
