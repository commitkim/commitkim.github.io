
import sys
import os
import logging
from unittest.mock import MagicMock

# Adjust path
sys.path.append(os.path.join(os.getcwd(), 'Auto trader'))

# Mock config
class MockConfig:
    COINS = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-SOL', 'KRW-DOGE']
    CAPITAL = {'max_coins_held': 3, 'investment_per_trade': 0.1}
    TRADING = {'interval': 'minute60'}

import trader
trader.config = MockConfig()

# Subclass to mock methods
class TestTrader(trader.AutoTrader):
    def __init__(self):
        self.config = MockConfig()
        self.upbit = MagicMock()
        self.upbit.get_balances.return_value = [
            {'currency': 'KRW', 'balance': 1000000, 'avg_buy_price': 0},
            {'currency': 'BTC', 'balance': 0.1, 'avg_buy_price': 50000000},
            {'currency': 'ETH', 'balance': 1.0, 'avg_buy_price': 3000000},
            {'currency': 'XRP', 'balance': 1000.0, 'avg_buy_price': 500}
        ] # Currently holding 3 coins (Full)
        self.model = MagicMock()

    def get_market_data(self, ticker):
        return "DUMMY_DF"

    def get_balance_info(self, ticker):
        return {'krw_balance': 1000000, 'coin_balance': 0, 'avg_buy_price': 0}

    def analyze_market(self, ticker, df, balance_info, total_assets):
        # Scenario:
        # BTC (Held) -> SELL (To free up slot)
        # ETH (Held) -> HOLD
        # XRP (Held) -> HOLD
        # SOL (New) -> BUY (Conf 0.9)
        # DOGE (New) -> BUY (Conf 0.8)
        
        if ticker == 'KRW-BTC':
            return {"action": "SELL", "confidence": 0.5, "reason_code": "TEST_SELL"}
        elif ticker == 'KRW-ETH':
            return {"action": "HOLD", "confidence": 0.5, "reason_code": "TEST_HOLD"}
        elif ticker == 'KRW-XRP':
            return {"action": "HOLD", "confidence": 0.5, "reason_code": "TEST_HOLD"}
        elif ticker == 'KRW-SOL':
            return {"action": "BUY", "confidence": 0.9, "reason_code": "TEST_BUY_HIGH"}
        elif ticker == 'KRW-DOGE':
            return {"action": "BUY", "confidence": 0.8, "reason_code": "TEST_BUY_LOW"}
        
        return {"action": "HOLD", "confidence": 0}

    def execute_trade(self, ticker, decision, current_price, balance_info, total_assets):
        print(f"EXECUTE: {decision['action']} {ticker} (Conf: {decision.get('confidence')})")

    def save_status(self, results):
        pass
    
    # Mock get_held_coin_count to return 3 initially
    def get_held_coin_count(self):
        # This is called during the loop. 
        # In real life, it calls API.
        # Here we mimic the behavior:
        # Initial = 3.
        # If we sold BTC, it should be 2.
        # But we are mocking execute_trade, so we need to validly track this?
        # The logic in run_cycle calls get_held_coin_count ONCE before the buy loop.
        # Does it?
        # Let's check the code:
        # "current_slots = self.get_held_coin_count()" is called AFTER sell loop.
        # So we need to ensure this method returns the count *after* sells.
        # In this mock, get_balances returns static list.
        # So we should start with 2 if we assume BTC is sold?
        # No, execute_trade is mocked, so it won't actually sell.
        # So get_held_coin_count will still return 3 unless we mock it to return 2.
        
        # We need to simulate that BTC was sold.
        # Since I know BTC is sold in this specific test case, I'll return 2.
        return 2 

if __name__ == "__main__":
    t = TestTrader()
    print("--- Starting Cycle ---")
    t.run_cycle()
    print("--- End Cycle ---")
