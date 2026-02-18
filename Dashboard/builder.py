import os
import json
import glob
import shutil
import sys
from datetime import datetime
import markdown
from jinja2 import Environment, FileSystemLoader

# Set encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

def load_latest_news():
    """Loads the most recent news JSON from data/news/ subdirectories."""
    # Summariser saves to: Dashboard/data/news/[morning|evening]/YYYY-MM-DD.json
    # We search recursively: Dashboard/data/news/**/*.json
    news_dir = os.path.join(DATA_DIR, 'news')
    news_files = glob.glob(os.path.join(news_dir, '**', '*.json'), recursive=True)
    
    if not news_files:
        return None
    
    all_news = []
    for f_path in news_files:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure it has a date
                if 'created_at' in data:
                    all_news.append(data)
        except:
            continue
            
    if not all_news:
        return None
        
    # Sort by created_at descending
    all_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return all_news[0]

def load_trade_status():
    """Loads the latest trade status from Auto trader/data/status.json."""
    status_path = os.path.join(PROJECT_ROOT, 'Auto trader', 'data', 'status.json')
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading trade status: {e}")
    return None

def map_reason_code(log):
    """Maps technical reason codes to user-friendly Korean explanations."""
    # Try to get code from 'reason_code' first, then fallback to 'reason'
    code = log.get('reason_code', log.get('reason', '')).upper()
    decision = log.get('decision', '').upper()
    confidence = log.get('confidence', 0)
    
    # Custom mapping dictionary with detailed explanations
    mapping = {
        "TREND_ALIGNMENT": "📉 현재 가격이 장기 이동평균선(60일선) 아래에 있어 하락세가 강합니다. 안전을 위해 매수를 보류했습니다.",
        "VOLATILITY_FILTER": "🌪️ 시장의 변동성이 너무 적거나 반대로 너무 극심합니다. 예측이 어려워 진입하지 않았습니다.",
        "LOW_CONFIDENCE": f"🤔 AI의 분석 결과, 상승 확신도가 기준치(0.65)보다 낮은 {confidence:.2f}입니다. 더 확실한 기회를 기다립니다.",
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
    
    # Logic to handle combined codes (e.g. "LOW_CONFIDENCE | STRUCTURE_UNCLEAR")
    msg_parts = []
    for part in code.split('|'):
        part = part.strip()
        msg_parts.append(f"<li>{mapping.get(part, part)}</li>")
        
    explanation =f"<ul class='list-disc pl-5 space-y-1 mt-1'>{''.join(msg_parts)}</ul>"
    
    # Add mapped explanation to log
    log['reason_mapped'] = explanation
    return log

def build_trade_page(output_dir, context):
    """Builds the dedicated trading status page."""
    
    # Process logs to map reasons
    if context.get('trade') and 'recent_trades' in context['trade']:
        context['trade']['recent_trades'] = [map_reason_code(log) for log in context['trade']['recent_trades']]

    # Group trades by ticker
    grouped_trades = {}
    if context.get('trade') and 'recent_trades' in context['trade']:
        for log in context['trade']['recent_trades']:
            ticker = log.get('ticker', 'Unknown')
            if ticker not in grouped_trades:
                grouped_trades[ticker] = []
            grouped_trades[ticker].append(log)
    
    context['grouped_trades'] = grouped_trades

    env = Environment(loader=FileSystemLoader(os.path.join(PROJECT_ROOT, 'Dashboard', 'templates')))
    template = env.get_template('trade.html')
    output = template.render(context)
    
    with open(os.path.join(output_dir, 'trade.html'), 'w', encoding='utf-8') as f:
        f.write(output)
    print("✅ Built trade.html")

def build(output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, 'docs') # Output to docs for GitHub Pages
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load Data
    news_data = load_latest_news()
    trade_data = load_trade_status() # Load trade data
    
    context = {
        'news': news_data,
        'trade': trade_data, # Pass trade data to context
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
    env = Environment(loader=FileSystemLoader(os.path.join(PROJECT_ROOT, 'Dashboard', 'templates')))
    template = env.get_template('dashboard.html')
    output_html = template.render(context)
    
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(output_html)
    print(f"✅ Built index.html at {output_dir}")
    
    # 3. Render Trade Page
    if trade_data:
        build_trade_page(output_dir, context)

    # 4. Copy Static Files
    static_src = os.path.join(BASE_DIR, 'static')
    static_dst = os.path.join(output_dir, 'static')
    if os.path.exists(static_src):
        if os.path.exists(static_dst):
             shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f"✅ Static files copied to {static_dst}")

def load_all_news():
    """Loads all news JSON files from data/news/."""
    news_files = glob.glob(os.path.join(DATA_DIR, 'news', '*.json'))
    news_files.sort(key=os.path.getctime, reverse=True)
    return news_files

if __name__ == "__main__":
    build()
