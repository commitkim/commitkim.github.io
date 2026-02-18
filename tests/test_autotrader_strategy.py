import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json
import pandas as pd

# Add project root and Auto trader dir
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'Auto trader')) # Priority for config.py
sys.path.append(PROJECT_ROOT)

from trader import AutoTrader
import config

class TestAutoTraderStrategy(unittest.TestCase):
    def setUp(self):
        self.config = config
        
        # Mock Environment Variables
        self.env_patcher = patch.dict(os.environ, {"GEMINI_API_KEY": "test_key", "UPBIT_ACCESS_KEY": "test", "UPBIT_SECRET_KEY": "test"})
        self.env_patcher.start()

        # Mock Upbit and Gemini
        self.patcher_upbit = patch('trader.pyupbit')
        self.patcher_genai = patch('trader.genai')
        self.mock_upbit = self.patcher_upbit.start()
        self.mock_genai = self.patcher_genai.start()
        
        self.trader = AutoTrader(self.config)
        self.trader.upbit = MagicMock() # Manually attach mock upbit instance

    def tearDown(self):
        self.patcher_upbit.stop()
        self.patcher_genai.stop()
        self.env_patcher.stop()

    def test_low_confidence_hold(self):
        """Test that confidence < 0.65 results in HOLD."""
        decision = {
            "action": "BUY",
            "confidence": 0.50, # Low confidence
            "position_size_percent": 10,
            "reason_code": "TEST"
        }
        
        balance_info = {'krw_balance': 1000000, 'coin_balance': 0, 'avg_buy_price': 0}
        total_capital = 1000000
        
        # Execute Trade
        self.trader.execute_trade('KRW-BTC', decision, 50000, balance_info, total_capital)
        
        # Should NOT buy
        self.trader.upbit.buy_market_order.assert_not_called()

    def test_high_confidence_buy(self):
        """Test that confidence >= 0.65 results in BUY."""
        decision = {
            "action": "BUY",
            "confidence": 0.80, # High confidence
            "position_size_percent": 5,
            "reason_code": "TEST"
        }
        
        balance_info = {'krw_balance': 1000000, 'coin_balance': 0, 'avg_buy_price': 0}
        total_capital = 1000000
        
        # Execute Trade
        self.trader.execute_trade('KRW-BTC', decision, 50000, balance_info, total_capital)
        
        # Should buy 5% of 1,000,000 = 50,000
        self.trader.upbit.buy_market_order.assert_called_with('KRW-BTC', 50000.0)

    def test_position_size_cap(self):
        """Test that position size is capped at 10%."""
        decision = {
            "action": "BUY",
            "confidence": 0.90,
            "position_size_percent": 20, # AI suggests 20%
            "reason_code": "TEST"
        }
        
        balance_info = {'krw_balance': 1000000, 'coin_balance': 0, 'avg_buy_price': 0}
        total_capital = 1000000
        
        # Execute Trade
        self.trader.execute_trade('KRW-BTC', decision, 50000, balance_info, total_capital)
        
        # Should buy capped 10% of 1,000,000 = 100,000
        self.trader.upbit.buy_market_order.assert_called_with('KRW-BTC', 100000.0)

    def test_max_coins_limit(self):
        """Test that new buys are blocked if max coins limit is reached."""
        # Simulate holding 3 coins already
        self.trader.get_held_coin_count = MagicMock(return_value=3)
        self.config.CAPITAL['max_coins_held'] = 3
        
        decision = {
            "action": "BUY",
            "confidence": 0.90,
            "position_size_percent": 5,
            "reason_code": "TEST"
        }
        
        balance_info = {'krw_balance': 1000000, 'coin_balance': 0, 'avg_buy_price': 0}
        total_capital = 1000000
        
        # Execute Trade
        self.trader.execute_trade('KRW-BTC', decision, 50000, balance_info, total_capital)
        
        # Should NOT buy
        self.trader.upbit.buy_market_order.assert_not_called()

    def test_sell_execution(self):
        """Test that SELL action executes correctly."""
        decision = {
            "action": "SELL",
            "confidence": 0.90,
            "reason_code": "TEST"
        }
        
        # Holding some BTC
        balance_info = {'krw_balance': 0, 'coin_balance': 0.1, 'avg_buy_price': 50000000}
        total_capital = 5000000
        current_price = 60000000
        
        # Execute Trade
        self.trader.execute_trade('KRW-BTC', decision, current_price, balance_info, total_capital)
        
        # Should sell all 0.1 BTC
        self.trader.upbit.sell_market_order.assert_called_with('KRW-BTC', 0.1)

if __name__ == '__main__':
    unittest.main()
