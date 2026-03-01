"""
Static Site Builder Core Logic
- Ported from Dashboard/builder.py
- Builds index.html, trade.html
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

from core.config import PROJECT_ROOT
from core.logger import get_logger

log = get_logger("site_builder.core")

# Paths
MODULE_DIR = PROJECT_ROOT / "modules" / "site_builder"
TEMPLATES_DIR = MODULE_DIR / "templates"
STATIC_DIR = MODULE_DIR / "static"
DOCS_DIR = PROJECT_ROOT / "docs"

# Data Paths (Unified)
DATA_DIR = PROJECT_ROOT / "data"
NEWS_DATA_DIR = DATA_DIR / "news"
NEWS_DATA_DIR = DATA_DIR / "news"
TRADE_DATA_FILE = DATA_DIR / "trade" / "status.json"
MICROGPT_DATA_FILE = DATA_DIR / "microgpt" / "trace.json"


def load_latest_news():
    """Loads the most recent news JSON from data/news/."""
    # Recursive search: data/news/**/*.json
    if not NEWS_DATA_DIR.exists():
        return None

    news_files = list(NEWS_DATA_DIR.rglob("*.json"))

    if not news_files:
        return None

    all_news = []
    for f_path in news_files:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'created_at' in data:
                    all_news.append(data)
        except Exception as e:
            log.warning(f"Error loading news {f_path}: {e}")
            continue

    if not all_news:
        return None

    # Sort by created_at descending
    all_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return all_news[0]



def load_recent_news_list(limit=7):
    """Loads recent news metadata for sidebar navigation."""
    if not NEWS_DATA_DIR.exists():
        return []

    news_items = []
    # Scan both morning and evening directories
    for mode in ['morning', 'evening']:
        mode_dir = NEWS_DATA_DIR / mode
        if not mode_dir.exists():
            continue

        for f_path in mode_dir.glob("*.json"):
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Extract minimal info needed for link
                    item = {
                        'date': f_path.stem,  # YYYYMMDD
                        'mode': mode,
                        'title': data.get('video_title', 'News Briefing'),
                        'created_at': data.get('created_at', '')
                    }
                    news_items.append(item)
            except Exception as e:
                log.warning(f"Error loading news metadata {f_path}: {e}")
                continue

    # Sort by created_at descending (or date if created_at missing)
    news_items.sort(key=lambda x: x.get('created_at', x['date']), reverse=True)
    return news_items[:limit]


def load_trade_status():
    """Loads the latest trade status from data/trade/status.json."""
    if TRADE_DATA_FILE.exists():
        try:
            with open(TRADE_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Error loading trade status: {e}")
    return None


def map_reason_code(log_entry):
    """Maps technical reason codes to user-friendly Korean explanations."""
    code = log_entry.get('reason_code', log_entry.get('reason', '')).upper()
    confidence = log_entry.get('confidence', 0)

    # Custom mapping dictionary with detailed explanations
    mapping = {
        "TREND_ALIGNMENT": ("📉 현재 가격이 장기 이동평균선(60일선) 아래에 있어 하락세가 강합니다. 안전을 위해 매수를 보류했습니다."),
        "VOLATILITY_FILTER": ("🌪️ 시장의 변동성이 너무 적거나 반대로 너무 극심합니다. 예측이 어려워 진입하지 않았습니다."),
        "LOW_CONFIDENCE": (f"🤔 AI의 분석 결과, 상승 확신도가 기준치(0.55)보다 낮은 {confidence:.2f}입니다. 조금 더 강한 시그널을 기다립니다."),
        "MAX_COINS_REACHED": ("🚫 이미 공격적으로 투자하여 최대 보유 종목 수에 도달했습니다. 수익 실현 후 새로운 기회를 노리겠습니다."),
        "ASSET_ALLOCATION": ("⚠️ 한 종목에 집중 투자할 수 있는 공격적 한계치에 도달했습니다. 리스크 관리를 위해 추가 매수를 제한합니다."),
        "CONSECUTIVE_LOSS_PROTECTION": ("🛡️ 최근 연속으로 손실이 발생하여 '쿨다운' 중입니다. 시장이 안정될 때까지 관망합니다."),
        "LOSS_CUT": ("✂️ 손절매(-5%) 라인 도달! 추가 하락을 막기 위해 칼같이 기계적 매도를 집행합니다."),
        "TAKE_PROFIT": ("💰 수익 목표(+5%) 도달! 욕심 부리지 않고 이익을 챙깁니다."),
        "STRUCTURE_UNCLEAR": ("🤷 차트 방향성이 아직 나오지 않았습니다. 섣불리 들어가지 않습니다."),
        "API_ERROR": ("⚠️ 일시적인 시스템/통신 오류가 발생했습니다. 안전을 위해 이번 턴은 건너뜁니다."),
        "CAPITAL_PRESERVATION": ("🛡️ 자본을 지키는 것이 먼저입니다. 확실한 타점이 올 때까지 웅크립니다."),
        "UNCLEAR_TREND": ("❓ 추세가 매우 모호합니다. 불확실성 리스크를 피하겠습니다."),
        "LOW_CONFIDENCE_AND_UNCLEAR_TREND": ("🤔 확신도 없고 추세도 없습니다. 진입 불가 판단."),
        "BEARISH_MOMENTUM_INDICATORS": ("📉 보조지표가 강력한 하락 시그널을 뿜고 있습니다."),
        "PRICE_BELOW_MAS": ("📉 역배열(이평선 아래) 상태입니다. 무겁게 짓눌려 상승이 힘듭니다."),
        "STRONG_MOMENTUM": ("🔥 강력한 파동이 감지되었습니다! 상승 모멘텀을 타고 공격적인 매수에 들어갑니다."),
        "BREAKOUT": ("🚀 주요 저항선을 돌파했습니다. 슈팅 구간을 노리고 과감하게 진입합니다."),
        "DIP_BUY": ("📉 의미 있는 지지 구간으로 판단됩니다. 반등을 노리고 저점 매수에 나섭니다."),
        "REVERSAL_SIGNAL": ("🔄 하락 파동이 끝나고 위로 고개를 듭니다. 추세 전환의 초입에서 선취매합니다."),
        "POTENTIAL_REVERSAL": ("🔄 추세가 도는 느낌입니다. 바닥권에서의 기회를 낚아채겠습니다."),
        "REVERSAL_DIVERGENCE": ("📈 가격은 빠지는데 RSI는 오히려 오르고 있습니다(상승 다이버전스). 반등이 머지않았습니다."),
        "REVERSAL_CANDIDATE": ("⏸️ 추세 전환의 냄새는 나지만, 아직 마지막 확신 도장이 찍히지 않았습니다."),
        "FAVORABLE_MOMENTUM": ("🐎 매수세가 붙고 있습니다. 달리는 말에 올라타 단기 수익을 극대화합니다."),
        "RSI_FILTER": ("📊 보조지표 필터에서 보수적인 신호가 나와 진입하지 않습니다."),
        "RSI_FILTER_NOT_MET": ("📊 단기 급반등 조건에 부합하지 않아 매수를 보류합니다."),
        "RSI_FILTER_CONDITION_NOT_MET": ("📊 현재 지표 상태로는 수익을 낼 만한 타점이 아닙니다."),
        "RSI_FILTER_NO_BUY_SIGNAL": ("📊 RSI 상 뚜렷한 매수 시그널이 나오지 않았습니다."),
        "RSI_FILTER_OVERBOUGHT": ("📈 과매수 구간(RSI Overbought)입니다. 추격 매수는 자제합니다."),
        "RSI_OVERBOUGHT": ("📈 RSI가 너무 높습니다. 단기 고점일 수 있어 진입하지 않습니다."),
        "RSI_FILTER_NO_ENTRY": ("📊 종합적인 RSI 필터 결과, 진입하기에 부적절한 타점입니다."),
        "AWAITING_REVERSAL_CONFIRMATION": ("⏳ 반등의 조짐은 보이나, 확실한 추세 전환 신호가 나올 때까지 대기합니다."),
        "OVERSOLD_BOUNCE_MONITORING": ("👀 과매도(Oversold) 구간입니다. 반등(Bounce) 시그널 발생을 집중 모니터링 중입니다."),
        "OVERSOLD_HOLDING_FOR_REBOUND": ("🧘‍♂️ 과매도 상태이므로 기술적 반등(Rebound) 폭이 클 것으로 기대되어 홀딩합니다."),
        "TRAILING_STOP_TRIGGERED": ("🏆 최고점 대비 2% 하락 발생! 트레일링 스탑을 작동시켜 수익을 굳힙니다."),
        "LET_PROFIT_RUN": ("🏃‍♂️ 아직 상승 추세가 꺾이지 않았습니다. 수익을 끝까지 끌고 가기 위해 매도하지 않습니다."),
        "OPPORTUNITY_SWAP": ("🔄 기회비용 극대화! 부진한 종목을 매도하고 훨씬 더 강력한 상승 모델로 강제 스위칭합니다.")
    }

    msg_parts = []
    for part in code.split('|'):
        part = part.strip()
        msg_parts.append(f"<li>{mapping.get(part, part)}</li>")

    explanation =f"<ul class='list-disc pl-5 space-y-1 mt-1'>{''.join(msg_parts)}</ul>"

    log_entry['reason_mapped'] = explanation
    return log_entry



def load_microgpt_data():
    """Loads the latest microgpt trace from data/microgpt/trace.json."""
    if MICROGPT_DATA_FILE.exists():
        try:
            with open(MICROGPT_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Error loading microgpt data: {e}")
    return None


def build_trade_page(output_dir, context):
    """Builds the dedicated trading status page."""

    # Process logs to map reasons
    if context.get('trade') and 'recent_trades' in context['trade']:
        # Create a copy/map to avoid modifying original if needed, but here modifying in place is fine or map
        # map_reason_code modifies dict in place and returns it
        context['trade']['recent_trades'] = [
            map_reason_code(log_item) for log_item in context['trade']['recent_trades']
        ]

    # Group trades by ticker
    grouped_trades = {}
    if context.get('trade') and 'recent_trades' in context['trade']:
        for log_entry in context['trade']['recent_trades']:
            ticker = log_entry.get('ticker', 'Unknown')
            if ticker not in grouped_trades:
                grouped_trades[ticker] = []
            grouped_trades[ticker].append(log_entry)

    context['grouped_trades'] = grouped_trades

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template('trade.html')
    output = template.render(context)

    with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(output)
    log.info("[OK] Built crypto_trader/index.html")


def build_microgpt_page(output_dir, context):
    """Builds the microgpt visualization page."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template('microgpt.html')
    output = template.render(context)

    # Output to docs/microgpt/index.html
    microgpt_dir = output_dir / "microgpt"
    microgpt_dir.mkdir(parents=True, exist_ok=True)
    
    with open(microgpt_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(output)
    log.info("[OK] Built microgpt/index.html")


def build(output_dir=None):
    """Main build function."""
    if output_dir is None:
        output_dir = DOCS_DIR
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    news_data = load_latest_news()
    recent_news = load_recent_news_list()  # Fetch sidebar list
    trade_data = load_trade_status()
    microgpt_data = load_microgpt_data()

    context = {
        'news': news_data,
        'recent_news': recent_news,  # Pass to template
        'trade': trade_data,
        'microgpt': microgpt_data,
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'summary_html': markdown.markdown(news_data.get('web_report', '')) if news_data else None,
        'coin_names': {
            "KRW-BTC": "비트코인",
            "KRW-ETH": "이더리움",
            "KRW-XRP": "리플",
            "KRW-SOL": "솔라나",
            "KRW-AVAX": "아발란체",
            "KRW-DOGE": "도지코인"
        }
    }

    # 2. Render Dashboard (index.html)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template('dashboard.html')
    output_html = template.render(context)

    with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(output_html)
    log.info(f"[OK] Built index.html at {output_dir}")

    # 3. Render Trade Page
    # Output to docs/crypto_trader/index.html
    if trade_data:
        trade_dir = output_dir / "crypto_trader"
        trade_dir.mkdir(parents=True, exist_ok=True)
        build_trade_page(trade_dir, context)

    # 4. Built MicroGPT Page - Always build as it is client-side now
    build_microgpt_page(output_dir, context)

    # 5. Copy Static Files
    if STATIC_DIR.exists():
        static_dst = output_dir / 'static'
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(STATIC_DIR, static_dst)
        log.info(f"[OK] Static files copied to {static_dst}")
