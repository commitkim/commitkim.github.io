"""
Crypto Trading Engine
- Ported from Auto trader/trader.py
- Core trading logic, market analysis, and execution.
"""

import json
import os
import time
from datetime import datetime

import pyupbit
from google import genai

from core.config import PROJECT_ROOT, Config
from core.logger import get_logger

log = get_logger("crypto_trader.engine")
STATUS_FILE = PROJECT_ROOT / "data" / "trade" / "status.json"


# Lazy-initialized Gemini client (shared across instances)
_gemini_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


class CryptoEngine:
    def __init__(self):
        self.cfg = Config.instance()

        # Load credentials
        self.access_key = os.getenv("UPBIT_ACCESS_KEY")
        self.secret_key = os.getenv("UPBIT_SECRET_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Initialize Upbit API
        if self.access_key and self.secret_key:
            self.upbit = pyupbit.Upbit(self.access_key, self.secret_key)
        else:
            log.warning("⚠️ Warning: Upbit API keys not found. Running in simulation mode.")
            self.upbit = None

        # Gemini availability flag (client is lazy-initialized)
        if not self.gemini_api_key:
            log.error("GEMINI_API_KEY is missing!")
            self.model = None
        else:
            self.model = self.cfg.get("ai.model", "gemini-2.5-flash")  # model name string

        # Config shortcuts
        self.coins = self.cfg.get("crypto_trader.coins", [])
        self.interval = self.cfg.get("crypto_trader.interval_minutes", 60)
        self.interval_str = "minute60" # Hardcoded in legacy, map from interval if needed

        # Capital Config
        self.max_coins_held = self.cfg.get("crypto_trader.capital.max_coins_held", 3)
        self.investment_per_trade_pct = self.cfg.get("crypto_trader.capital.investment_per_trade", 0.3)
        self.max_allocation_per_coin_pct = self.cfg.get("crypto_trader.capital.max_allocation_per_coin", 1.0)

        # Risk Config
        self.risk_per_trade = self.cfg.get("crypto_trader.risk.risk_per_trade", 0.01)
        self.stop_loss_default = self.cfg.get("crypto_trader.risk.stop_loss_default", -0.02)
        self.take_profit_min = self.cfg.get("crypto_trader.risk.take_profit_min", 0.03)

    def get_market_data(self, ticker):
        """Fetches OHLCV and technical indicators."""
        try:
            # Fetching 240 (10 days) to ensure enough buffer for MA60
            df = pyupbit.get_ohlcv(ticker, interval=self.interval_str, count=240)
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
            log.error(f"Error fetching market data for {ticker}: {e}")
            return None

    def analyze_market(self, ticker, df, balance_info, total_assets):
        """Analyzes market data using AI and returns a trading decision."""
        if not self.model:
            return {"action": "HOLD", "reason_code": "API_ERROR", "confidence": 0}

        try:
            # 1. Prepare Data
            row = df.iloc[-1]
            current_price = row['close']
            ma20 = row['ma20']
            ma60 = row['ma60']
            rsi = row['rsi']
            bb_upper = row['bb_upper']
            bb_lower = row['bb_lower']
            current_equity = total_assets

            # 2. Formulate Prompt
            ohlcv_json = df.tail(24).to_json(orient='records')

            prompt = f"""
            You are an autonomous crypto trading decision engine operating a very small account (approx 50,000 KRW).
            Your PRIMARY objective is long-term capital survival. Profit is secondary.
            If uncertain, DO NOT trade.

            ### MARKET DATA ({ticker})
            Current Price: {current_price}
            MA20: {ma20:.2f}, MA60: {ma60:.2f}
            BB Upper: {bb_upper:.2f}, BB Lower: {bb_lower:.2f}
            RSI (14): {rsi:.2f}

            ### ACCOUNT STATUS
            Total Equity: {current_equity:.0f} KRW
            Current Position: {balance_info}

            ### TRADING RULES
            1. Capital Preservation: if Total Equity < 50,000 KRW, be extremely conservative.
            2. RSI Filter: Buy only if RSI < 35 (Oversold). Sell if RSI > 70.
            3. Risk Management:
               - Position Size: Max 20% of equity per trade.
               - Stop Loss: -2% from entry.
               - Take Profit: +4% from entry.
            4. Volatility Filter: Avoid extreme panic or zero movement.
            5. Trend Alignment: Do NOT Buy against downtrend (MA20 < MA60).

            ### OUTPUT FORMAT (STRICT JSON ONLY)
            {{
              "action": "BUY" | "SELL" | "HOLD",
              "position_size_percent": number (1-30),
              "limit_price": number (optional),
              "stop_loss_price": number,
              "take_profit_price": number (Min 1.5x Risk),
              "confidence": 0.0~1.0,
              "reason_code": "TREND_ALIGNMENT | VOLATILITY_FILTER | RISK_MANAGEMENT | LOW_CONFIDENCE | ..."
            }}

            Analyze the following OHLCV data and provide your decision:
            {ohlcv_json}
            """

            # 3. Call AI
            client = _get_gemini_client()
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            decision = json.loads(text)

            # 4. Validate Decision (Client-side safety)
            # (Validation logic is handled in the caller or implicitly safe defaults)

            return decision

        except Exception as e:
            log.error(f"Error in analysis: {e}")
            return {"action": "HOLD", "reason_code": "API_ERROR", "confidence": 0}

    def execute_trade(self, ticker, decision, current_price, balance_info, total_capital):
        """Executes trade based on strategy."""
        action = decision.get('action', 'HOLD')
        confidence = decision.get('confidence', 0)

        # 1. Global Filter: Low Confidence
        if confidence < 0.65 and action != 'SELL':
             log.info(f"✋ Low Confidence ({confidence:.2f}) -> HOLD {ticker}")
             return

        if self.upbit is None:
            log.info(f"[Simulation] {action} {ticker} (Conf: {confidence}) Reason: {decision.get('reason_code')}")
            return

        try:
            if action == 'BUY':
                # Check Max Coins Held
                if self.get_held_coin_count() >= self.max_coins_held:
                    if balance_info['coin_balance'] * current_price < 5000: # New entry
                        log.warning(f"🚫 Max coins held ({self.max_coins_held}) reached. HOLD {ticker}")
                        return

                # Calculate Position Size via AI's suggestion or Hard Cap
                suggested_size_pct = min(
                    decision.get('position_size_percent', 0),
                    self.investment_per_trade_pct * 100
                )
                amount_to_invest = total_capital * (suggested_size_pct / 100)

                # Dynamic Sizing for Small Accounts
                min_order_val = 5500
                if amount_to_invest < min_order_val:
                    if total_capital >= min_order_val:
                        log.info(f"💡 Adjusting bet size to minimum: {min_order_val} KRW")
                        amount_to_invest = min_order_val
                    else:
                        log.warning(f"⚠️ Insufficient capital ({total_capital} < {min_order_val}). Skip.")
                        return

                # Double check with KRW balance
                if amount_to_invest > balance_info['krw_balance']:
                     amount_to_invest = balance_info['krw_balance']

                # 3. Allocation Limit Check
                current_holding_value = balance_info['coin_balance'] * current_price
                max_allocation = total_capital * self.max_allocation_per_coin_pct

                # If current holding already exceeds max allocation
                if current_holding_value >= max_allocation:
                    log.warning(f"🚫 Max allocation limit reached for {ticker}. Skip BUY.")
                    return

                # Cap investment amount to remaining allocation
                remaining_allocation = max_allocation - current_holding_value
                if amount_to_invest > remaining_allocation:
                    log.info(f"⚖️ Capping investment to remaining allocation: {remaining_allocation:,.0f} KRW")
                    amount_to_invest = remaining_allocation

                # If balance is too low after adjustment
                if amount_to_invest < 5000:
                    log.warning("⚠️ Insufficient KRW balance or Allocation for minimum order. Skip.")
                    return

                reason_kr = self.get_korean_reason(decision.get('reason_code'))
                log.info(f"🚀 BUY {ticker} | Size: {amount_to_invest:,.0f} KRW | Reason: {reason_kr}")
                self.upbit.buy_market_order(ticker, amount_to_invest)

            elif action == 'SELL':
                if balance_info['coin_balance'] * current_price > 5000:
                    reason_kr = self.get_korean_reason(decision.get('reason_code'))
                    log.info(f"📉 SELL {ticker} | Reason: {reason_kr}")
                    self.upbit.sell_market_order(ticker, balance_info['coin_balance'])

        except Exception as e:
            log.error(f"Trade Execution Error: {e}")

    def get_held_coin_count(self):
        """Returns number of coins currently held (value > 5000 KRW)."""
        if not self.upbit:
            return 0
        try:
            balances = self.upbit.get_balances()
            count = 0
            for b in balances:
                if b['currency'] == 'KRW':
                    continue

                current_price = pyupbit.get_current_price(f"KRW-{b['currency']}")
                if current_price and (float(b['balance']) * current_price) > 5000:
                    count += 1
            return count
        except Exception:
            return 0

    def get_balance_info(self, ticker):
        """Helper to get balance info for a specific ticker."""
        info = {'krw_balance': 0, 'coin_balance': 0, 'avg_buy_price': 0}
        if self.upbit:
            info['krw_balance'] = self.upbit.get_balance("KRW")
            info['coin_balance'] = self.upbit.get_balance(ticker)
            # Need to get avg_buy_price from full balance list
            try:
                balances = self.upbit.get_balances()
                if isinstance(balances, list):
                    currency = ticker.split('-')[1]
                    for b in balances:
                        if isinstance(b, dict) and b['currency'] == currency:
                            info['avg_buy_price'] = float(b['avg_buy_price'])
                            break
            except Exception as e:
                log.warning(f"Error getting balance info: {e}")
        else:
            # Simulation defaults
            info['krw_balance'] = 1000000
        return info

    def save_status(self, trade_results):
        """Saves current status to JSON, maintaining a history of trades."""
        # Load existing data to preserve history
        existing_data = {}
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                log.error(f"Failed to load existing status from {STATUS_FILE}: {e}")

        # Get total assets
        total_assets = 0
        balances = {}

        if self.upbit:
            try:
                balances_raw = self.upbit.get_balances()
                if isinstance(balances_raw, list):
                    for b in balances_raw:
                        if not isinstance(b, dict):
                            continue
                        currency = b['currency']
                        balance = float(b['balance'])
                        avg_buy_price = float(b['avg_buy_price'])
                        current_price = 1 if currency == 'KRW' else pyupbit.get_current_price(f"KRW-{currency}")

                        if current_price:
                            value = balance * current_price
                            total_assets += value

                            return_rate = 0
                            if avg_buy_price > 0:
                                return_rate = (current_price - avg_buy_price) / avg_buy_price * 100

                            balances[currency] = {
                                'balance': balance,
                                'value': value,
                                'avg_buy_price': avg_buy_price,
                                'return_rate': return_rate
                            }
            except Exception as e:
                log.warning(f"Error calculating assets: {e}")
        else:
             # Mock data for simulation
             total_assets = 1000000
             balances = {'KRW': {'balance': 1000000, 'value': 1000000}}

        # Update Trade History
        recent_trades = existing_data.get('recent_trades', [])
        recent_trades.extend(trade_results)
        recent_trades = recent_trades[-1000:]

        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_assets': total_assets,
            'positions': balances,
            'recent_trades': recent_trades
        }

        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_korean_reason(self, code, conf=0):
        """Maps technical codes to friendly Korean messages."""
        conf = float(conf)
        mapping = {
            "TREND_ALIGNMENT": ("[TREND] 현재 가격이 장기 이동평균선(60일선) 아래에 있어 "
                                "하락세가 강합니다. 안전을 위해 매수를 보류했습니다."),
            "VOLATILITY_FILTER": ("[VOL] 시장의 변동성이 너무 적거나 반대로 너무 극심합니다. "
                                  "예측이 어려워 진입하지 않았습니다."),
            "LOW_CONFIDENCE": (f"[LOW] 상승 확신도가 기준치(0.65)보다 낮은 {conf:.2f}입니다. "
                               "더 확실한 기회를 기다립니다."),
            "MAX_COINS_REACHED": ("[LIMIT] 이미 최대 보유 종목 수(3개)를 채웠습니다. "
                                  "새로운 종목을 매수하려면 기존 종목이 매도되어야 합니다."),
            "ASSET_ALLOCATION": ("[LIMIT] 한 종목에 담을 수 있는 최대 비중을 초과하게 됩니다. "
                                 "리스크 관리를 위해 추가 매수를 제한합니다."),
            "CONSECUTIVE_LOSS_PROTECTION": ("[COOL] 최근 연속으로 손실이 발생하여 '쿨다운' 중입니다. "
                                            "잠시 머리를 식히며 시장을 관망합니다."),
            "LOSS_CUT": ("[LOSS] 아쉽지만 손절매 라인(-3%)을 건드렸습니다. "
                         "더 큰 손실을 막기 위해 원칙대로 매도하여 자본을 지킵니다."),
            "TAKE_PROFIT": ("[PROFIT] 목표 수익률(+5%)에 도달했습니다! "
                            "욕심부리지 않고 수익을 확정 지어 주머니에 넣습니다."),
            "STRUCTURE_UNCLEAR": ("[UNCLEAR] 차트의 흐름이 위인지 아래인지 명확하지 않습니다. "
                                  "방향이 결정될 때까지 지켜보는 게 좋겠습니다."),
            "API_ERROR": "[ERR] 일시적인 시스템/통신 오류가 발생했습니다. 안전을 위해 이번 턴은 건너뜁니다.",
            "CAPITAL_PRESERVATION": ("[SAVE] 지금은 돈을 버는 것보다 지키는 것이 더 중요한 시기입니다. "
                                     "무리하지 않고 현금을 보유합니다."),
            "UNCLEAR_TREND": ("[UNCLEAR] 상승장인지 하락장인지 뚜렷하지 않습니다. "
                              "애매할 땐 쉬어가는 것이 상책입니다."),
            "LOW_CONFIDENCE_AND_UNCLEAR_TREND": ("[WEAK] 확신도 부족하고 추세도 애매합니다. "
                                                 "이럴 때 매수하면 물리기 쉽습니다."),
            "BEARISH_MOMENTUM_INDICATORS": ("[BEAR] 보조지표(MACD, RSI)가 하락을 가리키고 있습니다. "
                                            "매수하기엔 힘이 빠져 보입니다."),
            "PRICE_BELOW_MAS": ("[DOWN] 가격이 주요 이동평균선 아래로 처져 있습니다. "
                                "상승 추세로 돌아설 때까지 기다립니다.")
        }
        return mapping.get(code, code)

    def run_cycle(self):
        """Runs one trading cycle."""
        if not self.coins:
            log.warning("No coins configured for trading.")
            return

        # 1. Analyze ALL Coins
        analysis_results = []
        total_assets = 0

        # Calculate Total Capital
        if self.upbit:
             try:
                 balances = self.upbit.get_balances()
                 if not isinstance(balances, list) or (balances and not isinstance(balances[0], dict)):
                     log.error("⚠️ Upbit API returned unexpected response. Falling back to simulation.")
                     self.upbit = None
                     total_assets = 0
                 else:
                     for b in balances:
                         if b['currency'] == 'KRW':
                             total_assets += float(b['balance'])
                         else:
                             ticker = f"KRW-{b['currency']}"
                             current_price = pyupbit.get_current_price(ticker)
                             if current_price:
                                total_assets += float(b['balance']) * current_price
             except Exception as e:
                 log.error(f"Error checking balances: {e}")
                 self.upbit = None
                 total_assets = 0

        if not self.upbit:
            total_assets = 1000000 # Sim

        log.info(f"💰 Total Equity: {total_assets:,.0f} KRW")

        for ticker in self.coins:
            # Get Market Data
            df = self.get_market_data(ticker)
            if df is None:
                continue

            current_price = pyupbit.get_current_price(ticker)
            balance_info = self.get_balance_info(ticker)

            # AI Analysis
            decision = self.analyze_market(ticker, df, balance_info, total_assets)

            reason_kr = self.get_korean_reason(decision.get('reason_code', ''), decision.get('confidence', 0))
            log.info(f"👉 {ticker}: {decision.get('action')} (Conf: {decision.get('confidence', 0):.2f}) - {reason_kr}")

            analysis_results.append({
                'ticker': ticker,
                'decision': decision,
                'current_price': current_price,
                'balance_info': balance_info,
                'total_assets': total_assets
            })

            time.sleep(1) # Rate limit

        # 2. EXECUTE SELLS
        sells = [item for item in analysis_results if item['decision'].get('action') == 'SELL']
        for item in sells:
            log.info(f"📉 Executing SELL for {item['ticker']} first to clear slot...")
            self.execute_trade(
                item['ticker'], item['decision'], item['current_price'],
                item['balance_info'], item['total_assets']
            )

        # 3. EXECUTE BUYS
        buys = [item for item in analysis_results if item['decision'].get('action') == 'BUY']
        buys.sort(key=lambda x: x['decision'].get('confidence', 0), reverse=True)

        current_slots = self.get_held_coin_count()

        for item in buys:
            if current_slots < self.max_coins_held:
                log.info(f"🚀 Executing Ranked BUY for {item['ticker']} "
                         f"(Rank #{buys.index(item)+1}, Conf: {item['decision'].get('confidence'):.2f})")
                self.execute_trade(
                    item['ticker'], item['decision'], item['current_price'],
                    item['balance_info'], item['total_assets']
                )
                current_slots += 1
            else:
                log.warning(f"🚫 Slot Full ({current_slots}/{self.max_coins_held}). "
                            f"Skipping BUY for {item['ticker']}")
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
