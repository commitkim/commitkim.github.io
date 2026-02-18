# Auto Trader Configuration

# Target Cryptocurrencies
COINS = [
    "KRW-BTC",
    "KRW-ETH",
    "KRW-XRP",
    "KRW-SOL",
    "KRW-AVAX",
    "KRW-DOGE"
]

# Trading Settings
TRADING = {
    "interval_minutes": 60,       # 1시간 봉 기준
    "execution_cron": "0 * * * *", # 매시 정각 실행 (Linux Cron syntax - Reference only for now)
    "interval": "minute60"         # Upbit Chart Interval
}

# Capital Management (Strict Survival Rules)
CAPITAL = {
    "investment_per_trade": 0.1,    # Max 10% per trade (Dynamic sizing will be used, but this is hard cap)
    "max_exposure_total": 0.3,      # Max 30% total capital deployed
    "max_coins_held": 3,            # Max 3 coins
    "consecutive_loss_limit": 3     # Stop trading after 3 consecutive losses
}

# Risk Management
RISK = {
    "risk_per_trade": 0.01,         # Max 1% risk of total equity per trade
    "stop_loss_default": -0.02,     # Fallback stop loss if AI doesn't specify
    "take_profit_min": 0.03         # Minimum TP target
}

# Gemini Model Settings
GEMINI = {
    "model_name": "gemini-2.0-flash"
}
