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
        self.interval = self.cfg.get("crypto_trader.interval_minutes", 15)
        self.interval_str = f"minute{self.interval}"  # Dynamically use interval from config

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
            You are an autonomous crypto trading decision engine operating an account.
            Your PRIMARY objective is aggressive capital growth and profit maximization.
            Take calculated risks when momentum is favorable.

            ### MARKET DATA ({ticker})
            Current Price: {current_price}
            MA20: {ma20:.2f}, MA60: {ma60:.2f}
            BB Upper: {bb_upper:.2f}, BB Lower: {bb_lower:.2f}
            RSI (14): {rsi:.2f}

            ### ACCOUNT STATUS
            Total Equity: {current_equity:.0f} KRW
            Current Position: {balance_info}

            ### TRADING RULES
            1. Profit Maximization: Aggressively seek entry points during uptrends or strong momentum.
            2. RSI Filter: Buy when RSI suggests strong momentum (e.g., RSI > 40) or opportunistic dips. Avoid buying at extreme overbought levels (RSI > 85) unless momentum is exceptional.
            3. Risk Management & Trailing Stop:
               - Position Size: Max {self.investment_per_trade_pct * 100}% of equity per trade. The absolute minimum trade amount MUST be >= 5000 KRW.
               - Stop Loss: {self.stop_loss_default * 100}% from entry.
               - Trailing Stop (Take Profit): If position is in profit >= {self.take_profit_min * 100}%, DO NOT SELL immediately. Let the profit run! Only SELL if the price drops by 2% from the local peak, or if a clear bearish reversal occurs.
            4. Trend Alignment: Favor buying when momentum is strong. You can buy even if MA20 < MA60 if there is a clear reversal or breakout signal.

            ### OUTPUT FORMAT (STRICT JSON ONLY)
            {{
              "action": "BUY" | "SELL" | "HOLD",
              "position_size_percent": number (1-{int(self.investment_per_trade_pct * 100)}),
              "limit_price": number (optional),
              "stop_loss_price": number,
              "take_profit_price": number,
              "confidence": 0.0~1.0,
              "reason_code": "STRONG_MOMENTUM | BREAKOUT | DIP_BUY | RISK_MANAGEMENT | TRAILING_STOP_TRIGGERED | LET_PROFIT_RUN | LOW_CONFIDENCE | ..."
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

        # 1. Global Filter: Low Confidence (Lowered for aggressive strategy)
        if confidence < 0.55 and action != 'SELL':
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
            "TREND_ALIGNMENT": ("[TREND] 하락세가 강하지만, 모멘텀을 지켜보며 기회를 엿보고 있습니다."),
            "VOLATILITY_FILTER": ("[VOL] 시장의 변동성을 주시하며 적극적인 진입 타이밍을 계산 중입니다."),
            "LOW_CONFIDENCE": (f"[LOW] 확신도({conf:.2f})가 아직 진입 기준(0.55)에 못 미칩니다. 조금 더 강한 시그널을 기다립니다."),
            "MAX_COINS_REACHED": ("[LIMIT] 이미 공격적으로 투자하여 최대 보유 종목 수에 도달했습니다. "
                                  "수익 실현 후 새로운 기회를 노리겠습니다."),
            "ASSET_ALLOCATION": ("[LIMIT] 한 종목에 집중 투자할 수 있는 공격적 한계치에 도달했습니다. "
                                 "리스크 분산을 위해 추가 진입을 보류합니다."),
            "CONSECUTIVE_LOSS_PROTECTION": ("[COOL] 잦은 타격으로 잠시 전열을 가다듬고 있습니다. "
                                            "곧 다시 공격적인 매매를 재개할 예정입니다."),
            "LOSS_CUT": ("[LOSS] 공격적인 손절매 처리! "
                         "더 좋은 기회로 빠르게 갈아타기 위해 손실을 짧게 끊어냈습니다."),
            "TAKE_PROFIT": ("[PROFIT] 과감한 익절 적중! "
                            "빠르게 수익을 챙기고 다음 사냥감을 찾습니다."),
            "STRUCTURE_UNCLEAR": ("[UNCLEAR] 변동성이 애매합니다. "
                                  "큰 파도가 오기 전까지는 체력을 비축합니다."),
            "API_ERROR": "[ERR] 시스템 오류가 발생하여 작전을 일시 중지합니다.",
            "CAPITAL_PRESERVATION": ("[SAVE] 현재는 베팅하기 좋은 장세가 아닙니다. "
                                     "다음 기회를 위해 화력을 보존합니다."),
            "UNCLEAR_TREND": ("[UNCLEAR] 흐름이 불분명하여 무리한 진입을 자제합니다."),
            "LOW_CONFIDENCE_AND_UNCLEAR_TREND": ("[WEAK] 확신도와 추세 모두 돌파력이 부족합니다. "
                                                 "승률이 높은 곳에만 타격합니다."),
            "BEARISH_MOMENTUM_INDICATORS": ("[BEAR] 보조지표가 꺾였습니다. "
                                            "물러서야 할 때를 아는 것도 실력입니다."),
            "PRICE_BELOW_MAS": ("[DOWN] 저항선 아래에 갇혀 있습니다. "
                                "돌파하는 순간을 노리겠습니다."),
            "STRONG_MOMENTUM": ("[HOT] 강력한 상승 모멘텀 포착! 공격적으로 진입합니다."),
            "BREAKOUT": ("[BREAK] 주요 저항선 돌파 시그널! 과감하게 승부를 겁니다."),
            "DIP_BUY": ("[DIP] 단기 과대 낙폭 포착. 상승 반전을 노려 공격적으로 매수합니다."),
            "REVERSAL_SIGNAL": ("[REV] 추세 반전 시그널 포착! 공격적으로 올라탑니다."),
            "POTENTIAL_REVERSAL": ("[REV] 반전 가능성이 높은 구간입니다. 선취매에 들어갑니다."),
            "REVERSAL_DIVERGENCE": ("[REV] 다이버전스 포착! 하락 추세가 끝나고 상승으로 반전할 것으로 예측합니다."),
            "REVERSAL_CANDIDATE": ("[REV] 반전 유력 후보군. 분할 매수로 접근합니다."),
            "FAVORABLE_MOMENTUM": ("[MOMENTUM] 유리한 모멘텀 형성. 상승 파도에 편승합니다."),
            "RSI_FILTER": ("[RSI] RSI 수치가 진입 조건에 맞지 않습니다."),
            "RSI_FILTER_NOT_MET": ("[RSI] RSI 조건 미달로 진입을 보류합니다."),
            "RSI_FILTER_CONDITION_NOT_MET": ("[RSI] RSI 상세 조건이 충족되지 않았습니다."),
            "RSI_FILTER_NO_BUY_SIGNAL": ("[RSI] RSI 상 뚜렷한 매수 시그널이 나오지 않았습니다."),
            "RSI_FILTER_OVERBOUGHT": ("[RSI] 과매수 구간(RSI Overbought)입니다. 추격 매수는 자제합니다."),
            "RSI_OVERBOUGHT": ("[RSI] RSI가 너무 높습니다. 단기 고점일 수 있어 진입하지 않습니다."),
            "RSI_FILTER_NO_ENTRY": ("[RSI] 종합적인 RSI 필터 결과, 진입하기에 부적절한 타점입니다."),
            "TRAILING_STOP_TRIGGERED": ("[TRAILING] 최고점 대비 2% 하락 발생! 트레일링 스탑을 작동시켜 수익을 굳힙니다."),
            "LET_PROFIT_RUN": ("[RUN] 아직 상승 추세가 꺾이지 않았습니다. 수익을 끝까지 끌고 가기 위해 매도하지 않습니다."),
            "OPPORTUNITY_SWAP": ("[SWAP] 기회비용 극대화! 부진한 종목을 매도하고 훨씬 더 강력한 상승 모델로 강제 스위칭합니다.")
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
            # Check KRW balance BEFORE trying to buy
            # Upbit updates balance instantly after self.execute_trade, but here we estimate
            # Or we can just try to execute and let execute_trade handle Insufficient KRW.
            # But for SWAPPING, we need to know if we are out of cash.
            current_krw = self.get_balance_info(item['ticker'])['krw_balance'] if self.upbit else 1000000

            if current_slots < self.max_coins_held and current_krw >= 5000:
                log.info(f"🚀 Executing Ranked BUY for {item['ticker']} "
                         f"(Rank #{buys.index(item)+1}, Conf: {item['decision'].get('confidence'):.2f})")
                self.execute_trade(
                    item['ticker'], item['decision'], item['current_price'],
                    item['balance_info'], item['total_assets']
                )
                current_slots += 1
            else:
                # OPTIONAL: Opportunity Cost Switching (Swap)
                # We are out of cash or slots. Can we swap a weak coin for this strong buy?
                buy_conf = float(item['decision'].get('confidence', 0))
                
                # Find the weakest held coin
                held_coins = [
                    res for res in analysis_results 
                    if res['balance_info']['coin_balance'] * res['current_price'] > 5000
                ]
                
                if held_coins:
                    # Sort held coins by confidence (lowest first)
                    held_coins.sort(key=lambda x: float(x['decision'].get('confidence', 0)))
                    weakest_coin = held_coins[0]
                    weak_conf = float(weakest_coin['decision'].get('confidence', 0))
                    
                    # Threshold for switching: at least 0.20 (20%p) difference to cover 0.1% fee + slippage
                    if (buy_conf - weak_conf) >= 0.20:
                        log.info(f"🔄 [SWAP INITIATED] Strong Buy ({item['ticker']}, Conf: {buy_conf:.2f}) beats "
                                 f"Weak Hold ({weakest_coin['ticker']}, Conf: {weak_conf:.2f}). Differnce: {(buy_conf - weak_conf):.2f}")
                        
                        # 1. Force Sell Weak Coin
                        weak_sell_decision = {'action': 'SELL', 'reason_code': 'OPPORTUNITY_SWAP', 'confidence': weak_conf}
                        self.execute_trade(
                            weakest_coin['ticker'], weak_sell_decision, weakest_coin['current_price'],
                            weakest_coin['balance_info'], weakest_coin['total_assets']
                        )
                        
                        # Wait a bit for Upbit balance to update
                        time.sleep(0.5)
                        
                        # 2. Re-fetch current info for the new buy to ensure updated KRW balance
                        updated_balance_info = self.get_balance_info(item['ticker'])
                        
                        # 3. Buy Strong Coin
                        item['decision']['reason_code'] = 'OPPORTUNITY_SWAP'
                        self.execute_trade(
                            item['ticker'], item['decision'], item['current_price'],
                            updated_balance_info, item['total_assets']
                        )
                        continue # Done with this item

                # If no swap happened, just HOLD
                log.warning(f"🚫 Slot Full or No Cash ({current_slots}/{self.max_coins_held}). "
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
