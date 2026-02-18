import pyupbit
import google.generativeai as genai
import json
import os
import sys
import time
import logging
from datetime import datetime

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
            # Fetch more data to calculate indicators (MA60 needs 60, we want 7 days history i.e. 168h)
            # Fetching 240 (10 days) to ensure enough buffer for MA60 at the start of our 7-day window
            df = pyupbit.get_ohlcv(ticker, interval=self.config.TRADING['interval'], count=240)
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
        ohlcv_json = df.tail(168).to_json() # Last 7 days (168 hours)
        
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
        3. Risk Per Trade: Max risk {self.config.RISK['risk_per_trade'] * 100:.2f}% of total equity.
        4. Volatility Filter: Avoid extreme panic or zero movement.
        5. Trend Alignment: Do NOT Buy against downtrend (MA20 < MA60).
        
        ### OUTPUT FORMAT (STRICT JSON ONLY)
        {{
          "action": "BUY" | "SELL" | "HOLD",
          "position_size_percent": 0~{self.config.CAPITAL['investment_per_trade'] * 100} (Max {self.config.CAPITAL['investment_per_trade'] * 100}%),
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
                suggested_size_pct = min(decision.get('position_size_percent', 0), self.config.CAPITAL['investment_per_trade'] * 100)
                amount_to_invest = total_capital * (suggested_size_pct / 100)
                
                # Dynamic Sizing for Small Accounts (Ensure min 5500 KRW)
                min_order_val = 5500
                if amount_to_invest < min_order_val:
                    if total_capital >= min_order_val:
                        logging.info(f"💡 Adjusting bet size to minimum: {min_order_val} KRW")
                        amount_to_invest = min_order_val
                    else:
                        logging.warning(f"⚠️ Insufficient capital ({total_capital} < {min_order_val}). Skip.")
                        return

                # Double check with KRW balance
                if amount_to_invest > balance_info['krw_balance']:
                     amount_to_invest = balance_info['krw_balance']

                # 3. Allocation Limit Check (New Feature)
                current_holding_value = balance_info['coin_balance'] * current_price
                max_allocation = total_capital * self.config.CAPITAL.get('max_allocation_per_coin', 1.0) # Default to 100% if not set
                
                # If current holding already exceeds max allocation
                if current_holding_value >= max_allocation:
                    logging.warning(f"🚫 Max allocation ({self.config.CAPITAL.get('max_allocation_per_coin')}%) reached for {ticker}. Skip BUY.")
                    return

                # Cap investment amount to remaining allocation
                remaining_allocation = max_allocation - current_holding_value
                if amount_to_invest > remaining_allocation:
                    logging.info(f"⚖️ Capping investment to remaining allocation: {remaining_allocation:,.0f} KRW")
                    amount_to_invest = remaining_allocation

                # If balance is too low after adjustment
                if amount_to_invest < 5000:
                    logging.warning("⚠️ Insufficient KRW balance or Allocation for minimum order. Skip.")
                    return

                reason_kr = self.get_korean_reason(decision.get('reason_code'))
                logging.info(f"🚀 BUY {ticker} | Size: {amount_to_invest:,.0f} KRW | Reason: {reason_kr}")
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
        """Saves current status to JSON for Dashboard, maintaining a history of trades."""
        status_path = os.path.join(os.path.dirname(__file__), 'data', 'status.json')
        
        # Load existing data to preserve history
        existing_data = {}
        if os.path.exists(status_path):
            try:
                with open(status_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                # logging.info(f"✅ Loaded {len(existing_data.get('recent_trades', []))} existing trades from {status_path}")
            except Exception as e:
                logging.error(f"Failed to load existing status from {status_path}: {e}")
        else:
             logging.warning(f"⚠️ Status file not found at {status_path}. Starting fresh.")

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

        # Update Trade History (Append new results to existing ones)
        recent_trades = existing_data.get('recent_trades', [])
        
        # Add new trades
        recent_trades.extend(trade_results)
        
        # Keep only the last 50 trades (or 100, user asked for history)
        # Let's keep 100 to be safe
        recent_trades = recent_trades[-100:]

        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_assets': total_assets,
            'positions': balances,
            'recent_trades': recent_trades
        }
        
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run_cycle(self):
        """Runs one trading cycle with Ranked Execution (Analyze -> Sell -> Buy)."""
        
        # 1. Analyze ALL Coins
        analysis_results = []
        total_assets = 0
        
        # Calculate Total Capital (Equity) first
        if self.upbit:
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
            # logging.info(f"Analyzing {ticker}...")
            
            # Get Market Data
            df = self.get_market_data(ticker)
            if df is None: continue
            
            current_price = pyupbit.get_current_price(ticker)
            balance_info = self.get_balance_info(ticker)
            
            # AI Analysis
            decision = self.analyze_market(ticker, df, balance_info, total_assets)
            
            reason_kr = self.get_korean_reason(decision.get('reason_code', ''))
            logging.info(f"👉 {ticker}: {decision.get('action')} (Conf: {decision.get('confidence', 0):.2f}) - {reason_kr}")
            
            analysis_results.append({
                'ticker': ticker,
                'decision': decision,
                'current_price': current_price,
                'balance_info': balance_info,
                'total_assets': total_assets
            })
            
            time.sleep(1) # Rate limit

        # 2. EXECUTE SELLS (Prioritize clearing slots)
        # Filter for SELL actions
        sells = [item for item in analysis_results if item['decision'].get('action') == 'SELL']
        
        for item in sells:
            logging.info(f"📉 Executing SELL for {item['ticker']} first to clear slot...")
            self.execute_trade(item['ticker'], item['decision'], item['current_price'], item['balance_info'], item['total_assets'])

        # 3. EXECUTE BUYS (Ranked by Confidence)
        # Filter for BUY actions
        buys = [item for item in analysis_results if item['decision'].get('action') == 'BUY']
        
        # Sort by Confidence (Descending)
        buys.sort(key=lambda x: x['decision'].get('confidence', 0), reverse=True)
        
        # Check current slots after sells
        current_slots = self.get_held_coin_count()
        max_slots = self.config.CAPITAL['max_coins_held']
        
        for item in buys:
            if current_slots < max_slots:
                logging.info(f"🚀 Executing Ranked BUY for {item['ticker']} (Rank #{buys.index(item)+1}, Conf: {item['decision'].get('confidence'):.2f})")
                self.execute_trade(item['ticker'], item['decision'], item['current_price'], item['balance_info'], item['total_assets'])
                current_slots += 1 # Increment local slot count
            else:
                logging.warning(f"🚫 Slot Full ({current_slots}/{max_slots}). Skipping BUY for {item['ticker']} (Conf: {item['decision'].get('confidence'):.2f})")
                item['decision']['action'] = 'HOLD' # Change to HOLD for logging
                item['decision']['reason_code'] = 'MAX_COINS_REACHED'

        # 4. Save Results
        final_results = []
        for item in analysis_results:
            final_results.append({
                'ticker': item['ticker'],
                'decision': item['decision'].get('action', 'HOLD').lower(),
                'reason': item['decision'].get('reason_code', 'Unknown'),
                'time': datetime.now().strftime("%m/%d %H:%M"),
                'confidence': item['decision'].get('confidence', 0.0)
            })
            
        self.save_status(final_results)
        return final_results

    def get_korean_reason(self, code):
        """Maps technical codes to friendly Korean messages for console logging."""
        mapping = {
            "TREND_ALIGNMENT": "📉 현재 가격이 장기 이동평균선(60일선) 아래에 있어 하락세가 강합니다. 안전을 위해 매수를 보류했습니다.",
            "VOLATILITY_FILTER": "🌪️ 시장의 변동성이 너무 적거나 반대로 너무 극심합니다. 예측이 어려워 진입하지 않았습니다.",
            "LOW_CONFIDENCE": "🤔 AI의 분석 결과, 상승 확신도가 기준치(0.65)보다 낮습니다. 더 확실한 기회를 기다립니다.",
            "MAX_COINS_REACHED": "🚫 이미 최대 보유 종목 수(3개)를 채웠습니다. 새로운 종목을 매수하려면 기존 종목이 매도되어야 합니다.",
            "ASSET_ALLOCATION": "⚠️ 한 종목에 담을 수 있는 최대 비중을 초과하게 됩니다. 리스크 관리를 위해 추가 매수를 제한합니다.",
            "CONSECUTIVE_LOSS_PROTECTION": "🛡️ 최근 연속으로 손실이 발생하여 '쿨다운' 중입니다. 잠시 머리를 식히며 시장을 관망합니다.",
            "LOSS_CUT": "✂️ 아쉽지만 손절매 라인(-3%)을 건드렸습니다. 더 큰 손실을 막기 위해 원칙대로 매도하여 자본을 지킵니다.",
            "TAKE_PROFIT": "💰 목표 수익률(+5%)에 도달했습니다! 욕심부리지 않고 수익을 확정 지어 주머니에 넣습니다.",
            "STRUCTURE_UNCLEAR": "🤷 차트의 흐름이 위인지 아래인지 명확하지 않습니다. 방향이 결정될 때까지 지켜보는 게 좋겠습니다.",
            "API_ERROR": "⚠️ 일시적인 시스템/통신 오류가 발생했습니다. 안전을 위해 이번 턴은 건너뜁니다.",
            "CAPITAL_PRESERVATION": "💰 지금은 돈을 버는 것보다 지키는 것이 더 중요한 시기입니다. 무리하지 않고 현금을 보유합니다.",
            "UNCLEAR_TREND": "❓ 상승장인지 하락장인지 뚜렷하지 않습니다. 애매할 땐 쉬어가는 것이 상책입니다.",
            "LOW_CONFIDENCE_AND_UNCLEAR_TREND": "🤔 확신도 부족하고 추세도 애매합니다. 이럴 때 매수하면 물리기 쉽습니다.",
            "BEARISH_MOMENTUM_INDICATORS": "📉 보조지표(MACD, RSI)가 하락을 가리키고 있습니다. 매수하기엔 힘이 빠져 보입니다.",
            "PRICE_BELOW_MAS": "📉 가격이 주요 이동평균선 아래로 처져 있습니다. 상승 추세로 돌아설 때까지 기다립니다."
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
