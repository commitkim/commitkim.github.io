
import sys
import os
import json
import logging
from datetime import datetime

# Adjust path
sys.path.append(os.path.join(os.getcwd(), 'Auto trader'))

# Create dummy trader class to test save_status method in isolation
class MockTrader:
    def __init__(self):
        self.upbit = None # Sim mode

    def save_status(self, trade_results):
        # COPY PASTED LOGIC FROM trader.py to test EXACT logic
        status_path = os.path.join(os.getcwd(), 'Auto trader', 'data', 'status.json')
        
        # Load existing data to preserve history
        existing_data = {}
        if os.path.exists(status_path):
            try:
                with open(status_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"Failed to load existing status: {e}")

        # Update Trade History (Append new results to existing ones)
        recent_trades = existing_data.get('recent_trades', [])
        
        # Add new trades
        recent_trades.extend(trade_results)
        
        # Keep only the last 100 trades
        recent_trades = recent_trades[-100:]

        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_assets': 0,
            'positions': {},
            'recent_trades': recent_trades
        }
        
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# Setup
data_dir = os.path.join('Auto trader', 'data')
os.makedirs(data_dir, exist_ok=True)
status_path = os.path.join(data_dir, 'status.json')

# 1. Reset status.json
with open(status_path, 'w', encoding='utf-8') as f:
    json.dump({'recent_trades': []}, f)

trader = MockTrader()

# 2. Save first batch
print("Saving batch 1...")
trader.save_status([{'id': 1}])
with open(status_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"Count after batch 1: {len(data['recent_trades'])}")

# 3. Save second batch
print("Saving batch 2...")
trader.save_status([{'id': 2}])
with open(status_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"Count after batch 2: {len(data['recent_trades'])}")

if len(data['recent_trades']) == 2:
    print("✅ Accumulation Works")
else:
    print("❌ Accumulation Failed")
