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
TRADE_DATA_FILE = DATA_DIR / "trade" / "status.json"


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
        "TREND_ALIGNMENT": ("📉 현재 가격이 장기 이동평균선(60일선) 아래에 있어 하락세가 강합니다. "
                            "안전을 위해 매수를 보류했습니다."),
        "VOLATILITY_FILTER": ("🌪️ 시장의 변동성이 너무 적거나 반대로 너무 극심합니다. "
                              "예측이 어려워 진입하지 않았습니다."),
        "LOW_CONFIDENCE": (f"🤔 AI의 분석 결과, 상승 확신도가 기준치(0.65)보다 낮은 {confidence:.2f}입니다. "
                           "더 확실한 기회를 기다립니다." if confidence < 0.65 else
                           f"🤔 상승 확신도는 {confidence:.2f}이나, 다른 위험 요인으로 인해 관망합니다."),
        "MAX_COINS_REACHED": ("🚫 이미 최대 보유 종목 수(3개)를 채웠습니다. "
                              "새로운 종목을 매수하려면 기존 종목이 매도되어야 합니다."),
        "ASSET_ALLOCATION": ("⚠️ 한 종목에 담을 수 있는 최대 비중(30%)을 초과하게 됩니다. "
                             "리스크 관리를 위해 추가 매수를 제한합니다."),
        "CONSECUTIVE_LOSS_PROTECTION": ("🛡️ 최근 연속으로 손실이 발생하여 '쿨다운' 중입니다. "
                                        "잠시 머리를 식히며 시장을 관망합니다."),
        "LOSS_CUT": ("✂️ 아쉽지만 손절매 라인(-3%)을 건드렸습니다. "
                     "더 큰 손실을 막기 위해 원칙대로 매도하여 자본을 지킵니다."),
        "TAKE_PROFIT": ("💰 목표 수익률(+5%)에 도달했습니다! "
                        "욕심부리지 않고 수익을 확정 지어 주머니에 넣습니다."),
        "STRUCTURE_UNCLEAR": ("🤷 차트의 흐름이 위인지 아래인지 명확하지 않습니다. "
                              "방향이 결정될 때까지 지켜보는 게 좋겠습니다."),
        "API_ERROR": ("⚠️ 일시적인 시스템/통신 오류가 발생했습니다. "
                      "안전을 위해 이번 턴은 건너뜁니다."),
        "CAPITAL_PRESERVATION": ("💰 지금은 돈을 버는 것보다 지키는 것이 더 중요한 시기입니다. "
                                 "무리하지 않고 현금을 보유합니다."),
        "UNCLEAR_TREND": ("❓ 상승장인지 하락장인지 뚜렷하지 않습니다. "
                          "애매할 땐 쉬어가는 것이 상책입니다."),
        "LOW_CONFIDENCE_AND_UNCLEAR_TREND": ("🤔 확신도 부족하고 추세도 애매합니다. "
                                             "이럴 때 매수하면 물리기 쉽습니다."),
        "BEARISH_MOMENTUM_INDICATORS": ("📉 보조지표(MACD, RSI)가 하락을 가리키고 있습니다. "
                                        "매수하기엔 힘이 빠져 보입니다."),
        "PRICE_BELOW_MAS": ("📉 가격이 주요 이동평균선 아래로 처져 있습니다. "
                            "상승 추세로 돌아설 때까지 기다립니다."),
        "RSI_OVERSOLD_BB_LOWER_BOUNCE": ("📉 RSI가 과매도 구간(30 이하)이고, "
                                         "볼린저 밴드 하단을 찍고 반등하려는 신호가 포착되었습니다. "
                                         "기술적 반등을 노리고 진입합니다."),
        "OVERSOLD_BOUNCE_SETUP": ("📉 과매도 구간(Oversold)에서 반등할 수 있는 패턴"
                                  "(W자형, 꼬리 달린 캔들 등)이 확인되었습니다. "
                                  "저점 매수 기회로 판단했습니다."),
        "RISK_MANAGEMENT": ("🛡️ 리스크 관리 차원입니다. 시장의 불확실성이 커지거나, "
                            "급격한 변동이 예상되어 선제적으로 현금을 확보합니다.")
    }

    msg_parts = []
    for part in code.split('|'):
        part = part.strip()
        msg_parts.append(f"<li>{mapping.get(part, part)}</li>")

    explanation =f"<ul class='list-disc pl-5 space-y-1 mt-1'>{''.join(msg_parts)}</ul>"

    log_entry['reason_mapped'] = explanation
    return log_entry


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

    with open(output_dir / 'trade.html', 'w', encoding='utf-8') as f:
        f.write(output)
    log.info("[OK] Built trade.html")


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

    context = {
        'news': news_data,
        'recent_news': recent_news,  # Pass to template
        'trade': trade_data,
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
    if trade_data:
        build_trade_page(output_dir, context)

    # 4. Copy Static Files
    if STATIC_DIR.exists():
        static_dst = output_dir / 'static'
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(STATIC_DIR, static_dst)
        log.info(f"[OK] Static files copied to {static_dst}")
