"""
Crypto Trader Wrapper
- Delegates to the new CryptoEngine in modules.crypto_trader.engine
- Replaces legacy Auto trader/trader.py usage
"""

import json
from pathlib import Path

from core.logger import get_logger
from core.errors import isolated
from core.config import PROJECT_ROOT

log = get_logger("crypto_trader")
STATUS_FILE = PROJECT_ROOT / "data" / "trade" / "status.json"


class CryptoTrader:
    """
    Wrapper around the CryptoEngine.
    """

    def __init__(self):
        pass

    @isolated("crypto_trader")
    def run_cycle(self):
        """Run one trading cycle using the new CryptoEngine."""
        from modules.crypto_trader.engine import CryptoEngine
        
        log.info("Starting trading cycle (New Engine)...")
        engine = CryptoEngine()
        engine.run_cycle()
        log.info("Trading cycle complete.")

    def get_status(self):
        """Read the current trading status from data/trade/status.json."""
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.error(f"Error reading status file: {e}")
        return None
