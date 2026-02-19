"""
암호화폐 자동매매 핵심 로직

이 파일은 기존 Auto trader/trader.py의 래퍼입니다.
Phase 2에서는 기존 코드를 유지하면서 새 모듈 구조에서 접근 가능하도록 합니다.
Phase 3에서 전체 리팩토링이 이루어집니다.

Refactored: uses core.config and core.logger.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the original Auto trader directory to path for backward compatibility
_AUTOTRADER_DIR = Path(__file__).resolve().parent.parent.parent / "Auto trader"
if str(_AUTOTRADER_DIR) not in sys.path:
    sys.path.insert(0, str(_AUTOTRADER_DIR))

from core.config import Config, PROJECT_ROOT
from core.logger import get_logger
from core.errors import isolated

log = get_logger("crypto_trader")


class CryptoTrader:
    """
    Wrapper around the existing AutoTrader that uses the new core infrastructure.
    Delegates to the original trader.py for actual trading logic.
    """

    def __init__(self):
        self.cfg = Config.instance()
        self.coins = self.cfg.get("crypto_trader.coins", [])
        self.interval = self.cfg.get("crypto_trader.interval_minutes", 60)

    def run_cycle(self):
        """Run one trading cycle using the legacy AutoTrader."""
        # Import the legacy AutoTrader
        from trader import AutoTrader

        # Build a legacy-compatible config object
        legacy_config = _build_legacy_config(self.cfg)

        trader = AutoTrader(legacy_config)
        trader.run_cycle()

        log.info("Trading cycle complete.")

    def get_status(self):
        """Read the current trading status from data/status.json."""
        status_file = _AUTOTRADER_DIR / "data" / "status.json"
        if status_file.exists():
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None


def _build_legacy_config(cfg: Config):
    """
    Build a legacy config object compatible with the original AutoTrader
    which expects config.COINS, config.TRADING, config.CAPITAL, etc.
    """

    class LegacyConfig:
        COINS = cfg.get("crypto_trader.coins", [])
        TRADING = {
            "interval_minutes": cfg.get("crypto_trader.interval_minutes", 60),
            "execution_cron": cfg.get("crypto_trader.schedule", "0 * * * *"),
            "interval": "minute60",
        }
        CAPITAL = cfg.get("crypto_trader.capital", {})
        # Map new YAML keys to old keys expected by trader.py
        RISK = {
            "risk_per_trade": cfg.get("crypto_trader.risk.risk_per_trade", 0.01),
            "stop_loss": cfg.get("crypto_trader.risk.stop_loss_default", -0.02),
            "take_profit": cfg.get("crypto_trader.risk.take_profit_min", 0.03),
        }
        GEMINI = {"model_name": cfg.get("ai.model", "gemini-2.5-flash")}

    return LegacyConfig()
