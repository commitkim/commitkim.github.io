import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json
import pandas as pd

# Add project root and Auto trader dir
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, 'Auto trader'))

from trader import AutoTrader

class MockConfig:
    COINS = ['KRW-BTC']
    TRADING = {'interval': 'minute60'}
    CAPITAL = {'investment_per_trade': 0.2, 'max_coins_held': 3}
    RISK = {'stop_loss': -3.0, 'take_profit': 5.0}
    GEMINI = {'model_name': 'gemini-2.0-flash'}

class TestAutoTrader(unittest.TestCase):
    def setUp(self):
        self.config = MockConfig()
        # Setup dummy data dir
        self.test_data_dir = os.path.join(PROJECT_ROOT, 'Auto trader', 'data')
        os.makedirs(self.test_data_dir, exist_ok=True)

    @patch('trader.pyupbit')
    @patch('trader.genai')
    def test_run_cycle(self, mock_genai, mock_upbit):
        # Mock Upbit Data
        # Ensure we have enough data points for MA60 (60+)
        data = {'close': [100 + i for i in range(100)]} 
        df = pd.DataFrame(data)
        mock_upbit.get_ohlcv.return_value = df
        mock_upbit.get_current_price.return_value = 200
        
        # Mock Upbit Class Instance
        mock_upbit_instance = mock_upbit.Upbit.return_value
        mock_upbit_instance.get_balance.side_effect = lambda ticker: 1000000 if ticker == "KRW" else 0
        mock_upbit_instance.get_balances.return_value = [
            {'currency': 'KRW', 'balance': '1000000', 'avg_buy_price': '0'},
            {'currency': 'BTC', 'balance': '0', 'avg_buy_price': '0'}
        ]
        
        # Mock Gemini
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # New response structure with confidence_score
        mock_response = MagicMock()
        mock_response.text = '{"decision": "buy", "confidence_score": 90, "reason": "Test reason", "suggested_stop_loss": 190, "suggested_take_profit": 210}'
        mock_model.generate_content.return_value = mock_response

        # Initialize Trader
        with patch.dict(os.environ, {'UPBIT_ACCESS_KEY': 'test', 'UPBIT_SECRET_KEY': 'test', 'GEMINI_API_KEY': 'test'}):
            trader = AutoTrader(self.config)
            
            # Run Cycle
            results = trader.run_cycle()
            
            # Assertions
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['decision'], 'buy')
            self.assertEqual(results[0]['ticker'], 'KRW-BTC')
            
            # Verify buy order
            # investment = 1,000,000 * 0.2 = 200,000
            mock_upbit_instance.buy_market_order.assert_called_with('KRW-BTC', 200000.0)

if __name__ == '__main__':
    unittest.main()
