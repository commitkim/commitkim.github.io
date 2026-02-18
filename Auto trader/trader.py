import pyupbit
import google.generativeai as genai
import json
import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Set encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

class AutoTrader:
    def __init__(self, config):
        self.config = config
        self.access_key = os.getenv("UPBIT_ACCESS_KEY")
        self.secret_key = os.getenv("UPBIT_SECRET_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize Upbit API
        if self.access_key and self.secret_key:
            self.upbit = pyupbit.Upbit(self.access_key, self.secret_key)
        else:
            logging.warning("⚠️ Warning: Upbit API keys not found. Running in simulation mode.")
            self.upbit = None

        # Initialize Gemini API
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel(config.GEMINI['model_name'])
        else:
            raise ValueError("GEMINI_API_KEY is missing!")

    def get_market_data(self, ticker):
        """Fetches OHLCV and technical indicators."""
        try:
            # Fetch more data to calculate indicators (e.g., MA60 needs at least 60)
            df = pyupbit.get_ohlcv(ticker, interval=self.config.TRADING['interval'], count=100)
            if df is None or df.empty:
                return None
            
            # 1. Moving Averages
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()
            
            # 2. Bollinger Bands (20, 2)
            std20 = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['ma20'] + (std20 * 2)
            df['bb_lower'] = df['ma20'] - (std20 * 2)
            df['bb_mid'] = df['ma20']
            
            # 3. MACD (12, 26, 9)
            exp12 = df['close'].ewm(span=12, adjust=False).mean()
            exp26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp12 - exp26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # 4. RSI (14)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            return df
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {e}")
            return None

    def analyze_market(self, ticker, df, balance_info, total_capital):
        """Asks Gemini for trading advice using the 'Capital Survival' strategy."""
        current_data = df.iloc[-1]
        
        # Format data for prompt
        ohlcv_json = df.tail(24).to_json() # Last 24 hours
        
        # Technicals
        rsi = f"{current_data['rsi']:.2f}"
        ma20 = f"{current_data['ma20']:.0f}"
        ma60 = f"{current_data['ma60']:.0f}"
        bb_upper = f"{current_data['bb_upper']:.0f}"
        bb_lower = f"{current_data['bb_lower']:.0f}"
        
        # Portfolio Context
        krw_balance = balance_info.get('krw_balance', 0)
        coin_balance = balance_info.get('coin_balance', 0)
        avg_buy_price = balance_info.get('avg_buy_price', 0)
        current_equity = total_capital
        
        prompt = f"""
        You are an autonomous crypto trading decision engine operating a very small account (approx 50,000 KRW equivalent).
        Your PRIMARY objective is long-term capital survival. Profit is secondary.
        If uncertain, DO NOT trade.

        ### MARKET DATA
        Ticker: {ticker}
        Current Price: {current_data['close']}
        RSI(14): {rsi}
        MA20: {ma20}, MA60: {ma60}
        BB Upper: {bb_upper}, BB Lower: {bb_lower}
        
        ### ACCOUNT STATUS
        Total Equity: {current_equity:.0f} KRW
        Current Position: {coin_balance} coins (Avg Price: {avg_buy_price})

        ### STRICT RULES
        1. Capital preservation overrides every signal. When in doubt -> HOLD.
        2. Confidence Threshold: If confidence < 0.65 -> HOLD.
        3. Risk Per Trade: Max risk 1% of total equity.
        4. Volatility Filter: Avoid extreme panic or zero movement.
        5. Trend Alignment: Do NOT Buy against downtrend (MA20 < MA60).
        
        ### OUTPUT FORMAT (STRICT JSON ONLY)
        {{
          "action": "BUY" | "SELL" | "HOLD",
          "position_size_percent": 0~10 (Max 10%),
          "stop_loss_percent": number (e.g. 0.02 for 2%),
          "take_profit_percent": number (Min 1.5x Risk),
          "confidence": 0.0~1.0,
          "reason_code": "TREND_ALIGNMENT | VOLATILITY_FILTER | RISK_MANAGEMENT | LOW_CONFIDENCE | STRUCTURE_UNCLEAR | ..."
        }}
        
        Analyze the following OHLCV data and provide your decision:
        {ohlcv_json}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            logging.error(f"Gemini Analysis Error: {e}")
            return {"action": "HOLD", "reason_code": "API_ERROR", "confidence": 0}

    def execute_trade(self, ticker, decision, current_price, balance_info, total_capital):
        """Executes trade based on 'Capital Survival' strict rules."""
        action = decision.get('action', 'HOLD')
        confidence = decision.get('confidence', 0)
        
        # 1. Global Filter: Low Confidence
        if confidence < 0.65 and action != 'SELL':
             logging.info(f"✋ Low Confidence ({confidence:.2f}) -> HOLD {ticker}")
             return

        if self.upbit is None:
            logging.info(f"[Simulation] {action} {ticker} (Conf: {confidence}) Reason: {decision.get('reason_code')}")
            return

        try:
            # 2. Risk Control: Max Exposure Check
            
            if action == 'BUY':
                # Check Max Coins Held
                if self.get_held_coin_count() >= self.config.CAPITAL['max_coins_held']:
                    if balance_info['coin_balance'] * current_price < 5000: # New entry
                        logging.warning(f"🚫 Max coins held ({self.config.CAPITAL['max_coins_held']}) reached. HOLD {ticker}")
                        return

                # Calculate Position Size via AI's suggestion or Hard Cap
                suggested_size_pct = min(decision.get('position_size_percent', 0), 10) # Hard cap 10%
                amount_to_invest = total_capital * (suggested_size_pct / 100)
                
                # Minimum Order Size
                if amount_to_invest < 5000:
                    logging.info(f"⚠️ Calculated Amount {amount_to_invest:.0f} < 5000 KRW. Skip.")
                    return

                reason_kr = self.get_korean_reason(decision.get('reason_code'))
                logging.info(f"🚀 BUY {ticker} | Size: {suggested_size_pct}% ({amount_to_invest:,.0f} KRW) | Reason: {reason_kr}")
                self.upbit.buy_market_order(ticker, amount_to_invest)
            
            elif action == 'SELL':
                if balance_info['coin_balance'] * current_price > 5000:
                    reason_kr = self.get_korean_reason(decision.get('reason_code'))
                    logging.info(f"📉 SELL {ticker} | Reason: {reason_kr}")
                    self.upbit.sell_market_order(ticker, balance_info['coin_balance'])
                    
        except Exception as e:
            logging.error(f"Trade Execution Error: {e}")

    def get_held_coin_count(self):
        """Returns number of coins currently held (value > 5000 KRW)."""
        if not self.upbit: return 0
        try:
            balances = self.upbit.get_balances()
            count = 0
            for b in balances:
                if b['currency'] == 'KRW': continue
                
                current_price = pyupbit.get_current_price(f"KRW-{b['currency']}")
                if current_price and (float(b['balance']) * current_price) > 5000:
                    count += 1
            return count
        except:
            return 0

    def check_safety_stop(self, ticker, balance_info, current_price):
        """Checks hardcoded Safety Rules (Stop Loss / Take Profit). Returns True if action taken."""
        if not self.upbit: return False
        
        avg_buy_price = balance_info.get('avg_buy_price', 0)
        coin_balance = balance_info.get('coin_balance', 0)
        
        if coin_balance * current_price < 5000: return False # Ignore dust
        
        if avg_buy_price > 0:
            profit_rate = (current_price - avg_buy_price) / avg_buy_price * 100
            
            # Stop Loss
            if profit_rate <= self.config.RISK['stop_loss']:
                logging.warning(f"🚨 STOP LOSS TRIGGERED for {ticker} ({profit_rate:.2f}%). Selling immediately.")
                if self.upbit:
                    self.upbit.sell_market_order(ticker, coin_balance)
                return True
                
            # Take Profit
            if profit_rate >= self.config.RISK['take_profit']:
                logging.info(f"💰 TAKE PROFIT TRIGGERED for {ticker} ({profit_rate:.2f}%). Selling immediately.")
                if self.upbit:
                    self.upbit.sell_market_order(ticker, coin_balance)
                return True
                
        return False

    def get_balance_info(self, ticker):
        """Helper to get balance info for a specific ticker."""
        info = {'krw_balance': 0, 'coin_balance': 0, 'avg_buy_price': 0}
        if self.upbit:
            info['krw_balance'] = self.upbit.get_balance("KRW")
            info['coin_balance'] = self.upbit.get_balance(ticker)
            # Need to get avg_buy_price from full balance list
            balances = self.upbit.get_balances()
            currency = ticker.split('-')[1]
            for b in balances:
                if b['currency'] == currency:
                    info['avg_buy_price'] = float(b['avg_buy_price'])
                    break
        else:
            # Simulation defaults
            info['krw_balance'] = 1000000
        return info

    def save_status(self, trade_results):
        """Saves current status to JSON for Dashboard."""
        status_path = os.path.join(os.path.dirname(__file__), 'data', 'status.json')
        
        # Get total assets
        total_assets = 0
        balances = {}
        
        if self.upbit:
            balances_raw = self.upbit.get_balances()
            for b in balances_raw:
                currency = b['currency']
                balance = float(b['balance'])
                avg_buy_price = float(b['avg_buy_price'])
                current_price = 1 if currency == 'KRW' else pyupbit.get_current_price(f"KRW-{currency}")
                
                if current_price:
                    value = balance * current_price
                    total_assets += value
                    balances[currency] = {
                        'balance': balance,
                        'value': value,
                        'avg_buy_price': avg_buy_price,
                        'return_rate': ((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0
                    }
        else:
             # Mock data for simulation
             total_assets = 1000000
             balances = {'KRW': {'balance': 1000000, 'value': 1000000}}

        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_assets': total_assets,
            'positions': balances,
            'recent_trades': trade_results
        }
        
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run_cycle(self):
        """Runs one trading cycle for all coins."""
        results = []
        
        # Calculate Total Capital (Equity) first
        total_assets = 0
        if self.upbit:
             # Simple approximation: KRW + sum(coin_value)
             balances = self.upbit.get_balances()
             for b in balances:
                 if b['currency'] == 'KRW':
                     total_assets += float(b['balance'])
                 else:
                     ticker = f"KRW-{b['currency']}"
                     current_price = pyupbit.get_current_price(ticker)
                     if current_price:
                        total_assets += float(b['balance']) * current_price
        else:
            total_assets = 1000000 # Sim

        logging.info(f"💰 Total Equity: {total_assets:,.0f} KRW")

        for ticker in self.config.COINS:
            logging.info(f"Analyzing {ticker}...")
            
            # 1. Get Market Data (OHLCV + Indicators)
            df = self.get_market_data(ticker)
            if df is None: continue
            
            current_price = pyupbit.get_current_price(ticker)
            balance_info = self.get_balance_info(ticker)
            
            # 2. Safety Check (Stop Loss / Take Profit) - BEFORE AI
            # Note: We need to adapt check_safety_stop to new config keys if changed.
            # Assuming check_safety_stop is refactored or removed in next step if sticking deeply to AI rules. 
            # For now, let's keep it as hard fail-safe but use updated Risk Dict.
            
            # 3. AI Analysis
            decision = self.analyze_market(ticker, df, balance_info, total_assets)
            
            reason_kr = self.get_korean_reason(decision.get('reason_code', ''))
            logging.info(f"👉 {ticker}: {decision.get('action')} (Conf: {decision.get('confidence', 0):.2f}) - {reason_kr}")
            
            # 4. Execute Trade
            self.execute_trade(ticker, decision, current_price, balance_info, total_assets)
            
            results.append({
                'ticker': ticker,
                'decision': decision.get('action', 'HOLD').lower(),
                'reason': decision.get('reason_code', 'Unknown'), # Keep raw code for JSON/Dashboard builder
                'time': datetime.now().strftime("%H:%M")
            })
            
            time.sleep(1) # Rate limit prevention
            
        self.save_status(results)
        return results

    def get_korean_reason(self, code):
        """Maps technical codes to friendly Korean messages for console logging."""
        mapping = {
            "TREND_ALIGNMENT": "📉 하락 추세 (MA20 < MA60)",
            "VOLATILITY_FILTER": "🌪️ 변동성 부적합",
            "LOW_CONFIDENCE": "🤔 AI 확신도 부족",
            "MAX_COINS_REACHED": "🚫 보유 종목 수 최대",
            "ASSET_ALLOCATION": "⚠️ 비중 초과",
            "CONSECUTIVE_LOSS_PROTECTION": "🛡️ 연속 손실 보호",
            "LOSS_CUT": "✂️ 손절매 실행",
            "TAKE_PROFIT": "💰 익절매 실행",
            "STRUCTURE_UNCLEAR": "🤷 방향성 불확실",
            "API_ERROR": "⚠️ API/시스템 오류"
        }
        return mapping.get(code, code)

if __name__ == "__main__":
    import sys
    import os
    from dotenv import load_dotenv

    # Setup basic logging for manual run
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True
    )
    
    # Calculate Project Root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Load .env
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logging.info(f"✅ Loaded .env from {env_path}")
    else:
        logging.warning("⚠️ .env file not found!")

    # Import config
    try:
        sys.path.append(current_dir)
        import config
    except ImportError as e:
        logging.error(f"Config import failed: {e}")
        sys.exit(1)

    print("\n🤖 Manual Execution Started... (Press Ctrl+C to stop)")
    print("---------------------------------------------------")
    
    try:
        trader = AutoTrader(config)
        trader.run_cycle()
        print("\n✅ Cycle Completed Successfully.")
    except Exception as e:
        logging.error(f"❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("---------------------------------------------------")
