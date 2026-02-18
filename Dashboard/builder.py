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
        "TREND_ALIGNMENT": "📉 현재 가격이 장기 이동평균선(MA60) 아래에 위치하여 하락 추세로 판단했습니다. 추세가 전환될 때까지 매수를 보류합니다.",
        "VOLATILITY_FILTER": "🌪️ 시장 변동성이 너무 크거나(패닉 셀) 또는 너무 적어(거래량 부족) 진입 위험이 높다고 판단했습니다.",
        "LOW_CONFIDENCE": f"🤔 AI의 상승 확신도가 {confidence:.2f}로 기준치(0.65)보다 낮습니다. 확실한 기회가 올 때까지 기다립니다.",
        "MAX_COINS_REACHED": "🚫 이미 설정된 최대 보유 종목 수(3개)를 채웠습니다. 리스크 관리를 위해 추가 매수를 중단합니다.",
        "ASSET_ALLOCATION": "⚠️ 한 종목에 설정된 최대 투자 비중(10%)을 초과하게 되어 추가 매수를 제한합니다.",
        "CONSECUTIVE_LOSS_PROTECTION": "🛡️ 최근 연속적인 손실이 발생하여, 자본 보호를 위해 일시적으로 매매를 중단하고 관망합니다.",
        "LOSS_CUT": "✂️ 손실폭이 설정된 기준(-3%)을 초과하여, 더 큰 손실을 막기 위해 즉시 손절매를 실행했습니다.",
        "TAKE_PROFIT": "💰 목표 수익률(+5%)에 도달하여 안전하게 수익을 확정(익절매)했습니다.",
        "STRUCTURE_UNCLEAR": "🤷 시장의 방향성이 뚜렷하지 않아(횡보장 등) 예측이 어렵습니다. 관망하는 것이 유리합니다.",
        "API_ERROR": "⚠️ 일시적인 시스템/네트워크 오류로 인해 안전을 위해 거래를 보류했습니다."
    }
    
    # Default fallback
    explanation = mapping.get(code, log.get('reason', ''))
    
    # Add mapped explanation to log
    log['reason_mapped'] = explanation
    return log

def build_trade_page(output_dir, context):
    """Builds the dedicated trading status page."""
    
    # Process logs to map reasons
    if context.get('trade') and 'recent_trades' in context['trade']:
        context['trade']['recent_trades'] = [map_reason_code(log) for log in context['trade']['recent_trades']]

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
